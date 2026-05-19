---
name: 03-graph-mapping
description: Skill para mapear las relaciones conceptuales, ontologías y enlaces físicos/causales a través de los endpoints de Grafo de Conocimiento (KG) de Naut.
triggers: ["mapear grafo", "ver relaciones", "ontología del proyecto", "listar entidades", "relaciones físicas", "concept density"]
---

# Skill 03: Knowledge Graph & Ontology Mapping

## 1. Cuándo Utilizar Este Skill
- **Estructuración Conceptual**: Para mapear cómo interactúan los diferentes conceptos en el estado del arte (ej. qué variables físicas están ligadas al concepto de *estrés hídrico*).
- **Consistencia de Entidades**: Para verificar la consistencia de los términos científicos utilizados en el manuscrito en relación con las bases de datos de Naut.
- **Trazabilidad Causal**: Para reconstruir flujos de causalidad entre variables meteorológicas y variables hidrológicas a partir del grafo de conocimiento.

---

## 2. Cómo y de qué Manera Operar (Endpoints API)

### A. Obtener el Grafo de Conocimiento Enriquecido
Este endpoint proporciona los nodos (entidades y átomos) y los enlaces (`links`) que representan dependencias semánticas, inferencias cruzadas y co-referencias.

- **Endpoint**: `GET /projects/{project}/graph/full`
- **Query Parameters**:
  - `mode`: `"all"` (por defecto) o `"entities"` (solo entidades).
  - `threshold`: Umbral de correlación/confianza semántica (ej. `0.85`).
- **Lógica de Procesamiento**:
  ```python
  import requests
  
  def extract_knowledge_network(base_url: str, project: str, threshold: float = 0.85):
      url = f"{base_url}/projects/{project}/graph/full"
      params = {"mode": "all", "threshold": threshold}
      response = requests.get(url, params=params, timeout=15)
      response.raise_for_status()
      graph_data = response.json()
      
      nodes = graph_data.get("nodes", [])
      edges = graph_data.get("edges", [])
      stats = graph_data.get("statistics", {})
      
      # Filtrar enlaces de inferencia física o causalidad
      causal_relations = []
      for edge in edges:
          if edge.get("type") in ["cross_type_inference", "semantic_cluster"]:
              causal_relations.append({
                  "source": edge["source"],
                  "target": edge["target"],
                  "relation": edge.get("relation_type"),
                  "confidence": edge.get("confidence")
              })
              
      return {"nodes": nodes, "relations": causal_relations, "stats": stats}
  ```

### B. Listar Entidades y Definir Ontologías
- **Endpoint 1**: `GET /projects/{project}/reasoning/ontology`
  - *Retorno*: Estructura jerárquica de tipos de entidades (`Entity Types`) y predicados de relación validados para el dominio científico del proyecto.
- **Endpoint 2**: `GET /projects/{project}/reasoning/entities`
  - *Query Parameters*: `limit` (ej. `100`), `offset` (`0`), `entity_type` (ej. `"climate_variable"`, `"hydrologic_index"`).
  - *Retorno*: Lista de entidades físicas identificadas en la literatura con sus frecuencias de ocurrencia.

### C. Herramienta Automatizada: `get_concepts_graph.py`
Para extraer la taxonomía conceptual y las variables más citadas en la base documental:
- **Comando**:
  ```bash
  uv run python tools/get_concepts_graph.py --limit 100
  ```
- **Resultado esperado**: Genera una tabla en formato Markdown ordenando las variables, índices y conceptos de acuerdo con su frecuencia de aparición en los papers, facilitando la estandarización conceptual del marco teórico.

---

## 3. Reglas de Validación para el Agente
1. **Evitar Sesgos de Co-referencia**: Si dos variables o términos representan físicamente lo mismo (ej. *t2m* y *temperatura a 2 metros*), el agente debe verificar el enlace `entity_coref` en el grafo para mapearlos bajo una nomenclatura única en el manuscrito.
2. **Identificación de Conceptos Clave**: Utilizar los nodos de mayor grado (mayor cantidad de enlaces en el grafo) como los ejes centrales alrededor de los cuales se estructurará la sección de "Discusión de Hallazgos" del artículo.

