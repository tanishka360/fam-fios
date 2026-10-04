import sys
import os
import uvicorn

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    print("=" * 70)
    print("  FAM-FIOS: Multi-Tenant Operating System API Server")
    print("  Local Server: http://127.0.0.1:8000")
    print("  Interactive Swagger Docs: http://127.0.0.1:8000/docs")
    print("=" * 70)
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
