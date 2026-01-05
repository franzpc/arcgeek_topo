"""
Algoritmo para extraer puntos ordenados de polígonos
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
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsFields,
    QgsField,
    QgsWkbTypes,
    QgsProcessingParameterPoint,
    QgsCoordinateTransform,
    QgsProject
)
import math


class PolygonToPointsAlgorithm(QgsProcessingAlgorithm):
    """
    Extrae puntos ordenados de los vértices de polígonos
    con numeración bidireccional (horario y antihorario).
    """
    
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'
    POLYGON_ID_FIELD = 'POLYGON_ID_FIELD'
    START_POINT = 'START_POINT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Capa de polígonos de entrada'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterField(
                self.POLYGON_ID_FIELD,
                self.tr('Campo ID del polígono'),
                parentLayerParameterName=self.INPUT,
                type=QgsProcessingParameterField.Any
            )
        )
        
        self.addParameter(
            QgsProcessingParameterPoint(
                self.START_POINT,
                self.tr('Coordenada de inicio (opcional)'),
                optional=True
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Puntos de salida')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        polygon_id_field = self.parameterAsString(parameters, self.POLYGON_ID_FIELD, context)
        
        # Obtener el punto de inicio y su CRS
        start_point_geom = self.parameterAsPoint(parameters, self.START_POINT, context)
        start_point_crs = self.parameterAsPointCrs(parameters, self.START_POINT, context)
        
        # Crear el punto de inicio transformado al CRS de la capa
        start_point = None
        if start_point_geom and not start_point_geom.isEmpty():
            # Verificar validez del CRS antes de transformar
            if start_point_crs.isValid() and start_point_crs != source.sourceCrs():
                try:
                    transform = QgsCoordinateTransform(start_point_crs, source.sourceCrs(), QgsProject.instance())
                    transformed_point = transform.transform(start_point_geom)
                    start_point = QgsPointXY(transformed_point.x(), transformed_point.y())
                except Exception as e:
                    feedback.reportError(f"Error transformando coordenada de inicio: {e}")
                    # Fallback
                    start_point = QgsPointXY(start_point_geom.x(), start_point_geom.y())
            else:
                start_point = QgsPointXY(start_point_geom.x(), start_point_geom.y())
            
            if start_point:
                feedback.pushInfo(f'Punto de inicio (CRS capa): {start_point.x()}, {start_point.y()}')

        # Campos de salida
        fields = QgsFields()
        fields.append(QgsField('Punto_ID_H', QVariant.Int))   # Point_ID_CW
        fields.append(QgsField('Punto_ID_AH', QVariant.Int))  # Point_ID_CCW
        fields.append(QgsField('Poligono_ID', QVariant.String))
        fields.append(QgsField('X', QVariant.Double))
        fields.append(QgsField('Y', QVariant.Double))

        (sink, dest_id) = self.parameterAsSink(
            parameters, 
            self.OUTPUT, 
            context,
            fields, 
            QgsWkbTypes.Point, 
            source.sourceCrs()
        )

        if sink is None:
            return {}

        total = 100.0 / source.featureCount() if source.featureCount() else 0
        features = source.getFeatures()

        for current, feature in enumerate(features):
            if feedback.isCanceled():
                break

            try:
                polygon_id = feature[polygon_id_field]
            except KeyError:
                polygon_id = str(feature.id()) # Fallback si falla el campo

            polygon_geom = feature.geometry()

            if polygon_geom.isMultipart():
                polygons = polygon_geom.asMultiPolygon()
            else:
                polygons = [polygon_geom.asPolygon()]

            for polygon in polygons:
                exterior_ring = polygon[0]
                
                if len(exterior_ring) > 0 and exterior_ring[0] == exterior_ring[-1]:
                    exterior_ring = exterior_ring[:-1]
                
                if start_point is not None:
                    # Lógica exacta del script para encontrar inicio
                    min_distance = float('inf')
                    start_index = 0
                    
                    for i, pt in enumerate(exterior_ring):
                        dx = pt.x() - start_point.x()
                        dy = pt.y() - start_point.y()
                        distance = math.sqrt(dx * dx + dy * dy)
                        if distance < min_distance:
                            min_distance = distance
                            start_index = i
                    
                    feedback.pushInfo(f'Polígono {polygon_id}: Iniciando desde vértice {start_index} a distancia {min_distance:.2f}')
                else:
                    # Lógica por defecto: punto más al norte (Max Y)
                    if not exterior_ring: continue
                    max_y = max(pt.y() for pt in exterior_ring)
                    start_index = next(i for i, pt in enumerate(exterior_ring) if pt.y() == max_y)
                
                num_points = len(exterior_ring)
                unique_points = set()
                point_counter = 0

                for i in range(num_points):
                    index = (start_index + i) % num_points
                    point = exterior_ring[index]
                    
                    point_tuple = (point.x(), point.y())
                    if point_tuple in unique_points:
                        continue
                    unique_points.add(point_tuple)
                    
                    point_counter += 1
                    
                    f = QgsFeature()
                    f.setGeometry(QgsGeometry.fromPointXY(point))
                    
                    # Corrección: El vértice 1 es siempre el 1 en ambos sentidos
                    ccw_id = 1 if point_counter == 1 else (num_points - point_counter + 2)

                    f.setAttributes([
                        point_counter,  # Punto_ID_H (CW)
                        ccw_id,         # Punto_ID_AH (CCW)
                        str(polygon_id),
                        round(point.x(), 3),
                        round(point.y(), 3)
                    ])
                    sink.addFeature(f, QgsFeatureSink.FastInsert)

            feedback.setProgress(int(current * total))

        return {self.OUTPUT: dest_id}

    def name(self):
        return 'polygon_to_ordered_points'

    def displayName(self):
        return self.tr('Extraer Puntos Ordenados de Polígonos')

    def group(self):
        return self.tr('Levantamientos Topográficos')

    def groupId(self):
        return 'topography'

    def shortHelpString(self):
        return self.tr("""
        <h3>Extraer Puntos Ordenados de Polígonos</h3>
        
        <p>Extrae los vértices de polígonos como puntos ordenados con numeración bidireccional.</p>
        
        <h4>Parámetros:</h4>
        <ul>
        <li><b>Capa de polígonos:</b> Capa vectorial con los polígonos a procesar.</li>
        <li><b>Campo ID:</b> Campo que identifica cada polígono.</li>
        <li><b>Coordenada de inicio:</b> (Opcional) Clic en el mapa para seleccionar. 
        El vértice más cercano será el punto de inicio. Si no se especifica, usa el punto más al norte.</li>
        </ul>
        
        <h4>Salida:</h4>
        <ul>
        <li><b>Punto_ID_H:</b> Numeración en sentido horario (CW)</li>
        <li><b>Punto_ID_AH:</b> Numeración en sentido antihorario (CCW)</li>
        <li><b>Poligono_ID:</b> ID del polígono origen</li>
        <li><b>X, Y:</b> Coordenadas del punto</li>
        </ul>
        """)

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return PolygonToPointsAlgorithm()
