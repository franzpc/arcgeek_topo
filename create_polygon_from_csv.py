"""
Algoritmo para crear Polígono y Puntos desde CSV/Tabla
Compatible con Qt5/Qt6 y QGIS 3.x/4.x
"""
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (
    QgsProcessing,
    QgsFeatureSink,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterField,
    QgsProcessingParameterCrs,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsFields,
    QgsField,
    QgsWkbTypes
)

class CreatePolygonFromTableAlgorithm(QgsProcessingAlgorithm):
    """
    Crea un polígono y sus vértices a partir de una tabla de coordenadas secuenciales.
    """
    
    INPUT = 'INPUT'
    X_FIELD = 'X_FIELD'
    Y_FIELD = 'Y_FIELD'
    CRS = 'CRS'
    OUTPUT_POLYGON = 'OUTPUT_POLYGON'
    OUTPUT_POINTS = 'OUTPUT_POINTS'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Tabla de Coordenadas (CSV/Excel/Capa)'),
                [QgsProcessing.TypeVector]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterField(
                self.X_FIELD,
                self.tr('Campo X (Este)'),
                parentLayerParameterName=self.INPUT,
                type=QgsProcessingParameterField.Any
            )
        )
        
        self.addParameter(
            QgsProcessingParameterField(
                self.Y_FIELD,
                self.tr('Campo Y (Norte)'),
                parentLayerParameterName=self.INPUT,
                type=QgsProcessingParameterField.Any
            )
        )
        
        self.addParameter(
            QgsProcessingParameterCrs(
                self.CRS,
                self.tr('Sistema de Referencia de Coordenadas (CRS)'),
                defaultValue='EPSG:32717'
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_POLYGON,
                self.tr('Capa de Polígono'),
                type=QgsProcessing.TypeVectorPolygon
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_POINTS,
                self.tr('Capa de Vértices'),
                type=QgsProcessing.TypeVectorPoint
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        x_field = self.parameterAsString(parameters, self.X_FIELD, context)
        y_field = self.parameterAsString(parameters, self.Y_FIELD, context)
        crs = self.parameterAsCrs(parameters, self.CRS, context)
        
        # DEFINIR CAMPOS DE SALIDA (POINTS)
        fields_points = QgsFields()
        fields_points.append(QgsField('id', QVariant.Int))
        fields_points.append(QgsField('x', QVariant.Double))
        fields_points.append(QgsField('y', QVariant.Double))
        
        # DEFINIR CAMPOS DE SALIDA (POLYGON)
        fields_poly = QgsFields()
        fields_poly.append(QgsField('id', QVariant.Int))
        fields_poly.append(QgsField('num_vertices', QVariant.Int))
        
        # CREAR SINKS
        (sink_poly, dest_id_poly) = self.parameterAsSink(
            parameters, self.OUTPUT_POLYGON, context,
            fields_poly, QgsWkbTypes.Polygon, crs
        )
        
        (sink_pts, dest_id_pts) = self.parameterAsSink(
            parameters, self.OUTPUT_POINTS, context,
            fields_points, QgsWkbTypes.Point, crs
        )
        
        if sink_poly is None or sink_pts is None:
            return {}

        features = source.getFeatures()
        points = []
        
        # Recorrer features para extraer puntos
        feedback.pushInfo("Leyendo coordenadas...")
        
        count = 0
        total = source.featureCount() if source.featureCount() > 0 else 100
        
        for i, feature in enumerate(features):
            if feedback.isCanceled():
                break
                
            try:
                # Intentar obtener como número, si falla es None
                val_x = feature[x_field]
                val_y = feature[y_field]
                
                # Manejo de valores string que puedan venir del CSV
                if isinstance(val_x, str): val_x = float(val_x.replace(',', '.'))
                if isinstance(val_y, str): val_y = float(val_y.replace(',', '.'))
                
                x = float(val_x)
                y = float(val_y)
                
                pt = QgsPointXY(x, y)
                points.append(pt)
                
                # Crear Feature de Punto
                f_pt = QgsFeature()
                f_pt.setGeometry(QgsGeometry.fromPointXY(pt))
                f_pt.setAttributes([i + 1, x, y])
                sink_pts.addFeature(f_pt, QgsFeatureSink.FastInsert)
                
                count += 1
            except (ValueError, TypeError):
                feedback.reportError(f"Fila {i+1}: Valor inválido en coordenadas (se omite).")
                continue
                
            feedback.setProgress(int(i / total * 50))

        if len(points) < 3:
            feedback.reportError("Se requieren al menos 3 puntos válidos para crear un polígono.")
            return {}
            
        # Crear Polígono
        feedback.pushInfo(f"Creando polígono con {len(points)} vértices...")
        
        # Cerrar el polígono si es necesario
        poly_points = points[:]
        if poly_points[0] != poly_points[-1]:
            poly_points.append(poly_points[0])
            
        f_poly = QgsFeature()
        f_poly.setGeometry(QgsGeometry.fromPolygonXY([poly_points]))
        f_poly.setAttributes([1, count])
        sink_poly.addFeature(f_poly, QgsFeatureSink.FastInsert)
        
        feedback.setProgress(100)
        
        return {
            self.OUTPUT_POLYGON: dest_id_poly,
            self.OUTPUT_POINTS: dest_id_pts
        }

    def name(self):
        return 'create_polygon_from_table'

    def displayName(self):
        return self.tr('Crear Polígono y Puntos desde Tabla')

    def group(self):
        return self.tr('Levantamientos Topográficos')

    def groupId(self):
        return 'topography'

    def shortHelpString(self):
        return self.tr("""
        <h3>Crear Polígono y Puntos desde Tabla</h3>
        
        <p>Esta herramienta toma una tabla (CSV, Excel o capa sin geometría) con coordenadas X, Y 
        y genera dos capas vectoriales:</p>
        
        <ul>
            <li><b>Polígono:</b> Un polígono cerrado uniendo los puntos en orden secuencial.</li>
            <li><b>Vértices:</b> Una capa de puntos con la geometría de cada vértice.</li>
        </ul>
        
        <p><b>Nota:</b> El orden de los puntos en la tabla determina la forma del polígono. 
        Asegúrese de que estén ordenados (horario o antihorario) para evitar geometrías cruzadas.</p>
        """)

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return CreatePolygonFromTableAlgorithm()
