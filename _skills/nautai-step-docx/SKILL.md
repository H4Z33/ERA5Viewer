---
name: nautai-step-docx
description: Paso 4: Construir DOCX final desde markdown
triggers: ["nautai docx", "generate_cap", "DOCX", "build_cap", "thesis docx", "convertir markdown"]
---

# NautAI-Step: DOCX — Build Final Thesis Chapter

## Purpose
Convertir el markdown del capítulo (`tesis_ami/Capitulo_X_vN.md`) en un DOCX formal con formato APA 7, usando las herramientas de `docx_tools/` o `thesis_docx/`.

## Tools

### Option A: Node.js (`docx-tools/`)
```bash
node docx_tools/generate_capX.js
```

### Option B: Python (`thesis_docx/framework.py`)
```python
from thesis_docx.framework import ThesisDoc, heading1, heading2, body, bullet, para, table, Figure
from thesis_docx.charts import bar_chart, seaborn_bar, pie_chart, seaborn_boxplot, seaborn_heatmap

doc = ThesisDoc()
doc.title("Capítulo II. Marco Teórico")
doc.add(heading1("2.1 Teoría de las Relaciones Parasociales"))
doc.add(body("Párrafo académico..."))
doc.add(bullet("Elemento de lista"))
doc.add(table(headers, rows, caption="Distribución de la muestra"))
doc.add(Figure(fig, ax, caption="Correlaciones entre variables"))
doc.save("tesis_ami/Capitulo_II.docx")
```

## Features Available

### Lists
```python
bullet("Texto del ítem")   # viñeta
numbered("Texto", start=1)  # numerada
```

### Tables
```python
make_table(headers, rows, col_widths=None, caption="Título de tabla")
```

### Figures (matplotlib / seaborn)
```python
bar_chart(labels, values, title="", xlabel="", ylabel="")
seaborn_bar(labels, values, title="", palette="Blues_d")
horizontal_bar(labels, values, title="")
pie_chart(labels, values, title="", colors=None)
seaborn_boxplot(data_dict, title="")
seaborn_heatmap(correlation_matrix, title="", cmap="YlOrRd")
```

### SVG (vector, embebido)
```python
svg_figure("path/to/file.svg", caption="Título", width=Inches(5.5))
```

## APA 7 Formatting
- Fuente: Times New Roman 12pt
- Márgenes: 1 pulgada
- Interlineado: 1.15 (doble espacio según norma APA 7 — verificar con institución)
- Encabezados: bold, jerárquicos
- Sangría francesa en referencias
- Tabla: título en cursiva encima, notas debajo
- Figura: numeral y título centrado debajo

## QA Checks
1. El DOCX se abre sin errores en Word
2. Los heading levels son correctos (1, 2, 3)
3. Las referencias tienen sangría francesa
4. Tablas y figuras tienen numeración y leyendas
5. No hay caracteres rotos (ñ, acentos)

# RULES
1. All headings must use correct APA 7 hierarchy (level 1, 2, 3).
2. References section MUST use hanging indent (sangría francesa).
3. Tables and figures MUST have numbered captions and legends.
4. Font must be Times New Roman 12pt, margins 1 inch.
5. No broken characters (ñ, accents must render correctly).

# REQUIRED TOOLS
- bash (for running docx generation scripts)
- write_file (for writing intermediate markdown if needed)

# VALIDATION
Before completing this work, you MUST verify:
- The output .docx file opens without errors
- Heading levels are correct (1, 2, 3)
- References have hanging indent
- Tables and figures have complete captions
- No broken/garbled characters in the output
