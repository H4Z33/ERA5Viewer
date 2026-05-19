---
name: nautai-step-consolidate
description: Paso 1: Consolidar KG de NautAI en átomos temáticos
triggers: ["nautai consolidate", "consolidate_naut", "naut_all_results", "KG consolidation"]
---

# NautAI-Step: Consolidate — KG a Thematic Evidence

## Purpose
Consolidar los resultados crudos de NautAI (`naut_all_results.json`) en un archivo temático estructurado por categorías (`naut_consolidated.json`).

## Input
- `naut_all_results.json` — resultados crudos de la consulta a NautAI (655 papers)
- `papers_metadata.json` — metadata bibliográfica de cada paper

## Output
- `naut_consolidated.json` — dict por categoría, cada átomo con: `atom_type`, `validated_confidence`, `concept`, `predicate`, `object_value`, `paper_id`, `score`

## Execution
```bash
python consolidate_naut.py
```

## QA Checks
1. Cada categoría tiene átomos únicos (deduplicar por `paper_id + predicate + object_value`)
2. Los `atom_type` son: `mechanism | finding | observation | claim | definition`
3. `validated_confidence` está normalizado 0–1
4. `contradictions` se marca explícitamente cuando dos papers dicen lo opuesto

## Critical Rule
- **No traducir del inglés.** Los átomos se mantienen en el idioma original de la fuente.
- La escritura académica se hará después, en español directo.

# RULES
1. Atoms MUST remain in their original source language — no translation at this stage.
2. Deduplicate atoms by `paper_id + predicate + object_value`.
3. `atom_type` must be one of: `mechanism | finding | observation | claim | definition`.
4. `validated_confidence` must be normalized to 0–1 range.
5. Contradictions between papers MUST be explicitly marked.

# REQUIRED TOOLS
- bash (for running consolidate_naut.py)
- read_file (for inspecting input JSON)

# VALIDATION
Before completing this work, you MUST verify:
- Output file `naut_consolidated.json` exists and is valid JSON
- No duplicate atoms exist (by the deduplication key)
- All `atom_type` values are in the allowed set
- All `validated_confidence` values are in [0, 1]
