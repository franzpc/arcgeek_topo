# ArcGeek Topo - Generador de Levantamientos Topográficos

**Versión:** 1.0.0  
**Compatible con:** QGIS 3.40 - 4.x  
**Licencia:** GNU GPL v3  

Plugin para QGIS que automatiza la creación de planos y layouts topográficos a partir de coordenadas CSV/Excel, incluyendo herramientas de procesamiento geométrico y exportación.

---

## 🚀 Características Principales

### 1. 🏗️ Generador de Planos Automático
Crea un proyecto completo de levantamiento topográfico a partir de un archivo de coordenadas:
- **Capas Vectoriales**: Genera automáticamente polígono, vértices numerados y líneas de medidas.
- **Cálculos**: Rumbo, distancia, área y perímetro calculados e insertados.
- **Layout Inteligente**: Genera una composición de impresión (Layout) editable con:
  - Mapa centrado y escalado.
  - Cuadro de construcción (Tabla de derroteros).
  - Escala gráfica, norte y membrete.
- **Soporte de Formatos**: Lee CSV, TXT y Excel (.xlsx).

### 2. 🔌 Herramientas de Processing
Incluye herramientas integradas en la Caja de Herramientas de Procesos de QGIS:

*   **Crear Polígono desde CSV (Simple)**: 
    *   Convierte rápidamente una tabla de coordenadas en capas de polígono y puntos sin generar layout. Ideal para análisis rápido.
*   **Extraer Puntos Ordenados de Polígonos**: 
    *   Obtiene los vértices de cualquier capa de polígonos, ordenados horaria y antihorariamente, listos para generar cuadros de construcción.
*   **Exportar Tabla a CSV/Excel**:
    *   Exporta atributos de cualquier capa a CSV compatible con Excel (UTF-8 con BOM), solucionando problemas comunes de caracteres especiales.

---

## 📋 Requisitos e Instalación

### Requisitos
- **QGIS**: Versión 3.40 o superior.
- **Librerías Python**: Requiere `pandas` (normalmente incluido en QGIS moderno o fácil de instalar).

### Instalación
1. Descarga el archivo ZIP del repositorio o instálalo desde el Administrador de Complementos de QGIS (si está disponible).
2. Si es manual: `Complementos` -> `Administrar e Instalar Complementos` -> `Instalar a partir de ZIP`.

---

## 📖 Cómo Usar

### Generar un Plano Completo
1. Ve al menú **ArcGeek Topo** > **Generar Plano desde CSV/Excel**.
2. **Pestaña Datos**: Carga tu archivo CSV/Excel y selecciona las columnas X (Este) y Y (Norte). Elige el sistema de coordenadas (CRS).
3. **Pestaña Información**: Rellena los datos del proyecto (Propietario, Ubicación, etc.). Puedes añadir campos personalizados.
4. **Pestaña Impresión**: 
   - Elige el tamaño de papel (A4, A3, Carta, Oficio) y orientación.
   - **NUEVO**: Puedes usar tu propia **plantilla personalizada (.qpt)** marcando la casilla correspondiente.
5. **Pestaña Generar**: Haz clic en "Generar Plano".
6. El plugin creará las capas y abrirá el Layout listo para imprimir o exportar a PDF.

### Herramientas Individuales
Accede desde el menú **ArcGeek Topo**:
- **Crear Polígono desde CSV**: Para obtener geometrías rápidas sin layout.
- **Extraer Puntos**: Para analizar polígonos existentes.
- **Exportar CSV**: Para guardar datos de atributos en formato compatible con Excel.

---

## 📄 Formato de Datos (CSV/Excel)

El archivo de entrada debe tener al menos columnas de coordenadas. Ejemplo:

| Punto | Este (X) | Norte (Y) |
|-------|----------|-----------|
| 1     | 500.00   | 1000.00   |
| 2     | 550.50   | 1020.30   |
| 3     | 540.20   | 1080.10   |

*El separador de CSV se detecta automáticamente (; , | tab).*

---

## 🛠️ Soporte y Contacto

**Repositorio y Tracker:** [https://github.com/franzpc/arcgeek_topo](https://github.com/franzpc/arcgeek_topo)  
**Email:** soporte@arcgeek.com  
**Autor:** ArcGeek

---
*Hecho con ❤️ para la comunidad de QGIS.*
