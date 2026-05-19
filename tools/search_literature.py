#!/usr/bin/env python3
"""
Tool: search_literature.py
Queries NautAI's search API and outputs structured knowledge atoms categorized
by logical flow stages, with automatically formatted APA 7 citations.
"""

import argparse
import json
import sys
import requests

def format_apa_citation(item: dict) -> str:
    authors = item.get("authors") or "Unknown Author"
    year = f"({item.get('year')})" if item.get("year") else "(n.d.)"
    title = item.get("paper_title") or "Unknown Title"
    journal = item.get("journal") or ""
    
    citation = f"{authors} {year}. {title}."
    if journal:
        citation += f" *{journal}*."
    
    doi = item.get("doi")
    if doi:
        doi_clean = str(doi).strip().lstrip("https://doi.org/")
        citation += f" https://doi.org/{doi_clean}"
        
    return citation

def main():
    parser = argparse.ArgumentParser(description="Query NautAI knowledge atoms and output formatted literature.")
    parser.add_argument("query", type=str, help="Search query string")
    parser.add_argument("--project", type=str, default="default", help="Project name (default: default)")
    parser.add_argument("--top-k", type=int, default=10, help="Number of results to retrieve")
    parser.add_argument("--threshold", type=float, default=0.45, help="Similarity threshold (0.0 to 1.0)")
    parser.add_argument("--url", type=str, default="http://localhost:8000", help="NautAI base URL")
    
    args = parser.parse_args()
    
    search_url = f"{args.url}/projects/{args.project}/search"
    payload = {
        "query": args.query,
        "top_k": args.top_k,
        "hybrid": True,
        "keyword_weight": 0.3,
        "semantic_weight": 0.7,
        "similarity_threshold": args.threshold
    }
    
    try:
        response = requests.post(search_url, json=payload, timeout=20)
        response.raise_for_status()
        results = response.json()
    except Exception as e:
        print(f"Error querying NautAI at {search_url}: {e}", file=sys.stderr)
        sys.exit(1)
        
    if not results:
        print(f"\nNo knowledge atoms found for query: '{args.query}' above threshold {args.threshold}.")
        return

    # Categorize results by atom type / research category
    categories = {
        "definition": [],
        "mechanism": [],
        "finding": [],
        "observation": [],
        "claim": [],
        "other": []
    }
    
    references = {}
    
    for idx, item in enumerate(results, 1):
        atom_type = item.get("atom_type", "other").lower().strip()
        if atom_type not in categories:
            atom_type = "other"
            
        categories[atom_type].append((idx, item))
        
        # Build references dictionary to avoid duplicates
        paper_id = item.get("paper_id", 0)
        if paper_id and paper_id not in references:
            references[paper_id] = format_apa_citation(item)
            
    print(f"# Lit-Search Results: '{args.query}'")
    print(f"Total retrieved atoms: {len(results)}\n")
    
    # Print by structural category
    order = ["definition", "mechanism", "finding", "observation", "claim", "other"]
    headers = {
        "definition": "## 1. Definitions & Concepts",
        "mechanism": "## 2. Physical Mechanisms & Feedbacks",
        "finding": "## 3. Empirical Findings & Trends",
        "observation": "## 4. Observations & Field Notes",
        "claim": "## 5. Hypotheses & Qualitative Claims",
        "other": "## 6. Other General Knowledge"
    }
    
    for cat in order:
        items = categories[cat]
        if not items:
            continue
            
        print(headers[cat])
        for s_idx, (idx, item) in enumerate(items, 1):
            sc = item.get("short_citation") or "Unknown"
            yr = item.get("year") or "n.d."
            ref_str = f"{sc} ({yr})"
            
            content = item.get("content", "").strip()
            print(f"- **[{s_idx}]** {content} — *Cita: {ref_str} [Atom ID: {item.get('atom_id')}]*")
        print()
        
    # Print References section
    if references:
        print("## References (APA 7)")
        for ref in sorted(references.values()):
            print(f"- {ref}")
        print()

if __name__ == "__main__":
    main()
