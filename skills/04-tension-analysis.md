---
name: 04-tension-analysis
description: Skill para identificar contradicciones, inconsistencias físicas y consensos validados en la literatura científica procesada por Naut.
triggers: ["listar contradicciones", "consensos", "discrepancias", "analizar discrepancias", "cluster details", "limites de modelos"]
---

# Skill 04: Literature Tension & Consensus Analysis

## 1. Cuándo Utilizar Este Skill
- **Redacción de la sección de Discusión**: Para identificar discrepancias físicas o estadísticas explícitas reportadas entre distintos modelos (ej. acoplamientos fuertes vs. acoplamientos débiles de humedad del suelo bajo diferentes regímenes climáticos).
- **Justificación de la Metodología**: Para mapear consensos científicos sobre la formulación del balance de agua o de índices combinados de estrés.
- **Identificación de Gaps**: Para encontrar limitaciones físicas y fronteras metodológicas de estudios previos.

---

## 2. Cómo y de qué Manera Operar (Endpoints API)

### A. Listar Contradicciones y Tensiones de Literatura
Este endpoint permite al agente identificar dónde chocan los hallazgos de diferentes estudios sin tener que leer y comparar manualmente los papers de forma ciega.

- **Endpoint**: `GET /projects/{project}/reasoning/contradictions`
- **Lógica de Procesamiento**:
  ```python
  import requests
  
  def extract_literature_contradictions(base_url: str, project: str):
      url = f"{base_url}/projects/{project}/reasoning/contradictions"
      response = requests.get(url, timeout=15)
      response.raise_for_status()
      contradictions = response.json()
      
      conflicts_map = []
      for item in contradictions:
          conflict = {
              "id": item.get("id"),
              "concept": item.get("concept"),
              "description": item.get("description"),
              "atoms": item.get("involved_atoms", []),  # Lista de átomos que chocan
              "papers": [
                  {"title": p.get("title"), "doi": p.get("doi"), "authors": p.get("authors")}
                  for p in item.get("involved_papers", [])
              ]
          }
          conflicts_map.append(conflict)
      return conflicts_map
  ```

### B. Recuperar Consensos y Meta-Hallazgos
- **Endpoint**: `GET /projects/{project}/reasoning/consensus`
- **Utilidad**: Retorna los clústeres de átomos que presentan concordancia metodológica o física fuerte, sirviendo como base teórica robusta (R0/R1).

### C. Inspeccionar Detalles de un Clúster de Discusión
- **Endpoint**: `GET /projects/{project}/reasoning/clusters/{cluster_id}`
- **Utilidad**: Permite evaluar de manera desagregada qué artículos respaldan qué afirmaciones secundarias dentro de un clúster semántico específico.

### D. Herramienta Automatizada: `get_contradictions.py`
Para extraer de forma rápida los conflictos conceptuales e inconsistencias físicas registradas en el grafo:
- **Comando**:
  ```bash
  uv run python tools/get_contradictions.py
  ```
- **Resultado esperado**: Un informe detallado con cada conflicto, describiendo la tensión física (por ejemplo, discrepancias de escala temporal en el cálculo del acoplamiento suelo-atmósfera) y listando los átomos específicos que se contradicen junto a sus autores, ideal para nutrir la discusión crítica del borrador.

---

## 3. Reglas de Redacción para el Agente (Regla de Conflicto)
- **Prohibición de Promediar**: Cuando se extraiga una contradicción desde el endpoint `/reasoning/contradictions`, el agente **nunca** debe escribir que los resultados son "mixtos" o "neutrales". Debe redactar un párrafo crítico que:
  1.  Exponga el hallazgo del Estudio A (ej. acoplamiento dominado por evapotranspiración).
  2.  Exponga el hallazgo opuesto del Estudio B (ej. acoplamiento dominado por suministro de agua del suelo).
  3.  Desglose el motivo físico o de escala de la discrepancia (ej. clima húmedo vs. clima árido).
  4.  Proponga cómo el diseño de investigación del artículo CHSI resuelve o se posiciona frente a este conflicto.
- **Validación Factual**: Asegurar que cada paper involucrado en la discrepancia esté debidamente citado en el manuscrito en formato APA 7.

