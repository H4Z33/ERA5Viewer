---
name: 01-literature-harvesting
description: Skill para la catalogación, importación e inventario bibliométrico de literatura científica dentro de proyectos de Naut.
triggers: ["listar papers", "importar literatura", "bibliometría del proyecto", "papers base", "cargar PDF", "Web of Science export"]
---

# Skill 01: Literature Harvesting & Cataloging

## 1. Cuándo Utilizar Este Skill
- **Inicio de la investigación**: Para verificar qué literatura ha sido procesada previamente en el proyecto y evaluar los metadatos de partida.
- **Expansión documental**: Cuando falten papers base sobre la temática (ej. climatología, modelos hidrológicos, ERA5-Land) y se deban incorporar PDFs o exportaciones de Web of Science (WoS) e IEEE.
- **Análisis preliminar**: Para generar resúmenes estadísticos (distribución de años, revistas dominantes, autores principales) que describan la base de datos documental.

---

## 2. Cómo y de qué Manera Operar (Endpoints API)

### A. Listar y Validar la Colección de Artículos
- **Endpoint**: `GET /projects/{project}/papers`
- **Utilidad**: Obtiene la lista completa de papers con su `id`, `title`, `doi`, `year`, `authors`, `journal` y su estado de procesamiento (`status` y `atom_count`).
- **Lógica de Agente**:
  ```python
  import requests
  
  def check_project_literature(base_url: str, project: str):
      response = requests.get(f"{base_url}/projects/{project}/papers", timeout=10)
      response.raise_for_status()
      papers = response.json()
      
      indexed_papers = []
      pending_papers = []
      
      for p in papers:
          meta = {
              "id": p["id"],
              "title": p["title"],
              "doi": p.get("doi"),
              "year": p.get("year"),
              "authors": p.get("authors"),
              "status": p.get("status"),
              "atoms": p.get("atom_count", 0)
          }
          if p.get("status") == "processed":
              indexed_papers.append(meta)
          else:
              pending_papers.append(meta)
              
      return {"processed": indexed_papers, "pending": pending_papers}
  ```

### B. Importar Nuevos Documentos (PDF o WoS Exports)
El agente no debe subir archivos de manera directa a través de scripts arbitrarios si ya existe una estructura local. Debe invocar el escaneo y la importación de carpetas controladas:
1.  **Escanear Carpeta Temporal**:
    - **Endpoint**: `POST /projects/{project}/papers/scan-folder`
    - **Payload**: `{"folder_path": "ruta/a/los/pdfs"}`
    - **Resultado**: Retorna los archivos encontrados y si son duplicados (basado en `content_hash`).
2.  **Importar Seleccionados**:
    - **Endpoint**: `POST /projects/{project}/papers/import-folder`
    - **Payload**: `{"files": ["ruta/completa/paper1.pdf", "ruta/completa/paper2.pdf"]}`

### C. Extraer Métricas Bibliométricas
- **Endpoint**: `GET /projects/{project}/bibliometrics`
- **Utilidad**: Retorna distribuciones temporales y de frecuencia útiles para la sección de "Área de Estudio e Inventario de Literatura".
- **Estructura del Output Esperado**:
  ```json
  {
    "year_distribution": {"2022": 15, "2023": 22, "2024": 30},
    "author_frequency": {"Author A": 5, "Author B": 3},
    "journal_distribution": {"Journal of Hydrology": 12, "Water Resources Research": 8}
  }
  ```

---

## 3. Reglas de Validación
1. **Deduplicación Estricta**: Antes de ordenar la importación de un paper, el agente debe verificar que el `doi` o el `content_hash` no existan en la lista obtenida por `GET /projects/{project}/papers`.
2. **Control de Calidad de Metadatos**: Identificar y reportar papers con campos vacíos (`doi` nulo o `year` nulo) para corregirlos mediante `PATCH /projects/{project}/papers/{paper_id}` con metadatos corregidos.

---

## 4. Protocolo de Vacíos de Evidencia (Human-in-the-Loop)
Cuando el agente identifique lagunas de información críticas en el manuscrito (por ejemplo, falta de justificación física sobre el acoplamiento de variables en climas semiáridos o falta de validación de índices alternos como SPEI en la cuenca), debe seguir este protocolo:

1. **Generación de Querys Específicas**: Diseñar una lista de temas de búsqueda formateada con palabras clave lógicas (Booleanas si es necesario) optimizadas para bases de datos científicas internacionales.
   - *Ejemplo*: `("soil moisture potential evapotranspiration coupling" OR "evapoconvective feedback") AND "semi-arid"`
2. **Recomendación al Investigador**: Presentar la lista de keywords y el motivo de la búsqueda (ej. *"Se detectó falta de papers que comparen el índice con el Monitor de Sequía en México"*).
3. **Flujo de Carga**: El investigador buscará y descargará dichos papers desde **Web of Science (WoS)** o **IEEE Xplore**, y los colocará en el proyecto `default` de NautAI para expandir el conocimiento disponible.

