# 📋 Guía de Continuación — Investigación CHSI × Cuenca del Río Tamesí

> **Última actualización:** 2026-05-22
> **Investigador:** Raúl Alejandro Morales Rivera, DCI, Posgrado FIT
> **Línea principal:** Remote Sensing and AI for the Inference and Quantification of Non-Observable Hydric Parameters

---

## 1. Estado Actual del Proyecto

### ✅ Completado
- [x] **Dataset ERA5-Land descargado** (28 años, 1998–2025, horario, variables `t2m`, `swvl1`, `pev`).
- [x] **Pipeline de preprocesamiento**: NetCDF → SQLite (`era5_stats.db`) + Store Zarr consolidado (`era5_land_tamaulipas.zarr`).
- [x] **Dashboard web interactivo** (FastAPI + Leaflet) operativo.
- [x] **Auditoría científica automatizada** (generación de reportes PDF/HTML en `/reports`).
- [x] **Análisis de correlación multivariante**: Correlación estacional, cross-correlation con desfase temporal (lags), PCA y tendencias a largo plazo de Mann-Kendall.
- [x] **Pipeline ML para derivación de CHSI**: Comparación de **Random Forest (RF)** vs. **Gradient Boosting Regressor (GBR)**. GBR supera a RF, reduciendo el RMSE en un 37.9% ($RMSE = 0.0072$ vs. $0.0116$) y alcanzando un $R^2$ promedio de $0.9958$ (Folds $k=5$, `TimeSeriesSplit`).
- [x] **Modularización de gráficos de publicación**: Todos los gráficos del artículo se extrajeron en scripts individuales dentro de `plot_src/` (`plot_01` a `plot_10`).
- [x] **Generación de figuras en calidad de publicación (300 DPI)**: Salidas guardadas en `reports/figures/` usando la estética profesional del artículo (serif, ticks, paletas adaptadas).
- [x] **Ajuste de ejes temporales**: Integración de reglas verticales estacionales (ejes secundarios superiores) en todos los gráficos cronológicos (Figuras 3, 6, 7, 8 y 10).
- [x] **Análisis MWT (Moving-Window Trend)**: Cálculo de pendientes móviles centradas a escala estacional (90 días) y anual (365 días), comparando el CHSI contra la dinámica de sus componentes normalized (Figuras 6 y 7).
- [x] **Comparación de Estados Normalizados**: Reconstrucción de series temporales con promedios móviles centrados de 30 días para evaluar umbrales físicos (Figura 8).
- [x] **Análisis de Regímenes Hidrológicos y SEA (Superposed Epoch Analysis)**: Análisis de pendientes de tendencias lineales dentro vs. fuera de sequía, y análisis de lead/lag en ventanas de 1, 2 y 5 años alrededor de eventos de inundación (Figuras 9 y 10).
- [x] **Borrador del Manuscrito Actualizado** (`article_draft.md`): Texto expandido que documenta los resultados del modelo GBR, interpretabilidad SHAP, MWT y análisis de régimen hidrológico/SEA.

### 🔲 Pendiente (Próximos Pasos para Finalizar el Artículo)
- [ ] **Adquisición de Datos Satelitales GPM IMERG**: Descargar datos diarios de precipitación de alta resolución del producto GPM IMERG Late Run V06 (0.1° de resolución, 2000–2025) para la delimitación de la cuenca.
- [ ] **Cálculo de Índices de Sequía Estándar**: Derivar el Standardized Precipitation Index (SPI-3/6) y Standardized Precipitation Evapotranspiration Index (SPEI-3/6) utilizando la precipitación de satélite IMERG y las variables térmicas/evaporativas de ERA5-Land.
- [ ] **Validación Cuantitativa Externa**: Calcular la correlación de Pearson ($r$) entre el CHSI diario y los índices SPI/SPEI-3/6 basados en satélite para validar la consistencia del CHSI contra métricas estándar. Completar las secciones con *Placeholders* en la Sección 4.7 y 5 del borrador del artículo (`article_draft.md`).
- [ ] **Escalamiento y Downscaling regional**: Implementar la fusión y downscaling espacial (10–100 m) integrando imágenes Sentinel-2 (NDVI, NDWI, MSI), Sentinel-1 (humedad del suelo) y MODIS (evapotranspiración y LST).

---

## 2. Estructura del Repositorio

```
c:\git\APPS\CDS\
│
├── era5_land.py                    # Descarga de datos ERA5-Land via CDS API
├── preprocess.py                   # Indexación a SQLite + consolidación Zarr
├── main.py                         # Servidor FastAPI (dashboard + API REST)
├── analytics_utils.py              # Auditoría científica (HTML/PDF reports)
├── correlation_analysis.py         # Análisis estadístico y tendencias base
├── ml_pipeline.py                  # Pipeline ML (entrenamiento e inferencia base)
├── validation.py                   # Validación contra eventos extremos base
├── article_draft.md                # Borrador del manuscrito con resultados actualizados
├── article_proposals.md            # Propuestas de revistas y plan de redacción
├── RESEARCH_CONTINUITY.md          # ← Este documento (Guía de continuidad)
├── pyproject.toml                  # Dependencias del proyecto (uv/pip)
├── uv.lock                         # Lockfile para entornos virtuales deterministas
├── .python-version                 # Versión de Python activa (3.13)
│
├── plot_src/                       # Scripts modulares de graficación de publicación
│   ├── plot_01_climatic_trends.py
│   ├── plot_02_seasonal_correlation.py
│   ├── plot_03_chsi_events.py
│   ├── plot_04_ml_comparison.py
│   ├── plot_05_feature_importances.py
│   ├── plot_06_chsi_seasonal_slopes_comparison.py
│   ├── plot_07_chsi_yearly_slopes_comparison.py
│   ├── plot_08_chsi_normalized_components_comparison.py
│   ├── plot_09_chsi_event_regime_sea_composite.py
│   └── plot_10_chsi_event_regime_chronological_overlay.py
│
├── tools/                          # Herramientas de análisis avanzado y ejecución por lotes
│   ├── generate_publication_plots.py  # Corre figuras 1–5 (estética paper)
│   ├── analyze_chsi_rolling_trends.py  # Corre figuras 6–8 y calcula estadísticas MWT
│   └── analyze_event_regime_trends.py  # Corre figuras 9–10 y calcula estadísticas de régimen/SEA
│
├── static/                         # Interfaz del dashboard interactivo
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
│
├── reports/                        # Reportes y salidas
│   ├── figures/                    # Figuras PNG en calidad de publicación (300 DPI)
│   │   ├── 01_climatic_trends.png
│   │   ├── 02_seasonal_correlation.png
│   │   ├── 03_chsi_events.png
│   │   ├── 04_ml_comparison.png
│   │   ├── 05_feature_importances.png
│   │   ├── 06_chsi_seasonal_slopes_comparison.png
│   │   ├── 07_chsi_yearly_slopes_comparison.png
│   │   ├── 08_chsi_normalized_components_comparison.png
│   │   ├── 09_chsi_event_regime_sea_composite.png
│   │   └── 10_chsi_event_regime_chronological_overlay.png
│   ├── correlation_report.html
│   ├── chsi_report.html
│   ├── validation_report.html
│   └── chsi_tamesi_1998_2025.csv   # Serie temporal del CHSI diario
│
├── era5_land_tamaulipas/           # 337 archivos NetCDF (Ignorado en git, ~480MB)
├── era5_land_tamaulipas.zarr/      # Store Zarr consolidado (Ignorado en git)
└── era5_stats.db                   # SQLite con stats horarias (Ignorado en git, ~155MB)
```

---

## 3. Setup en Nueva Estación de Trabajo

### Requisitos
- Python 3.13+
- Gestor de paquetes `uv` (altamente recomendado para instalación rápida y entornos virtuales limpios)
- ~500MB de espacio en disco para el reanálisis
- Clave de API de Copernicus CDS configurada en `~/.cdsapirc` (si se descargan nuevos datos)

### Instalación y Ejecución de Pipelines

```powershell
# 1. Clonar el repositorio
git clone <REPO_URL> CDS
cd CDS

# 2. Sincronizar el entorno virtual e instalar dependencias
uv sync

# 3. Descargar y preprocesar datos ERA5 (solo si no se transfirieron los datos locales)
# Requiere configurar ~/.cdsapirc previamente
uv run python era5_land.py
uv run python preprocess.py

# 4. Generar reportes básicos de investigación (HTML en reports/)
uv run python correlation_analysis.py
uv run python ml_pipeline.py
uv run python validation.py

# 5. Generar figuras del artículo científico (Figuras 1 a 5)
uv run python tools/generate_publication_plots.py

# 6. Ejecutar análisis de tendencias móviles y generar figuras 6 a 8
uv run python tools/analyze_chsi_rolling_trends.py

# 7. Ejecutar análisis de régimen hidrológico/SEA y generar figuras 9 y 10
uv run python tools/analyze_event_regime_trends.py

# 8. Lanzar servidor del dashboard interactivo
uv run python main.py
# -> Abrir http://127.0.0.1:8008 en su navegador
```

### Script de ejecución rápida para recrear todas las figuras de publicación:
```powershell
uv run python plot_src/plot_01_climatic_trends.py
uv run python plot_src/plot_02_seasonal_correlation.py
uv run python plot_src/plot_03_chsi_events.py
uv run python plot_src/plot_04_ml_comparison.py
uv run python plot_src/plot_05_feature_importances.py
uv run python plot_src/plot_06_chsi_seasonal_slopes_comparison.py
uv run python plot_src/plot_07_chsi_yearly_slopes_comparison.py
uv run python plot_src/plot_08_chsi_normalized_components_comparison.py
uv run python plot_src/plot_09_chsi_event_regime_sea_composite.py
uv run python plot_src/plot_10_chsi_event_regime_chronological_overlay.py
```

---

## 4. Descripción Técnica de los Módulos de Análisis

### A. Scripts Base del Repositorio

*   **`era5_land.py`**: Utiliza `cdsapi` para consultar y descargar en paralelo los 337 archivos mensuales de reanálisis ERA5-Land correspondientes al bounding box del sur de Tamaulipas.
*   **`preprocess.py`**: Lee los archivos NetCDF mensuales usando `xarray`/`netcdf4` y realiza una doble exportación:
    1.  Consolida las series temporales por celda en un almacén optimizado **Zarr**.
    2.  Calcula estadísticas descriptivas horarias (media regional) y las almacena en la tabla `hourly_stats` de una base de datos **SQLite** (`era5_stats.db`) para consultas rápidas.
*   **`correlation_analysis.py`**: Realiza los análisis preliminares de correlación y tendencias básicas de Mann-Kendall. Genera el reporte HTML científico `reports/correlation_report.html`.
*   **`ml_pipeline.py`**: Ejecuta el pipeline de ingeniería de variables sintéticas (23 features físicas, incluyendo el índice de estrés térmico-hídrico, derivadas temporales y codificaciones de ciclo solar). Entrena los modelos e infiere el CHSI. Exporta el reporte de desempeño y la serie diaria reconstruida en `reports/chsi_tamesi_1998_2025.csv`.
*   **`validation.py`**: Implementa la validación direccional estática del CHSI y clasificaciones binarias contra un catálogo de 9 eventos extremos (d droughts, 5 floods) documentados históricamente en Tamaulipas. Genera `reports/validation_report.html`.
*   **`main.py`**: Servidor en FastAPI que sirve los reportes estáticos HTML e implementa una API REST para entregar la serie de CHSI y los reportes a la interfaz interactiva.

### B. Herramientas Especializadas de Análisis (`tools/`)

*   **`tools/generate_publication_plots.py`**:
    *   Carga datos históricos regionales consolidados desde SQLite.
    *   Genera las Figuras 1 a 5 con estilo académico refinado (serif, sin bordes laterales sobrantes `sns.despine`, alta resolución de 300 DPI).
*   **`tools/analyze_chsi_rolling_trends.py`**:
    *   Calcula pendientes de tendencias lineales con regresión por mínimos cuadrados mediante una ventana móvil centrada.
    *   Implementa la escala estacional (90 días) y anual (365 días) de pendientes móviles.
    *   Calcula y visualiza la serie diaria normalizada suavizada con una ventana centrada de 30 días para los 3 componentes físicos.
    *   Genera las Figuras 6, 7 y 8, dividiendo la visualización en 3 paneles cronológicos (1998–2006, 2007–2015, 2016–2025).
    *   Imprime estadísticas del MWT en consola para la redacción del texto de discusión.
*   **`tools/analyze_event_regime_trends.py`**:
    *   Realiza análisis estadístico comparativo de tendencias lineales de CHSI diferenciando periodos dentro vs. fuera de sequía.
    *   Implementa el análisis SEA (Superposed Epoch Analysis) centrando los 5 eventos de inundación/huracán en $t=0$, calculando las tendencias agregadas pre-evento y post-evento (ventanas de 1, 2 y 5 años).
    *   Genera la Figura 9 (comparación de pendientes y trazo compuesto del SEA con error estándar de la media $\pm 1\ \text{SEM}$).
    *   Genera la Figura 10 (línea temporal unificada con segmentos de regresión localizados sobre sequías fragmentadas por lluvias y periodos baseline de no-sequía fragmentados por inundaciones).
    *   Imprime las métricas de pendientes y valores p en consola.

### C. Módulos de Graficación Modular (`plot_src/`)

Para mantener el código ordenado y permitir ejecuciones aisladas de figuras específicas, cada gráfico del borrador se encuentra en un script dedicado:
1.  **`plot_01_climatic_trends.py`**: Tendencias a largo plazo de las variables físicas anualizadas con ajuste de línea de regresión e indicadores de significancia de Mann-Kendall.
2.  **`plot_02_seasonal_correlation.py`**: Correlación multivariada entre componentes del balance hídrico desglosada por estaciones meteorológicas (DJF, MAM, JJA, SON).
3.  **`plot_03_chsi_events.py`**: Reconstrucción temporal de CHSI diaria y suavizada a 30 días anotada con las ventanas temporales y códigos (D1–D4, F1–F5) de eventos extremos históricos.
4.  **`plot_04_ml_comparison.py`**: Comparación de métricas de desempeño ($R^2$ y $RMSE$) por fold de validación cruzada temporal entre Random Forest y Gradient Boosting.
5.  **`plot_05_feature_importances.py`**: Gráfico de barras horizontales con las 10 variables sintéticas más relevantes según la importancia interna del modelo GBR.
6.  **`plot_06_chsi_seasonal_slopes_comparison.py`**: Pendientes de regresión lineal móviles de 90 días (velocidad seasonal) del CHSI y componentes físicos en 3 paneles cronológicos.
7.  **`plot_07_chsi_yearly_slopes_comparison.py`**: Pendientes móviles anuales (365 días) de CHSI y componentes físicos para extraer tendencias de fondo multianuales libres de estacionalidad (3 paneles).
8.  **`plot_08_chsi_normalized_components_comparison.py`**: Estados físicos suavizados (30 días centrados) de humedad del suelo, temperatura y evaporación vs. CHSI (3 paneles).
9.  **`plot_09_chsi_event_regime_sea_composite.py`**: Panel doble que compara las pendientes de regresión de los regímenes hidrológicos y las ventanas pre/post flood, junto con el compuesto promedio y la dispersión $\pm 1\ \text{SEM}$ del análisis de época superpuesta.
10. **`plot_10_chsi_event_regime_chronological_overlay.py`**: Cronología completa de 28 años que superpone los tramos de regresión locales para sequías (divididas en presencia de inundaciones), baseline de no-sequía e intervalos de acumulación (pre) y relajación (post) de inundaciones a 2 años.

---

## 5. Especificaciones del Dataset e Índice

### A. Grilla ERA5-Land (Área de Estudio)
-   **Coordenadas geográficas**: Latitud $[22^\circ\text{N}, 24^\circ\text{N}]$, Longitud $[-99^\circ\text{W}, -97^\circ\text{W}]$.
-   **Puntos de grilla**: $21 \text{ lat} \times 21 \text{ lon} = 441 \text{ celdas}$.
-   **Resolución**: 0.1° ($\approx 9\ \text{km}$).
-   **Registros temporales**: $\approx 245,107$ pasos de tiempo horarias por celda.

### B. Formulación del Target Físico
El target diario se construyó a partir del promedio regional diario de variables escaladas en rango $[0,1]$:
$$\text{CHSI}_{\text{target}} = \frac{T_{2m, \text{norm}} + (1 - \theta_{\text{swvl1}, \text{norm}}) + |E_{\text{pev}}|_{\text{norm}}}{3}$$
-   $T_{2m, \text{norm}}$: Temperatura media normalizada (estresor térmico).
-   $1 - \theta_{\text{swvl1}, \text{norm}}$: Sequedad del suelo superficial normalizada (estresor hídrico).
-   $|E_{\text{pev}}|_{\text{norm}}$: Magnitud de evaporación potencial acumulada normalizada (estresor evaporativo).
-   **Rango**: $[0, 1]$, donde $0$ representa saturación y enfriamiento máximo (sin estrés) y $1$ representa sequía y estrés térmico/evaporativo extremo.

### C. Desempeño del Modelo
Comparación consolidada de la validación cruzada temporal en 5 Folds:
-   **Random Forest**: $R^2 \text{ promedio} = 0.9897$, $RMSE \text{ promedio} = 0.0116$.
-   **Gradient Boosting Regressor (GBR)**: $R^2 \text{ promedio} = 0.9958$, $RMSE \text{ promedio} = 0.0072$.
-   El modelo GBR reduce el error absoluto promedio de reconstrucción en un **37.9%** con respecto a RF y captura significativamente mejor las transiciones abruptas hacia sequías severas o saturaciones por huracanes.

---

## 6. Resultados del Análisis de Tendencias y Regímenes

### A. Tendencias Climáticas a Largo Plazo
Análisis de Mann-Kendall sobre promedios anuales (1998–2025):
-   **Calentamiento**: $+0.0387^\circ\text{C}/\text{año}$ ($p = 0.0032$, estadísticamente muy significativo). Equivalente a $+1.08^\circ\text{C}$ acumulados.
-   **Evaporación Potencial**: Aumento absoluto significativo de la demanda evaporativa ($p = 0.0350$).
-   **Humedad del Suelo**: Tendencia negativa no significativa a escala regional.

### B. Análisis de Velocidades MWT (Figuras 6 y 7)
-   **Pico de pendiente estacional**: $+1.53831\ \text{año}^{-1}$ (secado rápido) y $-2.37934\ \text{año}^{-1}$ (recuperación extrema por lluvia).
-   **Pico de pendiente anual**: Centrado en el **24 de febrero de 2009** ($+0.35861\ \text{año}^{-1}$). Este ciclo de secado crítico estuvo liderado por el vaciado del suelo (pendiente de sequedad de $+0.54017\ \text{año}^{-1}$), acompañado de calentamiento local ($+0.27577^\circ\text{C}/\text{año}$) e incremento de la demanda evaporativa ($+0.25990\ \text{año}^{-1}$).

### C. Análisis de Tendencias por Regímenes e Intervalos de Eventos (Figuras 9 y 10)
Análisis estadístico de la dinámica de CHSI (Tabla 5 del manuscrito):
-   **Tendencia dentro de sequías (D1–D4)**: $+0.005713\ \text{año}^{-1}$ ($p < 0.0001$). El estrés hídrico se acelera a más del doble del ritmo de fondo.
-   **Tendencia fuera de sequías (Baseline)**: $+0.002712\ \text{año}^{-1}$ ($p < 0.0001$). Existe un secado sistemático de fondo a largo plazo.
-   **Ventana Pre-Inundación (1 y 2 años)**: Pendientes altamente positivas ($+0.064908\ \text{año}^{-1}$ a 1 año; $+0.023604\ \text{año}^{-1}$ a 2 años). Esto demuestra físicamente que las inundaciones extremas actúan como "rompe-sequías", ocurriendo al final de ciclos severos de secado.
-   **Ventana Post-Inundación (Velocidad de Relajación a 1 año)**: $+0.118477\ \text{año}^{-1}$ ($p < 0.0001$). Después de la saturación provocada por tormentas, el sistema experimenta una rápida deshidratación de retorno hacia su estado de equilibrio o sequía latente.

---

## 7. Plan de Validación Satelital Pendiente (IMERG)

Para la robustez científica del artículo y completar las secciones vacías en el borrador, se debe llevar a cabo la validación cruzada con datos de satélite independientes:

### 1. Adquisición del Producto IMERG
-   **Fuente**: NASA GES DISC (GPM_3IMERGDL).
-   **Periodo**: 2000–2025.
-   **Resolución**: 0.1° diaria (Late Run).
-   **Procesamiento**: Filtrar y promediar espacialmente para el bounding box de la cuenca del Tamesí para obtener la precipitación diaria regionalizada en milímetros ($P_{\text{sat}}$).

### 2. Cálculo de Índices SPI y SPEI
-   **SPI (Standardized Precipitation Index)**: Calcular SPI a escalas de 3 y 6 meses a partir de la serie de precipitación IMERG.
-   **SPEI (Standardized Precipitation Evapotranspiration Index)**:
    -   Estimar el balance hídrico simplificado $D = P_{\text{sat}} - PET$, donde $PET$ es la evapotranspiración potencial calculada a partir de las variables de ERA5-Land (por ejemplo, usando la estimación directa de $pev$ o fórmulas empíricas basadas en $t2m$ y radiación solar).
    -   Ajustar a una distribución de probabilidad (Log-Logística) a escalas de 3 y 6 meses.

### 3. Correlación y Validación Cruzada
-   **Análisis**: Correlacionar la serie reconstruida del CHSI diario (y promedios mensuales) contra las series de SPI-3, SPI-6, SPEI-3 y SPEI-6.
-   **Hipótesis de Consistencia Física**: Se espera una correlación de Pearson sustancialmente mayor con SPEI ($r > 0.80$) que con SPI ($r \approx 0.60$), dado que el CHSI integra explícitamente la retroalimentación térmica y evaporativa de la superficie y la atmósfera baja en lugar de basarse puramente en la oferta de lluvia.
-   **Actualización del Draft**: Escribir los coeficientes $r$ finales y actualizar la Tabla 5 y las figuras correspondientes en la sección 4.7 y 5 de `article_draft.md`.

---

## 8. Dependencias del Proyecto (`pyproject.toml`)

El entorno virtual se define con las siguientes dependencias clave (reproducibilidad garantizada):
```toml
dependencies = [
    "fastapi>=0.136.0",        # Servidor de API y dashboard
    "jinja2>=3.1.6",           # Renderizado de reportes HTML
    "matplotlib>=3.10.8",      # Graficación y exportación de figuras
    "netcdf4>=1.7.4",          # Lectura de NetCDF4 de ERA5
    "numpy>=2.4.4",            # Álgebra lineal y procesamiento matricial
    "pandas>=3.0.2",           # Gestión de DataFrames y series de tiempo
    "seaborn>=0.13.2",         # Estilos visuales de publicación
    "uvicorn>=0.44.0",         # Servidor ASGI para FastAPI
    "xarray>=2026.4.0",        # Manejo de datasets NetCDF multidimensionales
    "cdsapi>=0.7.3",           # Descarga automatizada de Copernicus CDS
    "dask>=2025.2.0",          # Procesamiento en paralelo de NetCDF
    "zarr>=3.0.1",             # Store Zarr optimizado para series multidimensionales
    "scipy>=1.17.1",           # Regresión lineal, tendencias y cómputo matemático
    "fpdf2>=2.8.7",            # Exportación de reportes científicos a PDF
    "scikit-learn>=1.6.0",     # Entrenamiento de Random Forest, GBR y PCA
]
```

---

## 9. Literatura Clave para Revisar y Citar

Para contextualizar teóricamente la metodología y compararla con las metodologías oficiales nacionales:
1.  **Monitor de Sequía de México (MSM - CONAGUA)**:
    *   *Cita*: Lobato-Sánchez, R. (2016). *El monitor de la sequía en México*. Tecnología y ciencias del agua, 7(5), 143-156.
    *   *Propósito*: Conectar la justificación del CHSI como un proxy continuo y dinámico frente a la aproximación estática basada en el modelo Leaky Bucket de la NOAA y datos dispersos de estaciones de CONAGUA.
2.  **SPEI en el Contexto del Calentamiento en México**:
    *   *Cita*: Comparación de la sensibilidad de SPEI frente a SPI bajo tendencias de calentamiento regional. Justifica la necesidad de integrar la evapotranspiración potencial ($pev$) y la temperatura ($t2m$) en el monitoreo del estrés hídrico de la cuenca (e.g., estudios en *Atmosphere* 2025).
3.  **Balance Hídrico del Sistema Lagunario de Tampico-Madero-Altamira**:
    *   *Propósito*: Contextualizar en la Introducción la vulnerabilidad socioeconómica y ambiental de la desembocadura de la cuenca Guayalejo-Tamesí.
