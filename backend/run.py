import os

import uvicorn
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print(f"\n{'='*52}")
    print(f"  AutoDocThinker backend  ->  http://localhost:{port}")
    print(f"  Routes: /ingest/upload  /ingest/text  /ingest/source")
    print(f"  Docs:   http://localhost:{port}/docs")
    print(f"{'='*52}\n")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
