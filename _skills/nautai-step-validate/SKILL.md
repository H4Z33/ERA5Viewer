---
name: nautai-step-validate
description: Paso 5: Validación crítica del capítulo generado
triggers: ["nautai validate", "validar capitulo", "critical review", " QA", "quality assurance", "revisar capitulo"]
---

# NautAI-Step: Validate — Critical Chapter Review

## Purpose
Validar el capítulo generado antes de entregarlo. Esta revisión es **obligatoria** antes de ogni entrega.

## Scope of Review

### 1. Consistencia Conceptual
- [ ] Cada variable está definida conceptual y operativamente
- [ ] No hay definiciones circulares
- [ ] Las teorías se aplican consistentemente

### 2. Integridad de Citas
- [ ] Cada afirmación fáctica tiene cita
- [ ] Las citas en texto corresponden a referencias reales
- [ ] Los DOI en referencias son funcionales
- [ ] No hay citas invented o irreconocibles

### 3. Exposición de Contradicciones
- [ ] Los conflictos entre estudios se surfacen explícitamente
- [ ] "Estudios muestran resultados mixtos" **no se permite** sin mapear qué estudios, qué resultados, en qué contexto
- [ ] Las contradicciones se usan como objeto analítico, no como descarte

### 4. Defensibilidad Metodológica
- [ ] Las decisiones metodológicas se justifican
- [ ] Los límites del estudio se respetan en el texto
- [ ] No se infieren relaciones causales de estudios transversales

### 5. Coherencia del Capítulo
- [ ] Estructura jerárquica correcta (2.1 → 2.1.1 → 2.2...)
- [ ] Flujo argumentativo entre secciones
- [ ] Ninguna sección es puro resumen de literatura

### 6. Estilo Académico
- [ ] **NO em dashes** — corregir a comas o "sin embargo"
- [ ] **NO relleno académico genérico**
- [ ] **NO transiciones artificiales**
- [ ] **NO certeza sintética** — usar "sugiere", "indica", "bajo condiciones..."
- [ ] **NO anglicismos no adaptados** — "influencer" → "creador de contenido" o cursiva + definición
- [ ] Oraciones analíticamente densas (cada una justifica su existencia)

### 7. Formato APA 7
- [ ] Citas narrativas y parentéticas correctas
- [ ] Sangría francesa en referencias
- [ ] Tablas y figuras con leyenda completa
- [ ] Encabezados jerárquicos correctos

## Execution
Revisión manual o delegar a sub-agente con los criterios anteriores.
Generar lista de issues encontrados → corregir → volver a validar.

## Output
- Lista de issues
- Capítulo corregido `tesis_ami/Capitulo_X_vN+1.docx`
- Validación final confirmada

# RULES
1. Every checklist item in sections 1–7 MUST be explicitly evaluated — no skipping.
2. "Resultados mixtos" without conflict mapping is a validation failure.
3. Em dashes found in the text are a hard failure — must be corrected before delivery.
4. All DOIs in references must be verifiable (or flagged as unverifiable).

# VALIDATION
Before completing this work, you MUST verify:
- All 7 checklist categories have been evaluated with pass/fail for each item
- A corrected document has been produced if any issues were found
- The final validation summary explicitly states "PASSED" or lists remaining issues
