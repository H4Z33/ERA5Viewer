---
name: 02-semantic-search
description: Skill para ejecutar búsquedas semánticas e híbridas en la base de datos de átomos de conocimiento de Naut, abstrayendo resultados estructurados para el agente.
triggers: ["buscar evidencia", "búsqueda híbrida", "recuperar átomos", "post /search", "encontrar citas", "conceptos clave"]
---

# Skill 02: Semantic & Hybrid Search

## 1. Cuándo Utilizar Este Skill
- **Fundamentación de hipótesis**: Para buscar evidencia física específica sobre la interacción de variables (ej. cómo influye la humedad de suelo residual `swvl1` en los picos de evaporación potencial `pev`).
- **Construcción del Marco Teórico**: Para extraer definiciones precisas de variables e índices climáticos/hidrológicos reportados en otros estudios.
- **Búsqueda de Co-localización**: Para identificar si hay estudios previos que hayan evaluado la cuenca del Tamesí o la región del Noreste de México.

---

## 2. Cómo y de qué Manera Operar (Endpoints API)

### A. Ejecutar Búsqueda Híbrida Estructurada
El agente **nunca debe usar el endpoint de chat** para extraer evidencia cruda. Debe usar directamente la búsqueda híbrida pasándole parámetros de peso específicos para balancear la similitud semántica (embeddings) y la coincidencia exacta de palabras clave (BM25).

- **Endpoint**: `POST /projects/{project}/search`
- **Payload Schema**:
  ```json
  {
    "query": "ERA5-Land soil moisture potential evaporation Tamesi basin coupling",
    "top_k": 10,
    "hybrid": true,
    "keyword_weight": 0.3,
    "semantic_weight": 0.7,
    "advanced": true,
    "similarity_threshold": 0.5
  }
  ```
- **Lógica de Ejecución en el Agente**:
  ```python
  import requests
  
  def query_naut_evidence(base_url: str, project: str, query_str: str, limit: int = 10):
      url = f"{base_url}/projects/{project}/search"
      payload = {
          "query": query_str,
          "top_k": limit,
          "hybrid": True,
          "keyword_weight": 0.3,
          "semantic_weight": 0.7,
          "similarity_threshold": 0.45
      }
      r = requests.post(url, json=payload, timeout=20)
      r.raise_for_status()
      results = r.json()
      
      extracted_evidence = []
      for item in results:
          evidence = {
              "atom_id": item["atom_id"],
              "paper_id": item["paper_id"],
              "score": item["score"],
              "content": item["content"],
              "type": item.get("atom_type"),
              "paper_title": item.get("paper_title"),
              "doi": item.get("doi"),
              "year": item.get("year"),
              "authors": item.get("authors"),
              "confidence": item.get("confidence", 1.0)
          }
          extracted_evidence.append(evidence)
      return extracted_evidence
  ```

### B. Herramienta Automatizada: `search_literature.py`
Para búsquedas rápidas desde la terminal, el agente puede usar el script provisto en la carpeta de herramientas:
- **Comando**:
  ```bash
  uv run python tools/search_literature.py "Tu consulta de búsqueda aquí" --top-k 10 --threshold 0.45
  ```
- **Resultado esperado**: El script imprime los resultados clasificados por categorías científicas (Definiciones, Mecanismos, Hallazgos, etc.) y genera la lista consolidada de referencias formateadas en APA 7.

---

## 3. Reglas de Interpretación para el Agente
- **Filtro por Confianza**: Filtrar los resultados cuya propiedad `confidence` (o `validated_confidence`) sea inferior a `0.40`, a menos que se desee discutir hipótesis emergentes en la sección de discusión (R2).
- **Asignación de Tipo**: Clasificar los átomos recuperados según su propiedad `atom_type` para modular la redacción científica:
  - `definition` o `mechanism` $\rightarrow$ Redacción R0 (Directa y declarativa).
  - `finding` o `observation` $\rightarrow$ Redacción R1 (Condicional).
  - `claim` $\rightarrow$ Redacción R2 (Cualificada/Atribución).
- **Trazabilidad APA 7**: Cada fragmento de contenido extraído de un átomo debe mapearse directamente con sus metadatos (`authors`, `year`, `doi`) para evitar alucinaciones en el manuscrito final.

