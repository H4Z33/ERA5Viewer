---
name: nautai-step-structure
description: Paso 2: Estructurar evidencia en secciones de capítulo
triggers: ["nautai structure", "build_cap", "estructurar evidencia", "chapter sections"]
---

# NautAI-Step: Structure — Evidence to Chapter Sections

## Purpose
Asignar cada átomo de `naut_consolidated.json` a una sección específica del capítulo de tesis, generando `capX_structured.json` con evidencia pre-agrupada por tema.

## Input
- `naut_consolidated.json` — átomos temáticos (del paso de consolidación)
- `papers_metadata.json` — metadata bibliográfica

## Output
- `capX_structured.json` — dict por sección, cada entrada con: `atoms[]`, `citation_keys[]`, `theories[]`, `contradiction_map`

## Execution
```bash
python build_capX_structured.py
```

## Rules
- Cada sección tiene mínimo 3 y máximo 8 átomos
- Los átomos se ordenan: R0 → R1 → R2
- `contradiction_map` lista explícitamente conflictos entre estudios
- No se inventan transiciones — la coherencia viene de la estructura teórica

# RULES
1. Each section must have minimum 3 and maximum 8 atoms.
2. Atoms must be ordered: R0 → R1 → R2.
3. `contradiction_map` must explicitly list all conflicts between studies.
4. Every `paper_id` must have a corresponding citation in text and in references.
5. Do not invent transitions — coherence comes from theoretical structure.

# REQUIRED TOOLS
- bash (for running build_capX_structured.py)
- read_file (for inspecting consolidated atoms)

# VALIDATION
Before completing this work, you MUST verify:
- Output `capX_structured.json` is valid JSON
- All sections have 3–8 atoms
- Atom ordering follows R0 → R1 → R2
- `contradiction_map` is populated where applicable
