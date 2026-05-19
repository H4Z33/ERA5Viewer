---
name: nautai-thesis-pipeline
description: Pipeline doctoral completo: consolidar KG → estructurar → redactar → DOCX → validar
triggers: ["nautai thesis pipeline", "nautai-thesis-pipeline", "pipeline doctoral", "generar capitulo tesis", "nautai kapitel", "thesis chapter pipeline"]
---

# NautAI Doctoral Thesis Pipeline (APA 7)
## Per-Chapter-Step Instructions

Pipeline doctoral para generar capítulos de tesis en español usando NautAI KG y evidencia estructurada APA 7.

---

## Paso 0 — Inventario (ANTES de redactar)

Antes de empezar, leer el capítulo anterior existente:
```python
# Extraer texto del DOCX anterior
import zipfile, re, os
with zipfile.ZipFile('tesis_ami/Capitulo_II_Marco_Teorico.docx') as z:
    with z.open('word/document.xml') as f:
        texts = re.findall(r'<w:t[^>]*>([^<]+)</w:t>', f.read().decode('utf-8'))
# Escribir en archivo para revisión
with open('cap2_original_text.txt','w',encoding='utf-8') as f:
    f.write('\n'.join(texts))
```
Revisar: estructura, teorías usadas, citas reales, estilo, gaps,anglicismos.

---

## Paso 1 — Consolidate (KG → Átomos Temáticos)

**Trigger:** `nautai consolidate`, `naut_all_results`, `consolidate_naut`

**Ejecutar:**
```bash
python consolidate_naut.py
```

**Input:** `naut_all_results.json` (655 papers) + `papers_metadata.json`
**Output:** `naut_consolidated.json` — dict por categoría

**QA:**
- Deduplicar por `paper_id + predicate + object_value`
- `atom_type` en: `mechanism | finding | observation | claim | definition`
- `validated_confidence` normalizado 0–1
- `contradictions` marcado explícitamente
- **No traducir** — átomos en idioma original de la fuente

---

## Paso 2 — Structure (Átomos → Secciones del Capítulo)

**Trigger:** `nautai structure`, `build_cap`, `estructurar evidencia`

**Ejecutar:**
```bash
python build_capX_structured.py
```

**Input:** `naut_consolidated.json` + `papers_metadata.json`
**Output:** `capX_structured.json`

**Reglas:**
- Mínimo 3, máximo 8 átomos por sección
- Orden: R0 → R1 → R2
- `contradiction_map`: listar conflictos explícitamente
- Cada `paper_id` debe tener cita en texto y en referencias

---

## Paso 3 — Draft (Escritura Académica)

**Trigger:** `nautai draft`, `redactar`, `academic prose`, `escribir capitulo`

**EJECUTAR: Usar los skills individuales:**
```bash
# Skill: cargar nautai-step-draft
```

**Reglas de Escritura (CRÍTICAS):**

### Régimen Epistémico (R0/R1/R2)
- **R0** (mechanism/definition, conf ≥ 0.50): Declarativo. "X constituye...", "Y opera a través de..."
- **R1** (finding, conf ≥ 0.40): Condicional. "Los resultados indican que...", "Bajo condiciones controladas..."
- **R2** (claim/observation, conf < 0.40): Cualificado. "La evidencia sugiere que...", "Una posible explicación es..."

### PATTERNS PROHIBIDOS ( ¡NUNCA! )
- **Em dashes (—)** → usar coma, punto o "sin embargo"
- Relleno académico genérico
- Transiciones artificiales: "En este sentido...", "En cuanto a lo anterior..."
- Resúmenes vagos: "La literatura ha mostrado que..."
- Simetría sintáctica repetitiva
- Certidumbre sintética: "Está demostrado que..."
- "Estudios muestran resultados mixtos" sin mapear conflicto específico
- Capítulos de discusión descriptiva disfrazados de análisis
- Anglicismos no adaptados

### Anglicismos — Cómo Manejarlos
| Anglicismo | Solución |
|---|---|
| influencer | "creador de contenido" (definir al primer uso) |
| social media | "redes sociales" |
| self-esteem | "autoestima" (ya integrado al español) |
| body image | "imagen corporal" |
| social comparison | "comparación social" |
| parasocial relationship | "relación parasocial" (definir al primer uso) |
| social media use | "uso de redes sociales" |
| content creator | "creador de contenido" |

### Cada Oración Debe Justificar Su Existencia
Debe hacer al menos una de: definir, distinguir, justificar, delimitar, comparar, sintetizar, desafiar, interpretar, cualificar, refutar, establecer causalidad, exponer contradicción, defender método.

---

## Paso 4 — DOCX (Markdown → DOCX Formateado)

**Trigger:** `nautai docx`, `generate_cap`, `DOCX`, `convertir markdown`

**EJECUTAR:** Usar skill `nautai-step-docx`

```python
# Option A: Python thesis_docx/framework.py
from thesis_docx.framework import (
    ThesisDoc, heading1, heading2, body, bullet,
    para, table, make_table, figure, bar_chart,
    seaborn_bar, pie_chart, seaborn_boxplot, seaborn_heatmap
)

doc = ThesisDoc()
doc.title("Capítulo II. Marco Teórico")
doc.add(heading1("2.1 Teoría de las Relaciones Parasociales"))
doc.add(body("Párrafo académico..."))
doc.add(bullet("Viñeta 1"))
doc.add(bullet("Viñeta 2"))
doc.add(table(headers, rows, caption="Título de tabla"))
doc.save("tesis_ami/Capitulo_II_v2.docx")

# Option B: Node.js docx-tools
node docx_tools/generate_cap2.js
```

**Features disponibles:**
- Listas (viñetas, numeradas)
- Tablas con captions APA 7
- Figuras matplotlib/seaborn embebidas
- SVG vector embebido
- Sangría francesa en referencias

---

## Paso 5 — Validate (Revisión Crítica Obligatoria)

**Trigger:** `nautai validate`, `validar capitulo`, `revisar capitulo`

**EJECUTAR:** Usar skill `nautai-step-validate`

### Checklist de Revisión
- [ ] Consistencia conceptual (variables definidas)
- [ ] Cada afirmación fáctica tiene cita
- [ ] Citas corresponden a referencias reales
- [ ] Contradicciones entre estudios surfacen explícitamente
- [ ] NO "resultados mixtos" sin mapear conflicto
- [ ] Decisiones metodológicas justificadas
- [ ] Estructura jerárquica correcta (2.1 → 2.1.1 → 2.2...)
- [ ] **NO em dashes** (corregir a comas/sin embargo)
- [ ] **NO transiciones artificiales**
- [ ] **NO anglicismos sin adaptar**
- [ ] APA 7: citas narrativas/parentéticas correctas
- [ ] Sangría francesa en referencias
- [ ] Tablas/figuras numeradas y con leyenda

**Output:** Lista de issues → capítulo corregido → validación confirmada

---

## Evidence Semantics

| atom_type | Significado |
|---|---|
| mechanism | Proceso causal o sistema explicativo |
| finding | Resultado empírico de estudio |
| observation | Patrón reportado que requiere interpretación |
| claim | Proposición interpretativa que requiere cualificación |
| definition | Límite conceptual formal |

## Conflict Rule (CRÍTICO)
Cuando dos estudios se contradicen, **nunca promediar**. Exponer el conflicto como objeto analítico:
- Qué estudió cada uno
- En qué contexto
- Por qué difieren
- Qué implica para la investigación actual

---

## Formato APA 7 (recordatorio)
- Fuente: Times New Roman 12pt
- Márgenes: 1 pulgada
- Interlineado: 1.15
- Citas en texto: `(Autor, Año)` narrativas y parentéticas
- Referencias: sangría francesa
- Tablas: título en cursiva encima, notas debajo
- Figuras: numeral + título centrado debajo

# RULES
1. Execute steps in order: Consolidate → Structure → Draft → DOCX → Validate. Never skip a step.
2. Each step must complete successfully before moving to the next — check outputs exist.
3. ALL forbidden patterns from the Draft step are hard failures at any stage.
4. Contradictions between studies must NEVER be averaged — expose as analytical objects.
5. Atoms must remain in their original language during Consolidation; academic Spanish is written from scratch in Draft.
6. Always load the individual step skill (nautai-step-*) for detailed instructions.

# REQUIRED TOOLS
- use_skill (for loading individual nautai-step-* skills)
- bash (for running Python/Node scripts)
- read_file / write_file (for inspecting and producing artifacts)

# VALIDATION
Before completing this work, you MUST verify:
- Step outputs exist: naut_consolidated.json, capX_structured.json, Capitulo_X_vN.md, Capitulo_X.docx
- The Validate step was executed and produced a PASSED/issues report
- No forbidden patterns remain in the final output
- All citations are traceable to real sources
