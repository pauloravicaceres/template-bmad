import json
import urllib.request

try:
    with urllib.request.urlopen("http://127.0.0.1:8000/api/v1/workflow/status?include_history=true") as response:
        data = json.loads(response.read().decode())
        stages = data.get("stages", [])
        for stage in stages:
            print(f"Stage: {stage.get('stage_key')} -> Artifact: {stage.get('generated_artifact_path')}")
except Exception as e:
    print(f"API Error: {e}")