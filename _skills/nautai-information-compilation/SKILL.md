---
name: nautai-information-compilation
description: Skill completo para la compilación de información, búsqueda semántica y recuperación de literatura académica a través de la API RAG/KG de Naut (http://localhost:8000).
triggers: ["recuperación de literatura", "compilar información", "búsqueda en Naut", "Naut API", "literatura científica", "bibliometría", "RAG", "Knowledge Graph"]
---

# NautAI Information Compilation & Search Skill

## Objetivo
Interactuar de manera robusta y estructurada con la API REST del sistema Naut (`http://localhost:8000`) para buscar literatura, recuperar átomos de conocimiento, extraer contradicciones y generar reportes bibliométricos de soporte para la redacción científica y validación de hipótesis.

## Arquitectura de la API de Naut
El sistema Naut expone una API para la gestión de proyectos de revisión sistemática de literatura. Los principales endpoints son:

1. **Búsqueda Semántica e Híbrida** (`POST /projects/{project}/search`):
   Realiza búsquedas vectoriales y de palabras clave combinadas sobre la base de datos de átomos extraídos de los papers.
2. **Chat/RAG con Agente** (`POST /projects/{project}/chat`):
   Responde preguntas directas utilizando los átomos de conocimiento como contexto, devolviendo las fuentes (papers y DOIs) asociadas.
3. **Bibliometría** (`GET /projects/{project}/bibliometrics`):
   Retorna estadísticas globales sobre autores, años de publicación, revistas y distribución de palabras clave.
4. **Base de Conocimiento Estructurada** (`GET /projects/{project}/knowledge`):
   Obtiene los átomos clasificados por tipo de hecho (`definition`, `finding`, `mechanism`, `claim`, `observation`).
5. **Contradicciones y Tensiones** (`GET /projects/{project}/reasoning/contradictions`):
   Identifica discrepancias explícitas entre los papers procesados en el proyecto.

---

## Patrones de Uso (Python Templates)

### 1. Búsqueda Híbrida Avanzada (Semantic + Keyword)
```python
import requests
from typing import List, Dict, Any

class NautSearchClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def search(self, project: str, query: str, top_k: int = 10, semantic_weight: float = 0.7) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/projects/{project}/search"
        payload = {
            "query": query,
            "top_k": top_k,
            "hybrid": True,
            "keyword_weight": 1.0 - semantic_weight,
            "semantic_weight": semantic_weight,
            "advanced": True
        }
        response = requests.post(url, json=payload, timeout=20)
        response.raise_for_status()
        return response.json()
```

### 2. Recuperación de Respuestas RAG con Trazabilidad (Sources)
```python
class NautRAGClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def ask(self, project: str, question: str, use_agent: bool = True) -> Dict[str, Any]:
        url = f"{self.base_url}/projects/{project}/chat"
        payload = {
            "message": question,
            "top_k": 10,
            "hybrid": True,
            "use_agent": use_agent
        }
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return {
            "answer": data.get("answer"),
            "sources": [
                {
                    "title": s.get("paper_title") or s.get("title"),
                    "doi": s.get("doi"),
                    "year": s.get("year"),
                    "authors": s.get("authors")
                }
                for s in data.get("sources", [])
            ]
        }
```

### 3. Extracción de Contradicciones de Literatura
```python
class NautReasoningClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def get_contradictions(self, project: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/projects/{project}/reasoning/contradictions"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.json()
```

---

## Buenas Prácticas y Manejo de Errores
- **Timeouts**: Establecer timeouts explícitos de al menos 15s para búsquedas y 30s para chat/RAG para evitar bloqueos del cliente si el modelo local tarda en procesar.
- **Estructuración en APA 7**: Al extraer metadatos de papers (`title`, `authors`, `year`, `doi`), formatear las citas de manera consistente:
  - Cita parentética: `(Morales-Rivera et al., 2026)`
  - Cita narrativa: `Morales-Rivera et al. (2026)`
- **Validación de DOIs**: Siempre verificar que los DOIs recuperados de la API sean válidos y correspondan a publicaciones reales.

# RULES
1. Nunca realizar solicitudes HTTP concurrentes sin control de tasa (rate limiting) para evitar saturar el servidor local Naut.
2. Todas las citas generadas a partir de la información recopilada deben estructurarse bajo la norma APA 7.
3. Si el servidor local Naut devuelve un error 500, capturar la excepción y reintentar con un esquema de retroceso exponencial (exponential backoff).
4. No alterar ni modificar la base de datos de Naut de manera directa; todas las interacciones deben realizarse a través de los endpoints documentados de la API.

# REQUIRED TOOLS
- `requests` (o `httpx` para operaciones asíncronas)
- Python 3.13+

# VALIDATION
Antes de integrar los resultados de búsqueda en un artículo científico, verificar:
- La correspondencia lógica entre la pregunta de investigación y el contenido semántico de las fuentes recuperadas.
- La ausencia de alucinaciones en los metadatos (especialmente DOIs y años de publicación).
- Que las tensiones y contradicciones de literatura mapeadas en la discusión estén directamente fundamentadas en las respuestas obtenidas de los endpoints `/reasoning/contradictions` o `/chat`.
