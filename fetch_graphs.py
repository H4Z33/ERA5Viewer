import urllib.request
import json
import time

def fetch_graph(project):
    url = f"http://localhost:8000/projects/{project}/graph/full"
    print(f"Starting fetch for {project} from {url}...")
    start_time = time.time()
    try:
        req = urllib.request.Request(url)
        # Use a large timeout (3 minutes) as generating the full graph can take time
        with urllib.request.urlopen(req, timeout=180) as response:
            data = response.read()
            elapsed = time.time() - start_time
            print(f"Successfully fetched {project} graph in {elapsed:.2f} seconds. Size: {len(data)} bytes.")
            
            # Save the graph
            output_file = f"{project}_graph.json"
            with open(output_file, 'wb') as f:
                f.write(data)
            print(f"Saved {output_file}")
    except Exception as e:
        print(f"Error fetching {project}: {e}")

if __name__ == "__main__":
    fetch_graph("default")
    fetch_graph("test_wos")
