#!/usr/bin/env python3
"""
Tool: get_concepts_graph.py
Queries NautAI's entities endpoint and outputs a structured taxonomy of
geophysical variables, indices, and methods, ordered by frequency of occurrence.
"""

import argparse
import sys
import requests
from collections import defaultdict

def main():
    parser = argparse.ArgumentParser(description="Retrieve and group entities/concepts from NautAI.")
    parser.add_argument("--project", type=str, default="default", help="Project name (default: default)")
    parser.add_argument("--limit", type=int, default=100, help="Max entities to retrieve")
    parser.add_argument("--url", type=str, default="http://localhost:8000", help="NautAI base URL")
    
    args = parser.parse_args()
    
    url = f"{args.url}/projects/{args.project}/reasoning/entities"
    params = {"limit": args.limit}
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        res_data = response.json()
        entities_list = res_data.get("entities", [])
    except Exception as e:
        print(f"Error querying entities at {url}: {e}", file=sys.stderr)
        sys.exit(1)
        
    if not entities_list:
        print(f"\nNo conceptual entities found in project: '{args.project}'.")
        return
        
    # Group entities by type
    grouped_entities = defaultdict(list)
    for e in entities_list:
        etype = e.get("entity_type") or "general_concept"
        grouped_entities[etype.lower().strip()].append(e)
        
    print(f"# Conceptual Vocabulary & Taxonomy: Project '{args.project}'")
    print(f"Total entities analyzed: {len(entities_list)}\n")
    
    for etype, items in sorted(grouped_entities.items()):
        # Sort items by occurrence count
        items.sort(key=lambda x: x.get("occurrence_count", 0), reverse=True)
        
        # Format header
        header = etype.replace("_", " ").title()
        print(f"## Category: {header}")
        print("| Concept / Variable | Occurrence Count | Description |")
        print("|---|---|---|")
        for item in items:
            name = item.get("name") or "Unnamed"
            count = item.get("occurrence_count", 0)
            desc = item.get("description") or "No description."
            print(f"| **{name}** | {count} | {desc} |")
        print()

if __name__ == "__main__":
    main()
