# CHSI × Cuenca del Río Tamesí — ERA5-Land Reanalysis & Machine Learning

Este repositorio contiene la línea de investigación sobre la inferencia y cuantificación de parámetros hídricos no observables directamente, aplicada a la Cuenca del Río Guayalejo-Tamesí (sur de Tamaulipas, México) utilizando datos del reanálisis climático ERA5-Land (1998–2025) y modelos de aprendizaje automático.

---

## Estructura del Repositorio

*   `era5_land.py`: Script para descargar datos horariales de ERA5-Land (t2m, swvl1, pev) desde Copernicus CDS API.
*   `preprocess.py`: Procesa los archivos NetCDF mensuales consolidándolos en una base de datos SQLite (`era5_stats.db`) y en un store optimizado Zarr.
*   `correlation_analysis.py`: Ejecuta análisis estadístico multivariante de correlación estacional, cross-correlation con desfase (lag), PCA y tendencias de Mann-Kendall.
*   `ml_pipeline.py`: Entrena un regresor Random Forest con validación cruzada temporal ($k=5$) sobre 23 variables sintéticas (features) para derivar el **Composite Hydric Stress Index (CHSI)**.
*   `validation.py`: Valida la serie temporal del CHSI contrastándola contra 9 eventos extremos documentados (4 sequías y 5 inundaciones/huracanes).
*   `main.py`: Servidor API en FastAPI para exponer los datos y servir los reportes interactivos del dashboard.
*   `article_proposals.md`: Documento de propuesta científica y plan de redacción para revistas Q1.
*   `article_draft.md`: **[NUEVO] Borrador completo del artículo científico** en inglés técnico estructurado para revistas científicas, que integra los datos exactos del análisis actual.
*   `RESEARCH_CONTINUITY.md`: Guía metodológica para la continuación del proyecto en nuevas estaciones de trabajo.

---

## Resultados Clave Obtenidos

1.  **Modelo de Aprendizaje Automático**:
    *   Regresión Random Forest entrenada sobre 23 features físicas.
    *   Desempeño en validación cruzada temporal: R² promedio de **0.9897** y RMSE promedio de **0.0116**.
    *   La serie del índice CHSI diaria se exportó exitosamente en `reports/chsi_tamesi_1998_2025.csv`.
2.  **Validación de Consistencia Física**:
    *   Concordancia direccional del **100% (9 de 9 eventos documentados)**.
    *   Desviaciones significativas coherentes: las sequías excepcionales (2022 y 2024) registran Z-scores muy elevados ($+0.832$ y $+0.494$), mientras que las inundaciones y huracanes extremos (como Ingrid 2013) registran Z-scores marcadamente negativos ($-1.079$).
3.  **Tendencias Climáticas (1998–2025)**:
    *   Warming local significativo: calentamiento de **$+0.0387\ ^\circ\text{C}/\text{año}$** ($p = 0.0032$), equivalente a $+1.08\ ^\circ\text{C}$ acumulados en el periodo de 28 años.
    *   Incremento en la evaporación potencial ($pev$) de magnitud significativa ($p = 0.0350$).

---

## Reportes Generados (`/reports`)

Los siguientes reportes HTML científicos y conjuntos de datos fueron generados exitosamente por los scripts:

*   [`reports/correlation_report.html`](reports/correlation_report.html): Matrices de correlación multiescala, correlaciones estacionales, cross-correlation con desfase horarial, biplots de PCA y análisis de tendencias.
*   [`reports/chsi_report.html`](reports/chsi_report.html): Resultados de entrenamiento de Random Forest, importancia de variables y series temporales reconstruidas de CHSI.
*   [`reports/validation_report.html`](reports/validation_report.html): Línea del tiempo interactiva de eventos extremos vs. CHSI, boxplots comparativos y métricas de desempeño de clasificación.
*   [`reports/chsi_tamesi_1998_2025.csv`](reports/chsi_tamesi_1998_2025.csv): Dataset consolidado diario del CHSI generado por la investigación.

---

## Ejecución del Proyecto

Asegúrese de contar con Python 3.13 e instale las dependencias del proyecto usando `uv`:

```powershell
# Sincronizar el entorno virtual local
uv sync

# Regenerar todos los análisis y reportes científicos
uv run python correlation_analysis.py
uv run python ml_pipeline.py
uv run python validation.py

# Levantar el servidor FastAPI del Dashboard
uv run python main.py
# -> Abrir en http://127.0.0.1:8008
```
