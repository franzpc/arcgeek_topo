"""
Módulo de cálculos topográficos
Compatible con Qt5/Qt6 y QGIS 3.x/4.x
"""
import math


class TopographicCalculator:
    """Clase para cálculos topográficos"""
    
    @staticmethod
    def calculate_bearing(x1, y1, x2, y2):
        """
        Calcula el rumbo entre dos puntos.
        
        Args:
            x1, y1: Coordenadas del punto inicial
            x2, y2: Coordenadas del punto final
        
        Returns:
            tuple: (rumbo en formato topográfico, azimut en grados)
        """
        dx = x2 - x1
        dy = y2 - y1
        
        azimut_rad = math.atan2(dx, dy)
        azimut_deg = math.degrees(azimut_rad)
        
        if azimut_deg < 0:
            azimut_deg += 360
        
        # Determinar cuadrante
        if 0 <= azimut_deg < 90:
            angle = azimut_deg
            quadrant = "NE"
        elif 90 <= azimut_deg < 180:
            angle = 180 - azimut_deg
            quadrant = "SE"
        elif 180 <= azimut_deg < 270:
            angle = azimut_deg - 180
            quadrant = "SW"
        else:
            angle = 360 - azimut_deg
            quadrant = "NW"
        
        # Convertir a grados-minutos-segundos
        degrees = int(angle)
        minutes_decimal = (angle - degrees) * 60
        minutes = int(minutes_decimal)
        seconds = int((minutes_decimal - minutes) * 60)
        
        # Formatear rumbo
        if quadrant == "NE":
            bearing = f"N {degrees}-{minutes}-{seconds} E"
        elif quadrant == "SE":
            bearing = f"S {degrees}-{minutes}-{seconds} E"
        elif quadrant == "SW":
            bearing = f"S {degrees}-{minutes}-{seconds} W"
        else:
            bearing = f"N {degrees}-{minutes}-{seconds} W"
        
        return bearing, azimut_deg
    
    @staticmethod
    def calculate_distance(x1, y1, x2, y2):
        """
        Calcula la distancia euclidiana entre dos puntos.
        
        Args:
            x1, y1: Coordenadas del punto inicial
            x2, y2: Coordenadas del punto final
        
        Returns:
            float: Distancia en las mismas unidades de las coordenadas
        """
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    @staticmethod
    def calculate_area(coordinates):
        """
        Calcula el área del polígono usando la fórmula de Gauss (Shoelace).
        
        Args:
            coordinates: Lista de tuplas (x, y)
        
        Returns:
            float: Área en unidades cuadradas
        """
        n = len(coordinates)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += coordinates[i][0] * coordinates[j][1]
            area -= coordinates[j][0] * coordinates[i][1]
        return abs(area) / 2.0
    
    @staticmethod
    def calculate_perimeter(survey_table):
        """
        Calcula el perímetro sumando las distancias.
        
        Args:
            survey_table: Lista de diccionarios con campo 'distancia'
        
        Returns:
            float: Perímetro total
        """
        return sum([row['distancia'] for row in survey_table])
    
    @staticmethod
    def generate_survey_table(coordinates):
        """
        Genera la tabla de levantamiento completa.
        
        Args:
            coordinates: Lista de tuplas (x, y)
        
        Returns:
            tuple: (survey_table, area)
                - survey_table: Lista de diccionarios con punto, x, y, lado, rumbo, distancia, azimut
                - area: Área del polígono
        """
        calc = TopographicCalculator()
        area = calc.calculate_area(coordinates)
        
        survey_table = []
        n = len(coordinates)
        
        for i in range(n):
            j = (i + 1) % n
            x1, y1 = coordinates[i]
            x2, y2 = coordinates[j]
            
            bearing, azimut = calc.calculate_bearing(x1, y1, x2, y2)
            distance = calc.calculate_distance(x1, y1, x2, y2)
            
            survey_table.append({
                'punto': i + 1,
                'x': x1,
                'y': y1,
                'lado': f"{i + 1} - {j + 1}",
                'rumbo': bearing,
                'distancia': round(distance, 2),
                'azimut': azimut
            })
        
        return survey_table, area