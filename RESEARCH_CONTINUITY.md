# 📋 Guía de Continuación — Investigación CHSI × Cuenca del Tamesí

> **Última actualización:** 2026-05-15
> **Investigador:** Raúl Alejandro Morales Rivera, DCI, Posgrado FIT
> **Línea principal:** Remote Sensing and AI for the Inference and Quantification of Non-Observable Hydric Parameters

---

## 1. Estado Actual del Proyecto

### ✅ Completado
- [x] Dataset ERA5-Land descargado (28 años, 1998–2025, horario, 3 variables)
- [x] Pipeline de preprocesamiento: NetCDF → SQLite (stats) + Zarr (optimizado)
- [x] Dashboard web interactivo (FastAPI + Leaflet)
- [x] Auditoría científica automatizada (HTML + PDF)
- [x] Análisis de correlación multivariante (multi-escala, estacional, PCA, trends)
- [x] Pipeline ML para derivación del CHSI (Random Forest, TimeSeriesSplit k=5)
- [x] Validación contra 9 eventos extremos documentados (100% concordancia)
- [x] CHSI exportado como CSV (reports/chsi_tamesi_1998_2025.csv)
- [x] 3 API endpoints nuevos integrados al servidor

### 🔲 Pendiente (para el artículo)
- [ ] Agregar SHAP values para interpretabilidad del modelo RF
- [ ] Obtener datos del Monitor de Sequía de México (CONAGUA/SMN) para validación cuantitativa
- [ ] Comparar CHSI contra índices establecidos (SPI, SPEI, PDSI) si hay datos disponibles
- [ ] Entrenar variante con XGBoost y comparar con RF
- [ ] Redactar borrador del artículo
- [ ] Generar figuras en calidad de publicación (300 dpi, formato vectorial)

---

## 2. Estructura del Repositorio

```
c:\APPS\CDS\
│
├── era5_land.py              # Descarga de datos ERA5-Land via CDS API
├── preprocess.py             # Indexación a SQLite + consolidación Zarr
├── main.py                   # Servidor FastAPI (dashboard + API REST)
├── analytics_utils.py        # Auditoría científica (HTML/PDF reports)
├── correlation_analysis.py   # Correlación multivariante (nuevo)
├── ml_pipeline.py            # Pipeline ML para derivación del CHSI (nuevo)
├── validation.py             # Validación contra eventos extremos (nuevo)
├── article_proposals.md      # Propuestas de artículo y resultados
├── RESEARCH_CONTINUITY.md    # ← Este documento
│
├── pyproject.toml            # Dependencias del proyecto
├── uv.lock                   # Lock file de uv
├── .python-version           # Python 3.13
├── run.bat                   # Script de ejecución del servidor
├── .gitignore
│
├── static/                   # Frontend del dashboard
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
│
├── era5_land_tamaulipas/     # 337 archivos NetCDF (NO en git, ~480MB)
├── era5_land_tamaulipas.zarr/ # Store Zarr consolidado (NO en git)
├── era5_stats.db             # SQLite con stats horarias (NO en git, ~155MB)
├── datasets_manifest.json    # Manifest pre-generado (NO en git, ~8MB)
│
└── reports/                  # Reportes generados
    ├── correlation_report.html  # Análisis de correlación (1.1MB)
    ├── chsi_report.html         # Reporte CHSI con CV results (736KB)
    ├── chsi_tamesi_1998_2025.csv # Serie temporal del CHSI (316KB, SÍ en git)
    └── validation_report.html   # Validación vs eventos (693KB)
```

---

## 3. Setup en Nueva Estación de Trabajo

### Requisitos
- Python 3.13+
- `uv` package manager (recomendado) o `pip`
- ~500MB de espacio para datos ERA5
- CDS API key configurada en `~/.cdsapirc`

### Pasos

```powershell
# 1. Clonar el repositorio
git clone <REPO_URL> CDS
cd CDS

# 2. Instalar dependencias
uv sync
# O alternativamente:
# pip install -e .

# 3. Configurar CDS API (si se necesitan descargar datos nuevos)
# Crear archivo ~/.cdsapirc con:
# url: https://cds.climate.copernicus.eu/api
# key: <TU_CDS_API_KEY>

# 4. Descargar datos ERA5-Land (SOLO si no tienes los NetCDF)
uv run python era5_land.py

# 5. Preprocesar (indexar a SQLite + crear Zarr)
uv run python preprocess.py

# 6. Ejecutar el servidor
uv run python main.py
# → Abrir http://127.0.0.1:8008

# 7. Regenerar reportes de investigación
uv run python correlation_analysis.py
uv run python ml_pipeline.py
uv run python validation.py
```

### Si ya tienes los datos (transferencia desde otra máquina)

Necesitas copiar estos archivos/carpetas que NO están en git:

```
era5_land_tamaulipas/          # 337 archivos .nc (~480MB)
era5_land_tamaulipas.zarr/     # Store Zarr (~variable)
era5_stats.db                  # SQLite con stats (~155MB)
datasets_manifest.json         # Manifest (~8MB)
```

---

## 4. Descripción Técnica de Cada Módulo

### `correlation_analysis.py`
**Función:** Análisis de correlación multivariante entre t2m, swvl1 y pev.

**Componentes:**
- `load_multivariate_df()` — Carga datos de SQLite y convierte unidades
- `compute_correlation_matrix()` — Pearson/Spearman/Kendall con p-values
- `seasonal_correlation()` — Correlación por estación meteorológica (DJF/MAM/JJA/SON)
- `cross_correlation_with_lag()` — Cross-correlation con lag temporal (±48h por defecto)
- `pca_analysis()` — PCA sobre las 3 variables normalizadas
- `compute_annual_trends()` — Regresión lineal + significancia por variable
- `compute_anomalies()` — Anomalías respecto a climatología mensual
- `generate_correlation_html_report()` — Reporte HTML completo con todos los análisis

**Endpoint API:** `GET /api/correlation-report`

### `ml_pipeline.py`
**Función:** Derivación del Composite Hydric Stress Index (CHSI) via ML.

**Componentes:**
- `engineer_features()` — 23 features derivadas:
  - Ratios físicos (pev/swvl1, t2m/swvl1)
  - Rolling stats (media, std, ventana 7 días)
  - Derivadas temporales (Δ1h, Δ24h)
  - Anomalías mensuales
  - Encoding cíclico (hora, mes, DOY)
- `create_stress_target()` — Target basado en balance hídrico:
  `CHSI = (norm(t2m) + (1 - norm(swvl1)) + norm(|pev|)) / 3`
- `train_chsi_model()` — RF/GBR con TimeSeriesSplit (k=5)
- `generate_chsi_html_report()` — Reporte completo + exportación CSV

**Endpoint API:** `GET /api/chsi-report?model=rf`

**Resultados CV (Random Forest):**

| Fold | Periodo Test          | RMSE   | R²     |
|------|-----------------------|--------|--------|
| 1    | 2002-09 → 2007-05    | 0.0150 | 0.9817 |
| 2    | 2007-05 → 2011-12    | 0.0138 | 0.9876 |
| 3    | 2011-12 → 2016-08    | 0.0107 | 0.9916 |
| 4    | 2016-08 → 2021-03    | 0.0089 | 0.9937 |
| 5    | 2021-03 → 2025-12    | 0.0095 | 0.9937 |

### `validation.py`
**Función:** Validación del CHSI contra eventos extremos documentados.

**Catálogo de eventos (9):**
- 4 sequías: 1998-2003 (multianual), 2011-2012 (excepcional), 2022 (severa), 2024 (excepcional)
- 5 inundaciones: Keith 2000, Jul 2007, Alex 2010, Ingrid 2013, Sept-Oct 2017

**Componentes:**
- `compute_event_statistics()` — Z-score y concordancia direccional por evento
- `compute_binary_classification_metrics()` — AUC-ROC, F1, Precision-Recall
- `plot_chsi_with_events()` — Timeline anotada con eventos
- `plot_event_comparison_boxplot()` — Boxplot eventos vs baseline
- `generate_validation_html_report()` — Reporte HTML completo

**Resultado:** 9/9 concordancia direccional (100%)

**Endpoint API:** `GET /api/validation-report`

---

## 5. Dataset ERA5-Land — Especificaciones

| Campo | Valor |
|-------|-------|
| **Producto** | ERA5-Land (reanalysis-era5-land) |
| **Proveedor** | ECMWF via Copernicus Climate Data Store |
| **Región** | [24°N, -99°W, 22°N, -97°W] (Sur de Tamaulipas) |
| **Periodo** | 1998-01-01 a 2025-12-31 |
| **Resolución temporal** | Horaria |
| **Resolución espacial** | 0.1° × 0.1° (≈9 km) |
| **Grilla** | 21 lat × 21 lon = 441 puntos |
| **Variables** | t2m (K), swvl1 (m³/m³), pev (m) |
| **Timesteps** | ~245,107 |
| **Formato original** | NetCDF4 (337 archivos mensuales) |
| **Formato optimizado** | Zarr v3 (chunks: 1000×21×21) |

---

## 6. Artículo Propuesto

**Título:** *"Machine Learning-Driven Derivation of a Composite Hydric Stress Index from ERA5-Land Reanalysis: A 28-Year Analysis of the Tamesí River Basin, Mexico"*

**Estructura:**

1. **Introduction** — Gap en monitoreo hídrico de la cuenca Tamesí; potencial de reanálisis
2. **Study Area** — Cuenca Guayalejo-Tamesí, características fisiográficas
3. **Data & Methods** — ERA5-Land, preprocesamiento, feature engineering, RF, validación
4. **Results**
   - 4.1 Análisis exploratorio y tendencias (correlation_analysis.py)
   - 4.2 Correlación multivariante a múltiples escalas temporales
   - 4.3 Derivación del CHSI y feature importance
   - 4.4 Validación contra eventos documentados
5. **Discussion** — Implicaciones para inferencia de parámetros no observables
6. **Conclusions** — Utilidad del índice como proxy; contribución a la línea de investigación

**Revistas objetivo:**
- Remote Sensing of Environment (IF ~13.5)
- Journal of Hydrology (IF ~6.4)
- Water Resources Research (IF ~5.4)
- MDPI Remote Sensing (IF ~5.0, open access)

---

## 7. Dependencias del Proyecto

```toml
# pyproject.toml
[project]
requires-python = ">=3.13"
dependencies = [
    "fastapi>=0.136.0",
    "jinja2>=3.1.6",
    "matplotlib>=3.10.8",
    "netcdf4>=1.7.4",
    "numpy>=2.4.4",
    "pandas>=3.0.2",
    "seaborn>=0.13.2",
    "uvicorn>=0.44.0",
    "xarray>=2026.4.0",
    "cdsapi>=0.7.3",
    "dask>=2025.2.0",
    "zarr>=3.0.1",
    "scipy>=1.17.1",
    "fpdf2>=2.8.7",
    # Módulos CHSI (ya incluidos en scikit-learn):
    "scikit-learn",  # RF, GBR, PCA, StandardScaler, metrics
]
```

> **Nota:** scikit-learn ya está instalado como dependencia transitiva pero debe
> agregarse explícitamente al pyproject.toml para garantizar reproducibilidad.

---

## 8. Contexto de la Investigación Principal

La línea de investigación doctoral busca demostrar que **parámetros hídricos no observables directamente** (ej. estrés hídrico integrado, evapotranspiración real, recarga de acuíferos) pueden ser **inferidos y cuantificados** mediante la combinación de:

1. **Teledetección** (satélites ópticos/radar: Sentinel-2, MODIS, SAR)
2. **Reanálisis climático** (ERA5-Land — este proyecto)
3. **Inteligencia Artificial** (ML/DL para aprender las relaciones no lineales)

El artículo del CHSI es un **proof of concept lateral**: demuestra que 3 variables observables de reanálisis pueden capturar la dinámica de un parámetro compuesto no medible directamente, validado contra eventos reales. Este resultado fundamenta la escalabilidad del enfoque cuando se integren datos de teledetección de mayor resolución espacial.
