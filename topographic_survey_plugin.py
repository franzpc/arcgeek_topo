"""
Plugin de QGIS: Levantamientos Topográficos
Versión 1.0.0 - Compatible con Qt5/Qt6 y QGIS 3.x/4.x
"""
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon, QColor, QFont
from qgis.PyQt.QtWidgets import (
    QAction, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QFileDialog, QMessageBox, QProgressBar,
    QGroupBox, QFormLayout, QTabWidget, QWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QSpinBox,
    QCheckBox
)
from qgis.PyQt.QtXml import QDomDocument
from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY,
    QgsField, QgsCoordinateReferenceSystem, QgsPrintLayout,
    QgsLayoutItemMap, QgsLayoutItemLabel, QgsLayoutItemScaleBar,
    QgsFillSymbol, QgsMarkerSymbol, QgsLineSymbol, QgsTextFormat,
    QgsVectorLayerSimpleLabeling, QgsPalLayerSettings, QgsReadWriteContext,
    Qgis, QgsApplication, QgsLayoutItemAttributeTable, QgsRectangle,
    QgsVectorFileWriter
)
from qgis.gui import QgsProjectionSelectionWidget
import os
import sys
import csv
import math
from datetime import date

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

plugin_dir = os.path.dirname(__file__)
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)

from .topographic_calculator import TopographicCalculator



class TopographicSurveyDialog(QDialog):
    """Diálogo principal para generar levantamientos topográficos"""
    
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.setWindowTitle("ArcGeek Topo - Asistente")
        self.setMinimumWidth(700)
        self.setMinimumHeight(550)
        self.csv_path = ""
        self.csv_columns = []
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # WIDGET DE PESTAÑAS (Estilo Asistente)
        self.tabs = QTabWidget()
        try:
            self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        except AttributeError:
            self.tabs.setTabPosition(QTabWidget.North)
        # Deshabilitar clic en pestañas para forzar flujo secuencial (opcional, pero da más sensación de asistente)
        # self.tabs.tabBar().setEnabled(False) 
        
        # --- TAB 1: DATOS ---
        self.tab_data = QWidget()
        self.init_tab_data()
        self.tabs.addTab(self.tab_data, "1. Datos")
        
        # --- TAB 2: INFORMACIÓN ---
        self.tab_info = QWidget()
        self.init_tab_info()
        self.tabs.addTab(self.tab_info, "2. Información")
        
        # --- TAB 3: CONFIGURACIÓN IMPRESIÓN ---
        self.tab_config = QWidget()
        self.init_tab_config()
        self.tabs.addTab(self.tab_config, "3. Impresión")
        
        # --- TAB 4: GENERAR ---
        self.tab_run = QWidget()
        self.init_tab_run()
        self.tabs.addTab(self.tab_run, "4. Generar")
        
        main_layout.addWidget(self.tabs)
        
        # --- BARRA DE NAVEGACIÓN ---
        nav_layout = QHBoxLayout()
        
        self.btn_back = QPushButton("< Anterior")
        self.btn_back.clicked.connect(self.go_back)
        self.btn_back.setEnabled(False)
        
        self.btn_next = QPushButton("Siguiente >")
        self.btn_next.clicked.connect(self.go_next)
        
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self.close)
        
        nav_layout.addWidget(self.btn_cancel)
        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_back)
        nav_layout.addWidget(self.btn_next)
        
        main_layout.addLayout(nav_layout)
        self.setLayout(main_layout)
        
        # Conectar cambio de pestañas para actualizar estado de botones
        self.tabs.currentChanged.connect(self.update_nav_buttons)

    def init_tab_data(self):
        layout = QVBoxLayout()
        
        # Grupo Archivo
        file_group = QGroupBox("Origen de Datos")
        file_layout = QFormLayout()
        
        csv_layout = QHBoxLayout()
        self.csv_edit = QLineEdit()
        self.csv_edit.setPlaceholderText("Seleccione archivo CSV, TXT o Excel...")
        self.csv_edit.setReadOnly(True)
        csv_button = QPushButton("Examinar...")
        csv_button.clicked.connect(self.select_csv)
        csv_layout.addWidget(self.csv_edit)
        csv_layout.addWidget(csv_button)
        file_layout.addRow("Archivo:", csv_layout)
        
        self.x_combo = QComboBox()
        self.x_combo.setEnabled(False)
        file_layout.addRow("Columna X (Este):", self.x_combo)
        
        self.y_combo = QComboBox()
        self.y_combo.setEnabled(False)
        file_layout.addRow("Columna Y (Norte):", self.y_combo)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Grupo CRS
        crs_group = QGroupBox("Sistema de Referencia")
        crs_layout = QVBoxLayout()
        self.crs_selector = QgsProjectionSelectionWidget()
        self.crs_selector.setCrs(QgsCoordinateReferenceSystem("EPSG:32717"))
        self._setup_crs_options()
        crs_layout.addWidget(self.crs_selector)
        crs_group.setLayout(crs_layout)
        layout.addWidget(crs_group)
        
        layout.addStretch()
        self.tab_data.setLayout(layout)

    def init_tab_info(self):
        layout = QVBoxLayout()
        info_group = QGroupBox("Datos del Proyecto (Dinámico)")
        info_layout = QVBoxLayout()
        
        # Tabla de campos
        self.info_table = QTableWidget(0, 2)
        self.info_table.setHorizontalHeaderLabels(["ID en Plantilla", "Valor"])
        try:
            self.info_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        except AttributeError:
            self.info_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            
        try:
            self.info_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        except AttributeError:
            self.info_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        # Info
        help_lbl = QLabel("Agregue campos. El 'ID en Plantilla' debe coincidir con el 'ID del Elemento' en el diseño de impresión.")
        help_lbl.setStyleSheet("color: #555; font-size: 10px; font-style: italic;")
        info_layout.addWidget(help_lbl)
        
        info_layout.addWidget(self.info_table)
        
        # Botones de tabla
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("Agregar Campo")
        add_btn.setIcon(QIcon(QgsApplication.iconPath("mActionAdd.svg")))
        add_btn.clicked.connect(lambda: self._add_info_row("NUEVO_ITEM", ""))
        
        del_btn = QPushButton("Eliminar Campo")
        del_btn.setIcon(QIcon(QgsApplication.iconPath("mActionRemove.svg")))
        del_btn.clicked.connect(self._del_info_row)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        info_layout.addLayout(btn_layout)
        
        # Cargar valores por defecto
        defaults = [
            ("TITULO", "LEVANTAMIENTO PLANIMÉTRICO"),
            ("PROPIETARIO", ""),
            ("UBICACION", "Loja, Ecuador"),
            ("FECHA", date.today().strftime('%Y-%m-%d'))
        ]
        for k, v in defaults:
            self._add_info_row(k, v)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        self.tab_info.setLayout(layout)

    def _add_info_row(self, key, val):
        r = self.info_table.rowCount()
        self.info_table.insertRow(r)
        self.info_table.setItem(r, 0, QTableWidgetItem(key))
        self.info_table.setItem(r, 1, QTableWidgetItem(val))

    def _del_info_row(self):
        r = self.info_table.currentRow()
        if r >= 0:
            self.info_table.removeRow(r)
        else:
            # Si no hay selección, eliminar el último
            rc = self.info_table.rowCount()
            if rc > 0:
                self.info_table.removeRow(rc - 1)

    def init_tab_config(self):
        layout = QVBoxLayout()
        
        # --- OPCIÓN PLANTILLA PERSONALIZADA ---
        custom_group = QGroupBox("Plantilla Personalizada")
        custom_layout = QVBoxLayout()
        
        self.chk_custom_template = QCheckBox("Usar plantilla externa (.qpt)")
        self.chk_custom_template.toggled.connect(self._toggle_custom_template)
        custom_layout.addWidget(self.chk_custom_template)
        
        file_layout = QHBoxLayout()
        self.edit_custom_template = QLineEdit()
        self.edit_custom_template.setPlaceholderText("Seleccione un archivo .qpt...")
        self.edit_custom_template.setReadOnly(True)
        self.edit_custom_template.setEnabled(False)
        
        self.btn_custom_template = QPushButton("Examinar...")
        self.btn_custom_template.setEnabled(False)
        self.btn_custom_template.clicked.connect(self.select_custom_template)
        
        file_layout.addWidget(self.edit_custom_template)
        file_layout.addWidget(self.btn_custom_template)
        custom_layout.addLayout(file_layout)
        
        custom_group.setLayout(custom_layout)
        layout.addWidget(custom_group)
        
        # --- CONFIGURACIÓN ESTÁNDAR ---
        self.page_group = QGroupBox("Configuración de Página (Sistema)")
        page_layout = QFormLayout()
        
        self.combo_size = QComboBox()
        self.combo_size.addItems(["A4", "A3", "A2", "A1", "CARTA", "OFICIO"])
        page_layout.addRow("Tamaño de Papel:", self.combo_size)
        
        self.combo_orientation = QComboBox()
        self.combo_orientation.addItems(["Horizontal", "Vertical"])
        page_layout.addRow("Orientación:", self.combo_orientation)
        
        self.page_group.setLayout(page_layout)
        layout.addWidget(self.page_group)
        
        # Grupo Configuración de Datos
        data_config_group = QGroupBox("Formato de Datos")
        data_config_layout = QFormLayout()
        
        self.decimals_spin = QSpinBox()
        self.decimals_spin.setRange(0, 4)
        self.decimals_spin.setValue(2)
        data_config_layout.addRow("Decimales en Coordenadas:", self.decimals_spin)
        
        data_config_group.setLayout(data_config_layout)
        layout.addWidget(data_config_group)
        
        # Info label
        self.template_info_label = QLabel("Nota: Asegúrese de tener creada la plantilla correspondiente en la carpeta del plugin.\nEj: plantilla_A4_Horizontal.qpt")
        self.template_info_label.setStyleSheet("color: #666; font-style: italic; margin-top: 10px;")
        layout.addWidget(self.template_info_label)
        
        layout.addStretch()
        self.tab_config.setLayout(layout)

    def init_tab_run(self):
        layout = QVBoxLayout()
        
        self.summary_label = QLabel("Listo para generar el levantamiento.\n\nRevise los datos en las pestañas anteriores si es necesario.")
        try:
            self.summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        except AttributeError:
             self.summary_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.summary_label)

        # Opciones de Salida
        out_group = QGroupBox("Opciones de Salida")
        out_layout = QVBoxLayout()
        
        self.chk_save_files = QCheckBox("Guardar capas en carpeta (GeoPackage)")
        self.chk_save_files.stateChanged.connect(lambda: self.out_dir_widget.setEnabled(self.chk_save_files.isChecked()))
        out_layout.addWidget(self.chk_save_files)
        
        file_layout = QHBoxLayout()
        self.out_dir_edit = QLineEdit()
        self.out_dir_edit.setPlaceholderText("Seleccione carpeta de destino...")
        self.out_dir_edit.setReadOnly(True)
        
        self.btn_out_dir = QPushButton("...")
        self.btn_out_dir.clicked.connect(self.select_output_dir)
        
        file_layout.addWidget(self.out_dir_edit)
        file_layout.addWidget(self.btn_out_dir)
        
        self.out_dir_widget = QWidget()
        self.out_dir_widget.setLayout(file_layout)
        self.out_dir_widget.setEnabled(False)
        out_layout.addWidget(self.out_dir_widget)
        
        out_group.setLayout(out_layout)
        layout.addWidget(out_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        try:
            self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        except AttributeError:
            self.status_label.setAlignment(Qt.AlignCenter)

        self.status_label.setStyleSheet("color: #1976D2; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        self.generate_button = QPushButton("GENERAR PLANO")
        self.generate_button.setMinimumHeight(50)
        self.generate_button.setStyleSheet("""
            QPushButton { background-color: #2196F3; color: white; font-size: 14px; font-weight: bold; border-radius: 5px; }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:disabled { background-color: #BDBDBD; }
        """)
        self.generate_button.clicked.connect(self.generate_survey)
        self.generate_button.setEnabled(False) # Se activa al validar
        layout.addWidget(self.generate_button)
        
        layout.addStretch()
        self.tab_run.setLayout(layout)

    def go_next(self):
        curr = self.tabs.currentIndex()
        if curr < self.tabs.count() - 1:
            self.tabs.setCurrentIndex(curr + 1)

    def go_back(self):
        curr = self.tabs.currentIndex()
        if curr > 0:
            self.tabs.setCurrentIndex(curr - 1)

    def update_nav_buttons(self):
        curr = self.tabs.currentIndex()
        max_idx = self.tabs.count() - 1
        
        self.btn_back.setEnabled(curr > 0)
        
        if curr == max_idx:
            self.btn_next.setVisible(False)
            # Validar si se puede generar
            if self.x_combo.isEnabled():
                self.generate_button.setEnabled(True)
                self.summary_label.setText(f"Configuración:\nPapel: {self.combo_size.currentText()} - {self.combo_orientation.currentText()}\nCRS: {self.crs_selector.crs().authid()}")
            else:
                self.generate_button.setEnabled(False)
                self.summary_label.setText("⚠ Faltan datos. Por favor cargue un archivo CSV en la pestaña 1.")
        else:
            self.btn_next.setVisible(True)
            self.btn_next.setText("Siguiente >")

    def _setup_crs_options(self):
        try:
            self.crs_selector.setOptionVisible(QgsProjectionSelectionWidget.CrsOption.LayerCrs, False)
            self.crs_selector.setOptionVisible(QgsProjectionSelectionWidget.CrsOption.ProjectCrs, True)
            self.crs_selector.setOptionVisible(QgsProjectionSelectionWidget.CrsOption.CurrentCrs, True)
            self.crs_selector.setOptionVisible(QgsProjectionSelectionWidget.CrsOption.DefaultCrs, True)
            self.crs_selector.setOptionVisible(QgsProjectionSelectionWidget.CrsOption.RecentCrs, True)
        except AttributeError:
            self.crs_selector.setOptionVisible(QgsProjectionSelectionWidget.LayerCrs, False)
            self.crs_selector.setOptionVisible(QgsProjectionSelectionWidget.ProjectCrs, True)
            self.crs_selector.setOptionVisible(QgsProjectionSelectionWidget.CurrentCrs, True)
            self.crs_selector.setOptionVisible(QgsProjectionSelectionWidget.DefaultCrs, True)
            self.crs_selector.setOptionVisible(QgsProjectionSelectionWidget.RecentCrs, True)
    
    def detect_delimiter(self, file_path):
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            sample = f.read(2048)
            try:
                return csv.Sniffer().sniff(sample).delimiter
            except:
                for delim in [';', ',', '\t', '|']:
                    if delim in sample:
                        return delim
                return ';'
    
    def select_output_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de salida")
        if folder:
            self.out_dir_edit.setText(folder)

    def _toggle_custom_template(self, checked):
        self.edit_custom_template.setEnabled(checked)
        self.btn_custom_template.setEnabled(checked)
        self.page_group.setEnabled(not checked)

    def select_custom_template(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar plantilla de impresión", "",
            "Archivos QGIS Composer (*.qpt);;Todos los archivos (*)"
        )
        if file_path:
            self.edit_custom_template.setText(file_path)

    def select_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo de coordenadas", "",
            "Archivos de texto (*.csv *.txt);;Archivos Excel (*.xlsx *.xls);;Todos los archivos (*)"
        )
        if file_path:
            self.csv_path = file_path
            self.csv_edit.setText(file_path)
            self.load_csv_columns()
    
    def load_csv_columns(self):
        try:
            if not HAS_PANDAS:
                QMessageBox.critical(self, "Error", "La librería 'pandas' no está instalada.")
                return
            
            if self.csv_path.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(self.csv_path, nrows=0)
            else:
                delimiter = self.detect_delimiter(self.csv_path)
                df = pd.read_csv(self.csv_path, delimiter=delimiter, encoding='utf-8-sig', nrows=0)
            
            self.csv_columns = list(df.columns)
            self.x_combo.clear()
            self.y_combo.clear()
            self.x_combo.addItems(self.csv_columns)
            self.y_combo.addItems(self.csv_columns)
            
            for i, col in enumerate(self.csv_columns):
                col_lower = col.lower()
                if 'x' in col_lower or 'este' in col_lower:
                    self.x_combo.setCurrentIndex(i)
                if 'y' in col_lower or 'norte' in col_lower:
                    self.y_combo.setCurrentIndex(i)
            
            self.x_combo.setEnabled(True)
            self.y_combo.setEnabled(True)
            self.status_label.setText(f"✔ Archivo cargado: {len(self.csv_columns)} columnas")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al leer el archivo:\n{str(e)}")
    
    def generate_survey(self):
        # Validar estado limpio del proyecto (Opcional)
        if QgsProject.instance().mapLayers():
             try:
                 yes_btn = QMessageBox.Yes
                 no_btn = QMessageBox.No
             except AttributeError:
                 yes_btn = QMessageBox.StandardButton.Yes
                 no_btn = QMessageBox.StandardButton.No

             resp = QMessageBox.question(
                 self, 
                 "Proyecto no vacío", 
                 "El proyecto actual ya tiene capas cargadas.\n\nPara evitar conflictos con layouts anteriores, se recomienda usar un proyecto nuevo.\n¿Desea continuar de todos modos (se añadirán nuevas capas)?",
                 yes_btn | no_btn, 
                 no_btn
             )
             if resp == no_btn:
                 return

        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.status_label.setText("Procesando datos...")
            self.generate_button.setEnabled(False)
            self.btn_cancel.setEnabled(False)
            
            x_col = self.x_combo.currentText()
            y_col = self.y_combo.currentText()
            
            if self.csv_path.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(self.csv_path)
            else:
                delimiter = self.detect_delimiter(self.csv_path)
                df = pd.read_csv(self.csv_path, delimiter=delimiter, encoding='utf-8-sig')
            
            self.progress_bar.setValue(20)
            
            coordinates = [(float(row[x_col]), float(row[y_col])) for _, row in df.iterrows()]
            survey_table, area = TopographicCalculator.generate_survey_table(coordinates)
            
            self.progress_bar.setValue(40)
            
            crs = self.crs_selector.crs()
            if not crs.isValid():
                QMessageBox.warning(self, "Advertencia", "Sistema de coordenadas no válido.")
                return

            # Validar si ya existe layout con este nombre
            base_name = os.path.splitext(os.path.basename(self.csv_path))[0]
            layout_name = f"Levantamiento_{base_name}_{self.combo_size.currentText()}"
            if QgsProject.instance().layoutManager().layoutByName(layout_name):
                QMessageBox.warning(self, "Error", f"Ya existe un diseño llamado '{layout_name}'.\nElimínelo o use un archivo con otro nombre.")
                return
            
            self.status_label.setText("Creando capas...")
            decimals = self.decimals_spin.value()
            
            output_folder = None
            if self.chk_save_files.isChecked():
                output_folder = self.out_dir_edit.text()
                if not output_folder or not os.path.isdir(output_folder):
                    QMessageBox.warning(self, "Advertencia", "Carpeta de salida no válida. Se usarán capas temporales.")
                    output_folder = None
            
            layer = self._create_layers(coordinates, crs, area, survey_table, decimals, output_folder)
            
            self.progress_bar.setValue(60)
            
            self.status_label.setText("Generando layout...")
            layout = self._create_layout(layer, survey_table, area, crs)
            
            self.progress_bar.setValue(80)
            
            self.iface.openLayoutDesigner(layout)
            
            self.progress_bar.setValue(100)
            self.status_label.setText("✔ Layout creado exitosamente")
            
            self._show_success_message(area, len(coordinates), crs)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error:\n{str(e)}")
            self.status_label.setText("✗ Error")
            import traceback
            traceback.print_exc()
        finally:
            self.progress_bar.setVisible(False)
            self.generate_button.setEnabled(True)
            self.btn_cancel.setEnabled(True)
    
    def _show_success_message(self, area, n_vertices, crs):
        msg = QMessageBox()
        try:
            msg.setIcon(QMessageBox.Icon.Information)
        except AttributeError:
            msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("¡Levantamiento Generado!")
        msg.setText("El levantamiento topográfico se ha creado correctamente.")
        template_msg = getattr(self, 'last_template_used', 'Desconocida')
        msg.setInformativeText(f"Área: {area:.2f} m²\nVértices: {n_vertices}\nCRS: {crs.authid()}\nPlantilla: {template_msg}")
        try:
            msg.exec()
        except AttributeError:
            msg.exec_()
            


    
    def _create_layers(self, coordinates, crs, area, survey_table, decimals=2, output_folder=None):
        # CAPA POLÍGONO
        layer = QgsVectorLayer(f"Polygon?crs={crs.authid()}", "Lote", "memory")
        prov = layer.dataProvider()
        prov.addAttributes([QgsField("id", QVariant.Int), QgsField("area_m2", QVariant.Double), QgsField("perimetro", QVariant.Double)])
        layer.updateFields()
        
        points = [QgsPointXY(x, y) for x, y in coordinates]
        if points[0] != points[-1]:
            points.append(points[0])
        
        feat = QgsFeature()
        feat.setGeometry(QgsGeometry.fromPolygonXY([points]))
        feat.setAttributes([1, area, TopographicCalculator.calculate_perimeter(survey_table)])
        prov.addFeature(feat)
        layer.updateExtents()
        
        symbol = QgsFillSymbol.createSimple({'color': '255,200,200,100', 'outline_color': 'red', 'outline_width': '0.5'})
        layer.renderer().setSymbol(symbol)
        
        # CAPA VÉRTICES
        v_layer = self._create_vertex_layer(coordinates, crs, decimals)
        
        # CAPA MEDIDAS
        m_layer = self._create_measures_layer(survey_table, crs)
        
        # Si se solicita guardar, convertir memory layer a archivo
        if output_folder:
            base_name = os.path.splitext(os.path.basename(self.csv_path))[0]
            
            # Guardar Lote
            lote_path = os.path.join(output_folder, f"{base_name}_Lote.gpkg")
            layer = self._save_and_load_layer(layer, lote_path)
            
            # Guardar Vértices
            vert_path = os.path.join(output_folder, f"{base_name}_Vertices.gpkg")
            v_layer = self._save_and_load_layer(v_layer, vert_path)
            
            # Guardar Medidas
            med_path = os.path.join(output_folder, f"{base_name}_Medidas.gpkg")
            m_layer = self._save_and_load_layer(m_layer, med_path)

        QgsProject.instance().addMapLayer(layer)
        QgsProject.instance().addMapLayer(v_layer)
        QgsProject.instance().addMapLayer(m_layer)
        
        return layer

    def _save_and_load_layer(self, memory_layer, output_path):
        """Guarda una capa de memoria a disco y la recarga manteniendo estilo."""
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.fileEncoding = "UTF-8"
        
        transform_context = QgsProject.instance().transformContext()
        error = QgsVectorFileWriter.writeAsVectorFormatV3(
            memory_layer,
            output_path,
            transform_context,
            options
        )
        
        if error[0] != QgsVectorFileWriter.NoError:
            self.iface.messageBar().pushMessage("Error al guardar", f"No se pudo guardar {output_path}: {error}", Qgis.Warning)
            return memory_layer # Fallback a memoria
            
        # Cargar capa guardada
        new_layer = QgsVectorLayer(output_path, memory_layer.name(), "ogr")
        if not new_layer.isValid():
            return memory_layer
            
        # Copiar estilo
        # Copiar estilo
        if memory_layer.renderer():
            new_layer.setRenderer(memory_layer.renderer().clone())
            
        if memory_layer.labeling():
            new_layer.setLabeling(memory_layer.labeling().clone())
            
        new_layer.setLabelsEnabled(memory_layer.labelsEnabled())
        
        return new_layer
    
    def _create_vertex_layer(self, coordinates, crs, decimals=2):
        layer = QgsVectorLayer(f"Point?crs={crs.authid()}", "Vértices", "memory")
        prov = layer.dataProvider()
        prov.addAttributes([QgsField("punto", QVariant.Int), QgsField("x", QVariant.String), QgsField("y", QVariant.String)])
        layer.updateFields()
        
        for i, (x, y) in enumerate(coordinates):
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x, y)))
            f.setAttributes([i + 1, f"{x:.{decimals}f}", f"{y:.{decimals}f}"])
            prov.addFeature(f)
        layer.updateExtents()
        
        # Simbología simple (Punto pequeño)
        symbol = QgsMarkerSymbol.createSimple({'name': 'circle', 'color': 'black', 'size': '1.5', 'outline_color': 'black', 'outline_width': '0'})
        layer.renderer().setSymbol(symbol)
        
        # Etiquetado Cartográfico Simple
        settings = QgsPalLayerSettings()
        settings.fieldName = 'punto'
        settings.enabled = True
        
        try:
            settings.placement = QgsPalLayerSettings.Placement.OrderedPositionsAroundPoint
            settings.quadOffset = QgsPalLayerSettings.QuadrantPosition.QuadrantAboveRight
        except AttributeError:
            settings.placement = QgsPalLayerSettings.OrderedPositionsAroundPoint
            settings.quadOffset = QgsPalLayerSettings.QuadrantAboveRight
            
        settings.dist = 2.0 # Separación del punto (mm)
        
        txt_fmt = QgsTextFormat()
        txt_fmt.setSize(9)
        txt_fmt.setColor(QColor('black'))
        font = QFont()
        font.setBold(True)
        txt_fmt.setFont(font)
        settings.setFormat(txt_fmt)
        
        layer.setLabeling(QgsVectorLayerSimpleLabeling(settings))
        layer.setLabelsEnabled(True)
        
        return layer
    
    def _create_measures_layer(self, survey_table, crs):
        layer = QgsVectorLayer(f"LineString?crs={crs.authid()}", "Medidas", "memory")
        prov = layer.dataProvider()
        prov.addAttributes([QgsField("lado", QVariant.String), QgsField("rumbo", QVariant.String), QgsField("distancia", QVariant.Double), QgsField("label", QVariant.String)])
        layer.updateFields()
        
        for row in survey_table:
            next_idx = row['punto'] % len(survey_table)
            next_row = survey_table[next_idx]
            p1, p2 = QgsPointXY(row['x'], row['y']), QgsPointXY(next_row['x'], next_row['y'])
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromPolylineXY([p1, p2]))
            f.setAttributes([row['lado'], row['rumbo'], row['distancia'], f"{row['distancia']:.2f} m\n{row['rumbo']}"])
            prov.addFeature(f)
        layer.updateExtents()
        
        symbol = QgsLineSymbol.createSimple({'color': 'blue', 'width': '0.3', 'style': 'dash'})
        layer.renderer().setSymbol(symbol)
        
        settings = QgsPalLayerSettings()
        settings.fieldName = 'label'
        settings.enabled = True
        try:
            settings.placement = Qgis.LabelPlacement.Line
        except AttributeError:
            try:
                settings.placement = QgsPalLayerSettings.Placement.Line
            except AttributeError:
                settings.placement = QgsPalLayerSettings.Line
        
        txt_fmt = QgsTextFormat()
        txt_fmt.setSize(8)
        txt_fmt.setColor(QColor('blue'))
        settings.setFormat(txt_fmt)
        
        layer.setLabeling(QgsVectorLayerSimpleLabeling(settings))
        layer.setLabelsEnabled(True)
        return layer
    

    def _find_best_template_path(self, target_size, orientation):
        """Busca la plantilla solicitada o la más cercana disponible."""
        
        # Mapa de prioridades de búsqueda (Vecinos más cercanos)
        # Si falta la clave, buscamos solo esa.
        priorities = {
            "A4": ["CARTA", "OFICIO", "A3", "A2", "A1"],
            "A3": ["A4", "A2", "A1", "CARTA"],
            "A2": ["A3", "A1", "A4"],
            "A1": ["A2", "A3", "A4"],
            "CARTA": ["A4", "OFICIO", "A3"],
            "OFICIO": ["A4", "CARTA", "A3"]
        }
        
        search_order = [target_size] + priorities.get(target_size, [])
        
        plugin_dir = os.path.dirname(__file__)
        
        for size in search_order:
            filename = f"plantilla_{size}_{orientation}.qpt"
            path = os.path.join(plugin_dir, filename)
            if os.path.exists(path):
                # Si encontramos una plantilla (sea la solicitada o un fallback)
                return path, filename, size
                
        # Si no se encuentra ninguna
        return None, None, None

    def _create_layout(self, layer, survey_table, area, crs):
        project = QgsProject.instance()
        base_name = os.path.splitext(os.path.basename(self.csv_path))[0]
        
        layout_suffix = ""
        
        if self.chk_custom_template.isChecked():
            # USAR PLANTILLA PERSONALIZADA
            template_path = self.edit_custom_template.text()
            if not template_path or not os.path.exists(template_path):
                raise FileNotFoundError("La ruta de la plantilla personalizada no es válida o el archivo no existe.")
                
            template_name = os.path.basename(template_path)
            layout_suffix = "Personalizado"
            self.last_template_used = f"{template_name} (Usuario)"
            
        else:
            # USAR PLANTILLAS DEL SISTEMA
            target_size = self.combo_size.currentText()
            orientation = self.combo_orientation.currentText()
            
            # Buscar plantilla con lógica de fallback
            template_path, template_name, found_size = self._find_best_template_path(target_size, orientation)
            
            if not template_path:
                 raise FileNotFoundError(f"No se encontró ninguna plantilla compatible para {target_size} - {orientation}.\n"
                                         f"Genere al menos 'plantilla_{target_size}_{orientation}.qpt' o una de tamaño cercano (A4, A3, etc).")
            
            # Advertir si se usó un fallback
            if found_size != target_size:
                self.iface.messageBar().pushMessage("Aviso de Plantilla", f"No se encontró plantilla {target_size}. Usando {found_size} ({template_name}) en su lugar.", Qgis.Warning)
            
            self.last_template_used = template_name
            layout_suffix = found_size
        
        layout = QgsPrintLayout(project)
        with open(template_path, 'r', encoding='utf-8') as f:
             doc = QDomDocument()
             doc.setContent(f.read())
        layout.loadFromTemplate(doc, QgsReadWriteContext())
        layout.setName(f"Levantamiento_{base_name}_{layout_suffix}")
        
        map_item = layout.itemById('Mapa 1')
        if map_item:
            # 1. Establecer extensión inicial para centrar (con margen)
            extent = layer.extent()
            extent.scale(1.1) 
            map_item.setExtent(extent)
            map_item.refresh()
        
        self._update_layout_labels(layout, area, crs)
        self._link_scalebar_to_map(layout, map_item)
        
        # 4. Actualizar tabla de coordenadas
        for item in layout.items():
            if hasattr(item, 'multiFrame'):
                multi_frame = item.multiFrame()
                if isinstance(multi_frame, QgsLayoutItemAttributeTable):
                    # Buscar la capa de vértices por nombre (la acabamos de crear)
                    vertex_layer = None
                    for lyr in QgsProject.instance().mapLayers().values():
                        if lyr.name() == "Vértices" and lyr.providerType() == "memory":
                             vertex_layer = lyr
                             break
                    
                    if vertex_layer:
                        multi_frame.setVectorLayer(vertex_layer)
                        multi_frame.refreshAttributes() # Importante actualizar atributos
                        
                        # Actualizar encabezados
                        columns = multi_frame.columns()
                        for col in columns:
                            if col.attribute() == 'punto':
                                col.setHeading('Punto')
                            elif col.attribute() == 'x':
                                col.setHeading('X (Este)')
                            elif col.attribute() == 'y':
                                col.setHeading('Y (Norte)')
                        
                        multi_frame.setColumns(columns)
                        # Forzar refresco
                        multi_frame.update()

        
        project.layoutManager().addLayout(layout)
        return layout
    
    def _update_layout_labels(self, layout, area, crs):
        # 1. Valores Calculados (Prioridad ID Específico, luego fallback texto)
        # AREA
        item = layout.itemById('AREA')
        if item and isinstance(item, QgsLayoutItemLabel):
            item.setText(f"{area:.2f} m²")
        else:
            # Fallback búsqueda texto
            for item in layout.items():
                if isinstance(item, QgsLayoutItemLabel) and "SUPERFICIE" in item.text():
                     item.setText(f"SUPERFICIE: {area:.2f} m²")
        
        # CRS
        item = layout.itemById('CRS')
        if item and isinstance(item, QgsLayoutItemLabel):
            item.setText(f"{crs.authid()} - {crs.description()}")
        
        # 2. Valores Dinámicos de la Tabla
        rows = self.info_table.rowCount()
        
        # Recopilar todos los pares clave-valor (excepto Titulo y Area que ya se manejan)
        dynamic_data = {}
        for r in range(rows):
            key_item = self.info_table.item(r, 0)
            val_item = self.info_table.item(r, 1)
            if key_item and val_item:
                k = key_item.text().strip()
                v = val_item.text().strip()
                dynamic_data[k] = v

        # A. Actualizar elementos por ID directo (ej: TITULO)
        for k, v in dynamic_data.items():
            layout_item = layout.itemById(k)
            if layout_item and isinstance(layout_item, QgsLayoutItemLabel):
                layout_item.setText(v)
        
        # B. Reemplazar variables {CLAVE} en TODAS las etiquetas
        # Esto cubre el caso donde PROPIETARIO, UBICACION, FECHA están dentro de un cuadro de texto grande
        for item in layout.items():
            if isinstance(item, QgsLayoutItemLabel):
                original_text = item.text()
                new_text = original_text
                for k, v in dynamic_data.items():
                    placeholder = "{" + k + "}"
                    if placeholder in new_text:
                        new_text = new_text.replace(placeholder, v)
                
                if new_text != original_text:
                    item.setText(new_text)

        # C. (Nuevo) Manejo especial para INFO_BOX: 
        # Si agregaste campos NUEVOS que NO están en la plantilla (ej: 'CLI' o 'CLIMA'),
        # los agregamos al cuadro INFO_BOX si existe.
        info_box = layout.itemById('INFO_BOX')
        if info_box and isinstance(info_box, QgsLayoutItemLabel):
            current_text = info_box.text()
            extra_text = ""
            
            # Campos estándar que ya esperamos que estén en la plantilla para no duplicarlos
            standard_keys = ['TITULO', 'PROPIETARIO', 'UBICACION', 'FECHA']
            
            for k, v in dynamic_data.items():
                # Si es un campo "extra" Y no fue reemplazado (porque no estaba el placeholder)
                # Lo agregamos al final
                if k not in standard_keys:
                    # Verificar si ya está en el texto (por si acaso el usuario sí puso {CLIMA})
                    if k not in current_text and v: 
                        extra_text += f"\n{k}: {v}"
            
            if extra_text:
                info_box.setText(current_text + extra_text)
    
    def _link_scalebar_to_map(self, layout, map_item):
        if not map_item:
            return
        for item in layout.items():
            if isinstance(item, QgsLayoutItemScaleBar):
                item.setLinkedMap(map_item)
                item.update()





class TopographicSurveyPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.actions = []
        self.menu = "&ArcGeek Topo"
        self.dialog = None
        self.provider = None
    
    
    def initGui(self):
        # 1. Generar Plano (Main) - Icono de Layout
        icon_main = QgsApplication.getThemeIcon("/mActionLayoutManager.svg")
        self.action_main = QAction(icon_main, "Generar Plano desde CSV/Excel", self.iface.mainWindow())
        self.action_main.triggered.connect(self.run)
        self.iface.addPluginToMenu(self.menu, self.action_main)
        self.actions.append(self.action_main)

        # 2. Crear Polígono desde CSV - Icono de CSV/Texto
        icon_csv = QgsApplication.getThemeIcon("/mActionAddDelimitedTextLayer.svg")
        self.action_csv_tool = QAction(icon_csv, "Crear Polígono desde CSV (Simple)", self.iface.mainWindow())
        self.action_csv_tool.triggered.connect(self.run_csv_tool)
        self.iface.addPluginToMenu(self.menu, self.action_csv_tool)
        self.actions.append(self.action_csv_tool)

        # 3. Extraer Puntos (Geometría) - Icono de Puntos
        icon_points = QgsApplication.getThemeIcon("/mActionCapturePoint.svg")
        self.action_tools = QAction(icon_points, "Extraer Puntos de Polígono (Geometría)", self.iface.mainWindow())
        self.action_tools.triggered.connect(self.run_polygon_tool)
        self.iface.addPluginToMenu(self.menu, self.action_tools)
        self.actions.append(self.action_tools)
        
        # 4. Exportar CSV - Icono de Guardar Tabla
        icon_export = QgsApplication.getThemeIcon("/mActionSave.svg")
        self.action_export_csv = QAction(icon_export, "Exportar Tabla a CSV/Excel", self.iface.mainWindow())
        self.action_export_csv.triggered.connect(self.run_export_csv)
        self.iface.addPluginToMenu(self.menu, self.action_export_csv)
        self.actions.append(self.action_export_csv)
        
        # Provider registration removed to keep toolbox clean
    
    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
    
    def run(self):
        if self.dialog is None:
            self.dialog = TopographicSurveyDialog(self.iface, self.iface.mainWindow())
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()

    def run_polygon_tool(self):
        try:
            from .from_polygon_to_points import PolygonToPointsAlgorithm
            import processing
            
            alg = PolygonToPointsAlgorithm()
            dlg = processing.createAlgorithmDialog(alg)
            dlg.setWindowTitle("Extraer Puntos de Polígono")
            dlg.exec()
        except Exception as e:
            self.iface.messageBar().pushMessage("Error", f"No se pudo abrir la herramienta: {e}", Qgis.Critical)

    def run_csv_tool(self):
        try:
            from .create_polygon_from_csv import CreatePolygonFromTableAlgorithm
            import processing
            
            alg = CreatePolygonFromTableAlgorithm()
            dlg = processing.createAlgorithmDialog(alg)
            dlg.setWindowTitle("Crear Polígono desde Tabla")
            dlg.exec()
        except Exception as e:
            self.iface.messageBar().pushMessage("Error", f"No se pudo abrir la herramienta: {e}", Qgis.Critical)

    def run_export_csv(self):
        try:
            from .export_to_csv import ExportToCSVAlgorithm
            import processing
            
            alg = ExportToCSVAlgorithm()
            dlg = processing.createAlgorithmDialog(alg)
            dlg.setWindowTitle("Exportar Tabla a CSV")
            dlg.exec()
        except Exception as e:
            self.iface.messageBar().pushMessage("Error", f"No se pudo abrir la herramienta: {e}", Qgis.Critical)


def classFactory(iface):
    return TopographicSurveyPlugin(iface)