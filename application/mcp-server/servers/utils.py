from pathlib import Path
import json
import threading

DATA_DIR = Path(__file__).parent / ".." / "data"
DATA_DIR = DATA_DIR.resolve()


_write_lock = threading.Lock()

def read_json(path: Path):
    if not path.exists():
        return []
    return json.loads(path.read_text())

def write_json(path: Path, data):
    with _write_lock:
        path.write_text(json.dumps(data, indent=2))
