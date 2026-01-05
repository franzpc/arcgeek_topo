"""
ArcGeek Topo
Plugin de QGIS para generar automáticamente planos topográficos

Compatible con Qt5/Qt6 y QGIS 3.34+/4.x

Autor: ArcGeek
Versión: 1.0
"""

def classFactory(iface):
    """Función de fábrica requerida por QGIS"""
    from .topographic_survey_plugin import TopographicSurveyPlugin
    return TopographicSurveyPlugin(iface)