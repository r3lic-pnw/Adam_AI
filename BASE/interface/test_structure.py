# test_structure.py - Place this in BASE/interface/ directory
import os
import sys
from pathlib import Path

print("=== PROJECT STRUCTURE DIAGNOSTIC ===")
print(f"Current working directory: {os.getcwd()}")
print(f"Script location: {Path(__file__).resolve()}")

# Determine project structure
current_file = Path(__file__).resolve()
interface_dir = current_file.parent
base_dir = interface_dir.parent
project_root = base_dir.parent

print(f"\nDerived paths:")
print(f"Interface dir: {interface_dir}")
print(f"BASE dir: {base_dir}")
print(f"Project root: {project_root}")

print(f"\n=== CHECKING FOR REQUIRED FILES ===")

# Check for key files
files_to_check = [
    project_root / "BASE" / "core" / "config.py",
    project_root / "BASE" / "core" / "ai_core.py",
    project_root / "personality" / "bot_info.py",
    base_dir / "core" / "config.py",
    base_dir / "core" / "ai_core.py",
]

for file_path in files_to_check:
    exists = file_path.exists()
    size = file_path.stat().st_size if exists else 0
    print(f"{'✓' if exists else '✗'} {file_path} ({size} bytes)")

print(f"\n=== DIRECTORY STRUCTURE ===")

def print_tree(path, prefix="", max_depth=3, current_depth=0):
    if current_depth >= max_depth:
        return
    
    if not path.exists():
        return
        
    try:
        items = sorted(path.iterdir())
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            print(f"{prefix}{current_prefix}{item.name}")
            
            if item.is_dir() and not item.name.startswith('.'):
                extension = "    " if is_last else "│   "
                print_tree(item, prefix + extension, max_depth, current_depth + 1)
    except PermissionError:
        print(f"{prefix}└── [Permission Denied]")

print("Project Root Structure:")
print_tree(project_root)

print(f"\n=== PYTHON PATH ===")
for i, path in enumerate(sys.path[:10]):
    print(f"{i}: {path}")

print(f"\n=== IMPORT TESTS ===")

# Test different import strategies
import_tests = [
    ("sys.path.append(str(project_root))", lambda: sys.path.append(str(project_root))),
    ("from BASE.core.config import Config", lambda: __import__('BASE.core.config')),
    ("from core.config import Config", lambda: __import__('core.config')),
    ("import BASE", lambda: __import__('BASE')),
]

for test_name, test_func in import_tests:
    try:
        test_func()
        print(f"✓ {test_name}")
    except Exception as e:
        print(f"✗ {test_name}: {e}")

print(f"\n=== RECOMMENDATIONS ===")

# Check if we're in the right directory
if current_file.parent.name != "interface":
    print("⚠ WARNING: This script should be run from BASE/interface/ directory")
    
if not (project_root / "BASE").exists():
    print("⚠ WARNING: BASE directory not found in expected location")
    print("  Expected structure: Anna_AI/BASE/interface/")
    
if not (project_root / "BASE" / "core").exists():
    print("⚠ WARNING: BASE/core directory not found")
    
print("\nTo fix import issues:")
print("1. Make sure you're running from BASE/interface/ directory")
print("2. Ensure the project structure matches: Anna_AI/BASE/core/")
print("3. Check that all required Python files exist")
print("4. Consider adding __init__.py files in BASE/ and BASE/core/")