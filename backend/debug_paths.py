from pathlib import Path

# When app.py runs
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
frontend_index = project_root / 'frontend' / 'dist' / 'index.html'

print(f"__file__: {__file__}")
print(f"Backend dir: {backend_dir}")
print(f"Project root: {project_root}")
print(f"Frontend index: {frontend_index}")
print(f"Exists: {frontend_index.exists()}")

# Now simulate how it works in app.py
import app
print("\nIn app.py context:")
print(f"app.__file__: {app.__file__}")

# Test the actual route
from flask import Flask
test_app = Flask(__name__)

@test_app.route('/')
def test_root():
    backend_dir = Path(__file__).resolve().parent
    project_root = backend_dir.parent
    frontend_index = project_root / 'frontend' / 'dist' / 'index.html'
    print(f"\nInside route function:")
    print(f"  Backend: {backend_dir}")
    print(f"  Project: {project_root}")
    print(f"  Index: {frontend_index}")
    print(f"  Exists: {frontend_index.exists()}")
    return str(frontend_index.exists())

with test_app.test_client() as client:
    response = client.get('/')
    print(f"\nRoute returned: {response.data}")
