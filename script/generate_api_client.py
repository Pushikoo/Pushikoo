import json
from pathlib import Path
import subprocess
from pushikoo.api import app

ROOT = Path(__file__).parent.parent.resolve()

openapi_file = ROOT / "frontend" / "openapi.json"
openapi_file.touch(exist_ok=True)
openapi_file.write_text(json.dumps(app.openapi()), encoding="utf-8")
subprocess.check_call(["pnpm", "generate-client"], cwd=ROOT / "frontend", shell=True)
