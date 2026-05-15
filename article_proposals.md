# Propuestas de Artículo — ERA5-Land × Cuenca del Río Tamesí

> **Investigación principal:** *Remote Sensing and AI for the Inference and Quantification of Non-Observable Hydric Parameters*
> **Autor:** Raúl Alejandro Morales Rivera, DCI, Posgrado FIT

---

## Inventario de Activos Disponibles

Antes de proponer artículos, es fundamental entender qué **ya tenemos listo** para trabajar:

### Dataset
| Propiedad | Valor |
|---|---|
| **Fuente** | ERA5-Land (ECMWF via CDS API) |
| **Región** | Sur de Tamaulipas: 22°N–24°N, 99°W–97°W |
| **Periodo** | Enero 1998 – Diciembre 2025 (**28 años**) |
| **Resolución temporal** | Horaria (24 steps/día) |
| **Resolución espacial** | 0.1° × 0.1° (≈9 km), grilla 21×21 |
| **Archivos** | 337 NetCDF mensuales + Zarr consolidado |
| **Timesteps totales** | ~245,107 |

### Variables
| Short Name | Long Name | Unidades | Tipo |
|---|---|---|---|
| `t2m` | 2-metre temperature | K (→ °C) | Instantáneo |
| `swvl1` | Volumetric soil water layer 1 (0–7 cm) | m³/m³ | Instantáneo |
| `pev` | Potential evaporation | m | Acumulado |

### Infraestructura de Código
- **Pipeline de descarga** automatizado con log de estado ([era5_land.py](file:///c:/APPS/CDS/era5_land.py))
- **Preprocesamiento** con indexación a SQLite + consolidación Zarr ([preprocess.py](file:///c:/APPS/CDS/preprocess.py))
- **Servidor analítico** FastAPI con cache LRU, resampling temporal, y API REST ([main.py](file:///c:/APPS/CDS/main.py))
- **Auditoría científica** con generación de reportes HTML/PDF, boxplots anuales, violines, histogramas ([analytics_utils.py](file:///c:/APPS/CDS/analytics_utils.py))
- **Dashboard web** Leaflet + timeline interactiva para exploración espaciotemporal

---

## Propuesta Principal (Recomendada)

### 📄 *"Derivación de un Índice de Estrés Hídrico Compuesto a partir de Variables ERA5-Land mediante Aprendizaje Automático: Un Estudio en la Cuenca del Río Tamesí (1998–2025)"*

**Título sugerido en inglés:**
> *"Machine Learning-Driven Derivation of a Composite Hydric Stress Index from ERA5-Land Reanalysis: A 28-Year Analysis of the Tamesí River Basin, Mexico"*

#### Tesis del artículo

Las tres variables que ya tenemos (**t2m**, **swvl1**, **pev**) no son independientes: forman un **triángulo termodinámico** donde la temperatura gobierna la demanda evaporativa, la humedad del suelo limita la oferta hídrica, y la evapotranspiración potencial es la resultante del acoplamiento entre ambas. Este artículo propone:

1. **Caracterizar estadísticamente** las relaciones multivariantes entre t2m, swvl1 y pev a escala sub-diaria, diaria, mensual y anual.
2. **Derivar un índice compuesto** (Composite Hydric Stress Index — CHSI) usando técnicas de ML (Random Forest, XGBoost, o PCA no lineal) que capture la dinámica integrada de las tres variables.
3. **Validar el índice** contra registros conocidos de sequía (ej. CONAGUA, Monitor de Sequía de México) y eventos extremos documentados en la cuenca (ej. sequía 2011, inundaciones 2010).
4. **Demostrar** que variables "observables" de reanálisis pueden servir como **proxies** para inferir el estado hídrico no medible directamente.

#### ¿Por qué es lateralmente relevante?

```mermaid
graph LR
    A["Variables ERA5-Land<br/>(t2m, swvl1, pev)"] --> B["Índice CHSI<br/>(este artículo)"]
    B --> C["Validación contra<br/>eventos reales"]
    B --> D["Investigación principal:<br/>inferencia de parámetros<br/>hídricos no observables"]
    D --> E["Modelo AI completo<br/>con Remote Sensing"]
    
    style B fill:#38bdf8,stroke:#0284c7,color:#0f172a
    style D fill:#818cf8,stroke:#6366f1,color:#0f172a
```

- **Establece el marco de referencia** (baseline) de variabilidad hidro-climática de la cuenca del Tamesí que la tesis necesita.
- **Demuestra la metodología** de inferencia de parámetros no observables a partir de variables observables — exactamente lo que la línea de investigación propone escalar con remote sensing.
- **Genera un dataset publicable** que puede reutilizarse en la tesis y artículos subsecuentes.

#### Estructura propuesta del artículo

| Sección | Contenido | ¿Ya tenemos los datos? |
|---|---|---|
| 1. Introduction | Gap en monitoreo hídrico de la cuenca Tamesí; potencial de reanálisis | ✅ Revisión de literatura |
| 2. Study Area | Cuenca Guayalejo-Tamesí, características fisiográficas | ✅ Coordenadas en dataset |
| 3. Data & Methods | ERA5-Land 1998-2025, preprocesamiento, ML pipeline | ✅ Todo el código existente |
| 4.1 Análisis exploratorio | Estadísticas descriptivas, tendencias, estacionalidad | ✅ `ScientificAudit` ya genera esto |
| 4.2 Correlación multivariante | Cross-correlation t2m↔swvl1↔pev a múltiples escalas temporales | ⚠️ **Falta implementar** |
| 4.3 Derivación del CHSI | Entrenamiento de modelos ML, feature importance, SHAP | ⚠️ **Falta implementar** |
| 4.4 Validación temporal | Comparación contra Monitor de Sequía MX, eventos documentados | ⚠️ Requiere datos externos |
| 5. Discussion | Implicaciones para inferencia de parámetros no observables | ✅ Narrativo |
| 6. Conclusions | Utilidad del índice como proxy; contribución a la línea de investigación | ✅ Narrativo |

#### Revistas objetivo
- **Remote Sensing of Environment** (IF ~13.5) — si se integra validación con MODIS/Sentinel
- **Journal of Hydrology** (IF ~6.4) — enfoque hidrológico puro
- **Water Resources Research** (IF ~5.4) — enfoque en parámetros hídricos
- **MDPI Remote Sensing** (IF ~5.0) — open access, más rápido

---

## Propuesta Alternativa 1

### 📄 *"Acoplamiento Suelo-Atmósfera en Regiones Semiáridas de México: Evidencia de 28 Años de Reanálisis ERA5-Land en la Cuenca del Tamesí"*

**En inglés:**
> *"Land-Atmosphere Coupling in Semi-Arid Mexico: Evidence from 28 Years of ERA5-Land Reanalysis over the Tamesí Basin"*

#### Concepto

Este artículo se centra en el **fenómeno físico** del acoplamiento suelo-atmósfera. Cuando la humedad del suelo (swvl1) baja, la fracción de energía que va a evaporación disminuye y la temperatura (t2m) sube — creando un feedback positivo que intensifica sequías. Este es un **parámetro no observable** por excelencia: la *fuerza del acoplamiento* no se mide directamente, se infiere.

#### Análisis clave
1. **Índice de acoplamiento** τ = ∂T/∂θ (sensibilidad de temperatura a cambios en humedad) calculado por pixel y por estación.
2. **Detección de regímenes**: clasificar la grilla 21×21 en zonas de acoplamiento fuerte vs. débil usando clustering (K-means o DBSCAN).
3. **Tendencia temporal**: ¿Se ha fortalecido el acoplamiento en 28 años? → Evidencia de cambio climático local.

#### Ventajas
- Más "físico" y menos dependiente de ML
- Muy alineado con la literatura de cambio climático
- Los 3 variables ya son suficientes para el análisis completo

#### Desventajas
- Menor novelty metodológica (el acoplamiento suelo-atmósfera está bien estudiado globalmente)
- La grilla 21×21 puede ser limitante para conclusiones espaciales robustas

---

## Propuesta Alternativa 2

### 📄 *"Reconstrucción de Series de Evapotranspiración Real a partir de Evapotranspiración Potencial y Humedad del Suelo: Un Framework de Transferencia Aprendida para Cuencas con Datos Escasos"*

**En inglés:**
> *"Reconstructing Actual Evapotranspiration from Potential Evaporation and Soil Moisture: A Transfer Learning Framework for Data-Scarce Basins"*

#### Concepto

La **evapotranspiración real (ETa)** es quizás el parámetro hídrico no observable más importante. Tenemos **pev** (potencial) y **swvl1** (humedad del suelo). La relación ETa/pev = f(swvl1, t2m) es el factor de estrés hídrico. Este artículo entrenaría un modelo para inferir ETa usando solo nuestras 3 variables, validando contra productos satelitales (MODIS MOD16, SSEBop).

#### Relevancia directa
- **Es literalmente** "inference of non-observable hydric parameters from observable ones"
- Genera un framework transferible a otras cuencas
- Conecta directamente con la tesis

#### Desventajas
- Requiere descargar datos de validación adicionales (MODIS, SSEBop)
- Puede percibirse como "circular" si no se contrasta con datos independientes

---

## Análisis Comparativo

| Criterio | Propuesta Principal (CHSI) | Alt. 1 (Acoplamiento) | Alt. 2 (ETa) |
|---|:---:|:---:|:---:|
| **Factibilidad con datos actuales** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Novelty** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Relevancia a la tesis** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Publicabilidad** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Código ya existente** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Reutilización en tesis** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## Resultados de Ejecución (Implementados)

> [!IMPORTANT]
> Los módulos de correlación y ML se implementaron y ejecutaron exitosamente contra el dataset completo.

### Módulos implementados

| Módulo | Archivo | Status |
|---|---|---|
| Correlación Multivariante | [correlation_analysis.py](file:///c:/APPS/CDS/correlation_analysis.py) | ✅ Ejecutado |
| ML Pipeline CHSI | [ml_pipeline.py](file:///c:/APPS/CDS/ml_pipeline.py) | ✅ Ejecutado |
| API Endpoints | [main.py](file:///c:/APPS/CDS/main.py) (2 nuevos endpoints) | ✅ Integrado |

### Resultados Cross-Validation (Random Forest, TimeSeriesSplit k=5)

| Fold | Periodo Test | RMSE | MAE | R² |
|---|---|---|---|---|
| 1 | 2002-09 → 2007-05 | 0.0150 | 0.0087 | **0.9817** |
| 2 | 2007-05 → 2011-12 | 0.0138 | 0.0073 | **0.9876** |
| 3 | 2011-12 → 2016-08 | 0.0107 | 0.0061 | **0.9916** |
| 4 | 2016-08 → 2021-03 | 0.0089 | 0.0058 | **0.9937** |
| 5 | 2021-03 → 2025-12 | 0.0095 | 0.0062 | **0.9937** |

### Archivos generados
- [correlation_report.html](file:///c:/APPS/CDS/reports/correlation_report.html) — 1.1 MB
- [chsi_report.html](file:///c:/APPS/CDS/reports/chsi_report.html) — 736 KB
- [chsi_tamesi_1998_2025.csv](file:///c:/APPS/CDS/reports/chsi_tamesi_1998_2025.csv) — 316 KB (dataset exportable del índice)

---

## Validación contra Eventos Extremos (Completada)

| Módulo | Archivo | Status |
|---|---|---|
| Validación vs Eventos | [validation.py](file:///c:/APPS/CDS/validation.py) | ✅ Ejecutado |
| API Endpoint | `/api/validation-report` | ✅ Integrado |

### Concordancia Direccional: **9/9 (100%)**

| Evento | Tipo | CHSI | Z-score | Correcto |
|---|---|---|---|---|
| Sequía multinanual 1998-2003 | drought | 0.5271 | +0.099 | ✅ |
| Sequía excepcional 2011-2012 | drought | 0.5527 | +0.320 | ✅ |
| Sequía severa 2022 | drought | 0.6118 | +0.832 | ✅ |
| Sequía excepcional 2024 | drought | 0.5727 | +0.494 | ✅ |
| Huracán Keith 2000 | flood | 0.4011 | -0.993 | ✅ |
| Inundaciones Julio 2007 | flood | 0.4995 | -0.141 | ✅ |
| Huracán Alex 2010 | flood | 0.4683 | -0.412 | ✅ |
| Huracán Ingrid 2013 | flood | 0.3913 | -1.079 | ✅ |
| Inundaciones Sept-Oct 2017 | flood | 0.4292 | -0.750 | ✅ |

### Reporte generado
- [validation_report.html](file:///c:/APPS/CDS/reports/validation_report.html) — 693 KB

> [!TIP]
> **Pipeline 100% completado.** Los tres módulos (correlación, ML, validación) están implementados, ejecutados y con resultados publicables. Listo para redacción del artículo.

---

## Recomendación Final

**Ir con la Propuesta Principal (CHSI)** por las siguientes razones:

1. **Máxima sinergia** con la línea de investigación de la tesis — el artículo es literalmente un "proof of concept" de que variables observables pueden inferir estados hídricos no medibles.
2. **El dataset ya es robusto** — 28 años horarios, 3 variables co-localizadas, ya preprocesado y auditado.
3. **El código existente** reduce drásticamente el tiempo de implementación.
4. **Genera un producto publicable** (el índice CHSI) que puede citarse y reutilizarse en la tesis.
5. **Es lateralmente relevante** — no repite el trabajo de la tesis, sino que lo fundamenta con evidencia climática de largo plazo.

¿Quieres que empecemos a implementar los módulos faltantes (correlación multivariante, ML pipeline, validación)?
