#!/usr/bin/env python3
"""
Tool: get_contradictions.py
Queries NautAI's contradiction analysis endpoint and prints a detailed
scientific report on literature tensions and scale disagreements.
"""

import argparse
import sys
import requests

def format_paper_short(paper: dict) -> str:
    authors = paper.get("authors") or "Unknown"
    year = paper.get("year") or "n.d."
    
    # Simple short citation generator
    if ";" in authors or "," in authors:
        # Multiple authors
        parts = [a.strip() for a in authors.replace(";", ",").split(",")]
        if len(parts) > 1:
            short = f"{parts[0]} et al."
        else:
            short = parts[0]
    else:
        short = authors
        
    return f"{short} ({year})"

def main():
    parser = argparse.ArgumentParser(description="Retrieve and format contradictions from NautAI.")
    parser.add_argument("--project", type=str, default="default", help="Project name (default: default)")
    parser.add_argument("--url", type=str, default="http://localhost:8000", help="NautAI base URL")
    
    args = parser.parse_args()
    
    url = f"{args.url}/projects/{args.project}/reasoning/contradictions"
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        res_data = response.json()
        contradictions_list = res_data.get("contradictions", [])
    except Exception as e:
        print(f"Error querying contradictions at {url}: {e}", file=sys.stderr)
        sys.exit(1)
        
    if not contradictions_list:
        print(f"\nNo literature contradictions or physical tensions found in project: '{args.project}'.")
        return
        
    print(f"# Literature Contradictions & Tensions: Project '{args.project}'")
    print(f"Total conflicts detected: {len(contradictions_list)}\n")
    
    for idx, c in enumerate(contradictions_list, 1):
        verdict = c.get("verdict") or "tension"
        reasoning = c.get("reasoning") or "No explanation provided."
        cluster_id = c.get("cluster_id") or "N/A"
        
        print(f"## Conflict {idx}: Verdict: {verdict.upper()} (Cluster ID: {cluster_id})")
        if reasoning and reasoning.strip():
            print(f"**AI Reasoning:** {reasoning}\n")
            
        atom_a = c.get("atom_a") or {}
        atom_b = c.get("atom_b") or {}
        
        print("**Contradicting Claims:**")
        if atom_a:
            a_id = atom_a.get("id")
            content_a = atom_a.get("content") or ""
            paper_a = atom_a.get("paper_title") or "Unknown Paper"
            print(f"- **[SOURCE A]** *\"{paper_a}\" (Atom ID: {a_id})*:\n  > \"{content_a}\"")
            
        if atom_b:
            b_id = atom_b.get("id")
            content_b = atom_b.get("content") or ""
            paper_b = atom_b.get("paper_title") or "Unknown Paper"
            print(f"- **[SOURCE B]** *\"{paper_b}\" (Atom ID: {b_id})*:\n  > \"{content_b}\"")
            
        print()
        print("-" * 40)
        print()

if __name__ == "__main__":
    main()
