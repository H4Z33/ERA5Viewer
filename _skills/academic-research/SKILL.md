---
name: academic-research
description: Skill para realizar investigación académica automatizada usando Wikipedia, CrossRef, y otras fuentes abiertas.
triggers: ["investigaci\u00f3n acad\u00e9mica", "tesis", "revisi\u00f3n sistem\u00e1tica", "bibliograf\u00eda", "Wikipedia", "CrossRef", "SciELO"]
---

# Academic Research Skill

## Objetivo
Realizar búsquedas y extracción de información académica de fuentes abiertas para enriquecer documentos de investigación.

## Herramientas disponibles
1. **Wikipedia API** (`wikipediaapi`) - Para definiciones conceptuales y contexto general.
2. **CrossRef API** (`requests`) - Para metadatos de artículos científicos por DOI.
3. **OpenAlex API** (`requests`) - Para descubrimiento de literatura académica.
4. **Semantic Scholar API** (`requests`) - Para papers y citas.

## Patrones de uso

### WikipediaSkill
```python
import wikipediaapi
import requests

class WikipediaSkill:
    def __init__(self, language: str = "es"):
        self.wiki = wikipediaapi.Wikipedia(
            language=language,
            user_agent="MiriAcademicResearch/1.0 (contact: research@miri.local)"
        )

    def search(self, query: str):
        url = "https://es.wikipedia.org/w/api.php"
        params = {
            "action": "opensearch",
            "search": query,
            "limit": 5,
            "namespace": 0,
            "format": "json"
        }
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        titles = data[1]
        return titles[0] if titles else None

    def get_summary(self, title: str, sentences: int = 3):
        page = self.wiki.page(title)
        if not page.exists():
            return {"error": f"Page '{title}' not found."}
        summary = page.summary
        short = ". ".join(summary.split(". ")[:sentences]).strip()
        if not short.endswith("."):
            short += "."
        return {
            "title": page.title,
            "summary": short,
            "url": page.fullurl
        }

    def run(self, query: str):
        title = self.search(query)
        if not title:
            return {"error": "No results found."}
        return self.get_summary(title)
```

### CrossRefSkill
```python
class CrossRefSkill:
    def __init__(self):
        self.base_url = "https://api.crossref.org/works"
        self.headers = {"User-Agent": "MiriAcademicResearch/1.0"}

    def search(self, query: str, rows: int = 5):
        params = {"query": query, "rows": rows, "sort": "relevance", "order": "desc"}
        r = requests.get(self.base_url, params=params, headers=self.headers, timeout=15)
        r.raise_for_status()
        items = r.json()["message"]["items"]
        return [
            {
                "title": i.get("title", ["N/A"])[0],
                "authors": [f"{a.get('given','')} {a.get('family','')}" for a in i.get("author", [])[:3]],
                "year": i.get("published-print", {}).get("date-parts", [["N/A"]])[0][0],
                "doi": i.get("DOI"),
                "journal": i.get("container-title", ["N/A"])[0],
                "type": i.get("type")
            }
            for i in items
        ]
```

## Buenas prácticas
- Siempre usar `timeout` en requests.
- Respetar rate limits (esperar entre requests).
- Citar fuentes correctamente en formato APA 7.
- Verificar que la información obtenida sea relevante antes de integrarla.

# RULES
1. Always include `timeout` on every HTTP request (min 10s, max 30s).
2. Respect API rate limits — never fire concurrent requests to the same endpoint.
3. All citations must use APA 7 format.
4. Verify that retrieved information is relevant before integrating it into any document.
5. Never fabricate DOIs, authors, or publication years.

# REQUIRED TOOLS
- web_search (for discovery when APIs fail)
- bash (for running Python scripts with requests/wikipediaapi)

# VALIDATION
Before completing this work, you MUST verify:
- Every citation has a real, verifiable source (DOI or URL)
- API responses were parsed without errors
- No duplicate references were introduced
