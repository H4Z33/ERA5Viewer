---
name: nautai-step-draft
description: Paso 3: Redactar prosa académica doctoral directamente del evidence
triggers: ["nautai draft", "redactar", "academic prose", "thesis writing", "scholarly drafting", "escribir capitulo"]
---

# NautAI-Step: Draft — Academic Writing from Evidence

## Purpose
Redactar el capítulo completo en prosa académica doctoral española, directamente desde la evidencia estructurada. Sin traducción. Sin resumen genérico. Sin filler.

## Input
- `capX_structured.json` — evidencia por sección
- `naut_consolidated.json` — átomos originales
- `papers_metadata.json` — metadata APA 7

## Output
- `tesis_ami/Capitulo_X_vN.md` — capítulo en markdown académico

## Execution
Redactar directamente con el modelo, alimentando la evidencia estructurada como contexto.

## Writing Rules

### Epistemic Regime (R0/R1/R2)
- **R0** (mechanism/definiton, conf ≥ 0.50): "X constituye...", "Y opera a través de..." Declarativo.
- **R1** (finding, conf ≥ 0.40): "Los resultados indican que...", "Bajo condiciones controladas..." Condicional.
- **R2** (claim/observation, conf < 0.40): "La evidencia sugiere que...", "Una posible explicación es..." Cualificado.

### Forbidden Patterns (¡NUNCA!)
- Em dashes (—) — usar coma, punto o "sin embargo"
- Relleno académico genérico
- Transiciones artificiales ("En este sentido...", "En cuanto a lo anterior...")
- Resúmenes vagos de literatura ("La literatura ha mostrado que...")
- Simetría sintáctica repetitiva
- Certidumbre sintética ("Está demostrado que...")
- Frases como "studies show mixed results" sin mapear el conflicto
- Capítulos de discusión descriptiva disfrazados de análisis
- Anglicismos no adaptados ("influencer", "selfie", "branding" — adaptar o usar cursiva + equivalencia)

### APA 7 Rules
- Citas en texto: `(Autor, Año)` narrativas y parentéticas
- Referencias al final con DOI completos en `doi.org/` cuando existan
- Encabezados jerárquicos: 2.1, 2.1.1, 2.2...
- Sangría francesa en referencias
- Tablas numeradas: "Tabla 1. Título"
- Figuras numeradas: "Figura 1. Título"

### Direct Academic Spanish
NO se traduce del inglés. El modelo piensa directamente en español académico.
- "parasocial relationship" → "relación parasocial" (definir al primer uso)
- "social comparison" → "comparación social" (definir al primer uso)
- "body image" → "imagen corporal" (definir al primer uso)
- "influencer" → "creador de contenido" o "figura de influencia"

## Every Sentence Must Justify Its Existence
Cada oración debe hacer al menos una de estas cosas:
- Definir
- Distinguir
- Justificar
- Delimitar
- Comparar
- Sintetizar
- Desafiar
- Interpretar
- Cualificar
- Refutar
- Establecer límites de causalidad
- Exponer contradicción
- Defender decisiones metodológicas

Si una oración no hace nada de esto, se elimina.

# RULES
1. ALL forbidden patterns listed above are hard failures — zero tolerance.
2. Apply the correct epistemic regime (R0/R1/R2) based on atom_type and confidence.
3. Write directly in academic Spanish — do NOT translate from English.
4. Every sentence must perform at least one analytical function from the justification list.
5. Contradictions between studies must be exposed as analytical objects, never averaged.

# REQUIRED TOOLS
- use_skill (for loading nautai-step-validate after drafting)
- read_file (for reading structured evidence JSON)
- write_file (for writing the chapter markdown)

# VALIDATION
Before completing this work, you MUST verify:
- No em dashes (—) appear in the output
- No forbidden patterns (generic filler, artificial transitions) are present
- All citations use APA 7 format (narrative and parenthetical)
- The epistemic regime is correctly applied to each claim
- Every paragraph has at least one citation
