import json
import re
import sys

# Reconfigure stdout to use utf-8 encoding for printing special characters
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def search_graph(filename, keywords):
    print(f"\n==========================================")
    print(f"SEARCHING {filename}")
    print(f"==========================================")
    with open(filename, 'r', encoding='utf-8') as f:
        graph = json.load(f)
    
    nodes = graph.get('nodes', [])
    edges = graph.get('edges', [])
    
    matching_entities = []
    matching_references = []
    matching_atoms = []
    
    for node in nodes:
        kind = node.get('kind', '')
        label = node.get('label', '') or ''
        
        text_to_search = label.lower()
        if kind == 'reference':
            text_to_search += " " + (node.get('title', '') or '').lower() + " " + (node.get('journal', '') or '').lower()
        elif kind == 'atom':
            text_to_search += " " + (node.get('content', '') or '').lower()
        
        matches = [kw for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', text_to_search)]
        if matches:
            if kind == 'entity':
                matching_entities.append((node, matches))
            elif kind == 'reference':
                matching_references.append((node, matches))
            elif kind == 'atom':
                matching_atoms.append((node, matches))
                
    print(f"Found {len(matching_entities)} matching entities")
    print(f"Found {len(matching_references)} matching references")
    print(f"Found {len(matching_atoms)} matching atoms")
    
    print("\n--- TOP ENTITIES ---")
    sorted_entities = sorted(matching_entities, key=lambda x: x[0].get('occurrence_count', 0), reverse=True)
    for ent, m in sorted_entities[:15]:
        print(f"- {ent['label']} (type: {ent.get('entity_subtype') or ent.get('entity_type')}, count: {ent.get('occurrence_count', 0)}) matches: {m}")
        
    print("\n--- TOP REFERENCES ---")
    sorted_refs = sorted(matching_references, key=lambda x: x[0].get('occurrence_count', 0), reverse=True)
    for ref, m in sorted_refs[:15]:
        print(f"- {ref.get('short_citation')} ({ref.get('year')}): {ref.get('title')} in {ref.get('journal')} [DOI: {ref.get('doi')}] (count: {ref.get('occurrence_count')}) matches: {m}")
        
    print("\n--- TOP ATOMS ---")
    for atom, m in matching_atoms[:20]:
        print(f"- Atom ID: {atom['id']} (Paper: {atom.get('short_citation_references')}) matches: {m}\n  Content: {atom.get('content')}\n")

if __name__ == "__main__":
    kws = ['drought', 'stress', 'hydric', 'era5', 'gradient boosting', 'random forest', 'composite index', 'tamesi', 'tamaulipas', 'mexico']
    search_graph('test_wos_graph.json', kws)
    search_graph('default_graph.json', kws)
