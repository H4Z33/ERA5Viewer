---
name: 05-science-writing
description: Skill de redacción científica de alto rigor (nivel Q1), control epistémico en español, cumplimiento estricto de APA 7 y eliminación de patrones de escritura de IA comunes.
triggers: ["redactar prosa", "estilo de escritura", "corrección de estilo", "anglicismos", "APA 7", "estructurar párrafo"]
---

# Skill 05: Q1 Scientific Writing & Epistemic Control

## 1. Cuándo Utilizar Este Skill
- **Redacción de secciones del artículo**: Al escribir el Abstract, Introducción, Metodología, Resultados, Discusión y Conclusiones.
- **Auditoría de estilo**: Al revisar prosa pre-existente o generada para limpiar vicios de lenguaje, conectores artificiales y estructuras redundantes.
- **Formateo final**: Para asegurar la correcta jerarquía de títulos y el cumplimiento exacto de la norma APA 7.

---

## 2. Cómo y de qué Manera Operar (Régimen Epistémico)

El agente debe controlar de manera precisa la asertividad de cada oración a partir de los datos crudos obtenidos de la base de conocimientos de NautAI.

| Nivel Epistémico | Tipo de Evidencia | Rango de Confianza | Estilo de Redacción | Ejemplo Práctico |
|---|---|---|---|---|
| **R0: Leyes & Mecanismos** | `mechanism`, `definition` | $\ge 0.50$ | Declarativo directo. Hechos físicos absolutos. | *"La evaporación potencial representa la tasa límite de transferencia de vapor de agua hacia la atmósfera en condiciones de saturación de superficie."* |
| **R1: Hallazgos Empíricos** | `finding` | $0.40 - 0.49$ | Condicional, circunstanciado a escalas físicas y temporales del estudio. | *"En la cuenca del Tamesí, la temperatura de 2 metros exhibe una tendencia al alza significativa de $+0.0387^\circ\text{C}/\text{año}$ ($p = 0.0032$)."* |
| **R2: Afirmaciones Cualitativas** | `claim`, `observation` | $< 0.40$ | Calificado con verbos de atenuación (*sugiere*, *podría*, *indica la posibilidad*). | *"La covarianza de baja frecuencia entre la temperatura y la humedad superficial sugiere que el calentamiento regional podría estar acelerando el desecamiento de la capa superior del suelo."* |

---

## 3. Control de Estilo y Patrones Prohibidos

El agente debe eliminar sistemáticamente los siguientes patrones comunes en textos redactados por modelos generativos generales:

1.  **Guiones largos (Em dashes: —)**: Están prohibidos en español científico. Sustitúyalos por comas, punto y coma o paréntesis.
2.  **Conectores vacíos**: Eliminar conectores que solo sirven de relleno (ej. *"Por otra parte..."*, *"En este orden de ideas..."*, *"Cabe destacar que..."*, *"Es importante señalar..."*). Las oraciones deben encadenarse mediante relaciones lógicas directas.
3.  **Certidumbre Sintética**: No usar *"Está plenamente demostrado..."* o *"Es un hecho innegable..."* a menos que se cite la ley física correspondiente.
4.  **Resultados Mixtos Vagos**: No escribir que los resultados son *"mixtos"* o *"inconsistentes"* sin detallar los parámetros en conflicto (según el protocolo de **Skill 04**).
5.  **Simetría Sintáctica**: Variar la estructura y longitud de las oraciones sucesivas para evitar un ritmo repetitivo y artificial.

---

## 4. Adaptación de Terminología Técnica (Glosario de Anglicismos)

Para escribir un español científico natural y formal, evite las traducciones literales de términos en inglés:

| Término en Inglés | Traducción Literal (Prohibida) | Adaptación Científica (Requerida) |
|---|---|---|
| *Soil moisture* | Humedad del suelo | Contenido de agua en el suelo (o humedad edáfica) |
| *Potential evaporation* | Evaporación potencial | Demanda evaporativa potencial (o evaporación potencial) |
| *Flash drought* | Sequía relámpago | Sequía repentina (o sequía de desarrollo rápido) |
| *Reanalysis dataset* | Conjunto de datos de reanálisis | Datos de reanálisis climático |
| *Target variable* | Variable objetivo | Variable de respuesta (o variable dependiente) |
| *Feature engineering* | Ingeniería de características | Extracción (o derivación) de variables predictoras |
| *Water stress* | Estrés de agua | Estrés hídrico |
| *Ground truth* | Verdad de terreno | Datos de referencia (o mediciones in situ) |

---

## 5. Normas de Formato (APA 7)
- **Citas en el texto**:
  - Un autor: `(Morales, 2026)`
  - Dos autores: `(Morales & Rivera, 2026)` en parentética; `Morales y Rivera (2026)` en narrativa.
  - Tres o más autores: `(Morales et al., 2026)` desde la primera aparición.
- **Sección de Referencias**:
  - Usar sangría francesa.
  - El título de las revistas y libros debe ir en cursiva.
  - Incluir siempre el DOI en formato HTTPS completo: `https://doi.org/10.xxxx/xxxx`.
