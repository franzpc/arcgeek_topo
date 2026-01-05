# Generador de Levantamientos Topográficos v2.0 - Con Layouts Editables

## 🎯 ¿Qué hay de nuevo en v2.0?

### ✨ **LAYOUTS EDITABLES EN QGIS**

Ahora el plugin crea el layout **directamente en QGIS** para que puedas editarlo manualmente:

- ✅ Layout completo con todos los elementos
- ✅ Mapa del terreno con capas editables
- ✅ Cuadro de construcción
- ✅ Títulos y etiquetas
- ✅ Escala gráfica
- ✅ Flecha de norte
- ✅ **Todo editable** - cambias colores, fuentes, posiciones, etc.
- ✅ Exportas a PDF cuando quieras

---

## 🆕 CARACTERÍSTICAS NUEVAS

### 3 Capas Vectoriales Creadas:

1. **Levantamiento_Topográfico** - Polígono del terreno
2. **Vértices** - Puntos numerados en cada vértice
3. **Medidas** - Líneas con etiquetas de distancia y rumbo

### Layout Completo Editable:

- Mapa principal con extent ajustado
- Cuadro de construcción (tabla HTML)
- Información del propietario
- Ubicación completa
- Simbología
- Sistema de coordenadas
- Escala gráfica
- Flecha de norte

### Flujo de Trabajo:

```
CSV → Plugin → Capas en QGIS + Layout → Editas manualmente → Exportas PDF
```

---

## 📋 Instalación

### Requisitos:
- QGIS 3.0 o superior
- Python 3.6+
- pandas (para leer CSV)

### Pasos:

1. **Copiar plugin a carpeta de QGIS:**

   **Windows:**
   ```
   C:\Users\[USUARIO]\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\topographic_survey_v2\
   ```

   **Linux:**
   ```
   ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/topographic_survey_v2/
   ```

2. **Instalar pandas en QGIS:**

   Abre la Consola Python de QGIS y ejecuta:
   ```python
   import subprocess, sys
   subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas"])
   ```

3. **Activar plugin:**
   - `Complementos → Administrar complementos → Instalados`
   - Busca "Generador de Levantamientos Topográficos"
   - Actívalo ✅

4. **Reinicia QGIS**

---

## 🚀 Cómo Usar

### Paso 1: Abrir la herramienta

`Complementos → Levantamientos Topográficos → Generar Levantamiento Topográfico`

### Paso 2: Configurar parámetros

**1. Archivo de Coordenadas**
- Examinar → Selecciona tu CSV
- Columna X (Este)
- Columna Y (Norte)

**2. Sistema de Coordenadas**
- Selecciona de la lista (ej: EPSG:32613 - UTM 13N)

**3. Información del Predio** _(opcional)_
- Propietario
- Ubicación
- Poblado
- Municipio
- Estado

**4. Opciones de Salida**
- ✅ **Crear Layout en QGIS** (editable) - ¡Recomendado!
- ☐ Exportar también a PDF (opcional)

### Paso 3: Generar

Click en **"Generar Levantamiento"**

### Paso 4: Editar en QGIS

El plugin:
1. Crea 3 capas vectoriales
2. Genera el layout completo
3. **Abre el layout automáticamente**

Ahora puedes:
- Mover elementos del layout
- Cambiar colores y fuentes
- Ajustar tamaños
- Agregar logos
- Modificar el cuadro de construcción
- Cambiar estilos de las capas
- **¡Personalizarlo completamente!**

### Paso 5: Exportar

Cuando termines de editar:
1. En el layout: `Layout → Exportar como PDF`
2. ¡Listo!

---

## 📊 Formato del CSV

```csv
Punto;X(Este);Y(Norte)
1;598791.625;2742655.116
2;598780.340;2742638.604
3;598799.495;2742624.990
4;598854.594;2742634.993
5;598835.922;2742648.422
6;598824.348;2742632.112
```

**Importante:**
- Separador: `;` (punto y coma)
- Columnas X e Y numéricas
- Puntos ordenados

---

## 💡 Ventajas de v2.0

### Antes (v1.0):
```
CSV → PDF directo (no editable)
```

### Ahora (v2.0):
```
CSV → Layout en QGIS → Editas → PDF
```

**Beneficios:**
- ✅ Control total sobre el diseño
- ✅ Modificas lo que quieras
- ✅ Agregas elementos adicionales
- ✅ Cambias colores y estilos
- ✅ Guardas el proyecto para reutilizar
- ✅ Exportas cuando estés listo

---

## 🎨 Elementos del Layout

El layout incluye:

### Mapa Principal (280x180mm)
- Polígono del terreno
- Vértices numerados con etiquetas
- Líneas de medidas con distancias y rumbos
- Extent ajustado automáticamente

### Cuadro de Construcción
- Tabla HTML con todos los datos
- Punto, X, Y, Lado, Rumbo, Distancia
- Superficie total

### Información
- Título del levantamiento
- Datos del propietario
- Ubicación completa
- Simbología
- Sistema de coordenadas

### Elementos Cartográficos
- Escala gráfica
- Flecha de norte
- Marco del mapa

---

## 🔧 Personalización

### Cambiar colores del polígono:
1. Click derecho en capa "Levantamiento_Topográfico"
2. Propiedades → Simbología
3. Cambia color de relleno y borde

### Cambiar estilo de vértices:
1. Click derecho en capa "Vértices"
2. Propiedades → Simbología
3. Cambia símbolo y tamaño

### Modificar texto del layout:
1. Doble click en cualquier elemento de texto
2. Edita el contenido
3. Cambia fuente, tamaño, color

### Agregar logo de empresa:
1. En el layout: `Agregar elemento → Agregar imagen`
2. Selecciona tu logo
3. Posiciona donde quieras

---

## 📐 Cálculos Automáticos

El plugin calcula todo automáticamente:

- **Rumbos**: Formato topográfico (N 34-21-1 W)
- **Distancias**: Euclidianas en metros
- **Área**: Fórmula de Gauss (Shoelace)
- **Perímetro**: Suma de distancias

---

## ⚡ Para 1200 Mapas

### Opción 1: Individual (ahora)
- Generas layout para cada CSV
- Editas si es necesario
- Exportas a PDF
- ~2 minutos por mapa

### Opción 2: Procesamiento en lote (próximo)
- Script que procesa todos los CSVs
- Genera layouts automáticamente
- Exporta PDFs masivamente
- ~10 segundos por mapa

---

## 🆘 Solución de Problemas

**Layout no se abre:**
- Verifica que el plugin esté activado
- Reinicia QGIS

**Capas no se ven:**
- Verifica el sistema de coordenadas
- Zoom a la capa del levantamiento

**Error al leer CSV:**
- Verifica que use `;` como separador
- Asegura que coordenadas sean numéricas

**Etiquetas no se ven:**
- Haz zoom al mapa
- Ajusta el tamaño de fuente de las etiquetas

---

## 📚 Comparación v1.0 vs v2.0

| Característica | v1.0 | v2.0 |
|----------------|------|------|
| Genera PDF | ✅ | ✅ |
| Layout editable | ❌ | ✅ |
| Capas vectoriales | ❌ | ✅ (3 capas) |
| Personalización | ❌ | ✅ Total |
| Agregar elementos | ❌ | ✅ |
| Modificar estilos | ❌ | ✅ |
| Guardar proyecto | ❌ | ✅ |

---

## 🎯 Flujo Recomendado

### Para un solo mapa:
1. Abre el plugin
2. Carga CSV
3. Genera layout
4. Edita en QGIS
5. Exporta PDF

### Para múltiples mapas con el mismo estilo:
1. Crea el primer layout
2. Personalízalo completamente
3. Guarda el proyecto QGIS como plantilla
4. Para los siguientes:
   - Abre la plantilla
   - Carga nuevo CSV
   - Regenera solo las capas
   - Exporta

---

## 💾 Archivos Generados

- **Capas vectoriales**: En memoria (no se guardan automáticamente)
- **Layout**: En el proyecto QGIS
- **PDF**: Solo si marcas "Exportar también a PDF"

**Tip:** Guarda el proyecto QGIS para conservar todo.

---

## 🚀 Próximas Mejoras

- [ ] Procesamiento en lote de múltiples CSVs
- [ ] Plantillas de layout personalizables
- [ ] Exportación automática a DWG/DXF
- [ ] Integración con Google Maps para ubicación
- [ ] Generación de memorias descriptivas

---

## 📞 Soporte

Si encuentras problemas:
1. Verifica el formato del CSV
2. Confirma que pandas esté instalado
3. Reinicia QGIS
4. Revisa el sistema de coordenadas

---

**Versión:** 2.0  
**Compatible con:** QGIS 3.0+  
**Requiere:** pandas

¡Disfruta creando tus levantamientos topográficos con total control! 🎉
