import ast
import os
import sys

# Configuration
TARGET_DIR = "app"
SKIP_DIRS = ["__pycache__", "venv", ".git"]

class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.issues = []

    def visit_Call(self, node):
        # Check for print() usage
        if isinstance(node.func, ast.Name) and node.func.id == 'print':
            self.issues.append(f"Line {node.lineno}: Usage of 'print()' found. Use 'logger' instead.")
        
        # Check for dangerous functions
        if isinstance(node.func, ast.Name) and node.func.id in ['eval', 'exec']:
            self.issues.append(f"Line {node.lineno}: Dangerous function '{node.func.id}()' used.")
        
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        # Check for broad except without logging (basic heuristic)
        if node.type is None: # bare except:
            self.issues.append(f"Line {node.lineno}: Bare 'except:' clause found. Catch specific exceptions.")
        elif isinstance(node.type, ast.Name) and node.type.id == 'Exception':
            # Check if variable is named (e.g. except Exception as e)
            if not node.name:
                 self.issues.append(f"Line {node.lineno}: 'except Exception:' without variable. Error might be swallowed.")
        
        self.generic_visit(node)

    def visit_Constant(self, node):
        # Check for hardcoded secrets (Basic heuristic)
        if isinstance(node.value, str):
            val = node.value
            if len(val) > 20 and any(k in val.lower() for k in ['key', 'secret', 'token', 'password']) and ' ' not in val:
                 # Reduce false positives: skip if it looks like a config key, not value
                 # This is hard to do perfectly with AST alone without context, so skipping for now to avoid noise.
                 pass
        self.generic_visit(node)

def analyze_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=filepath)
        
        analyzer = CodeAnalyzer(filepath)
        analyzer.visit(tree)
        
        if analyzer.issues:
            print(f"\n[ISSUES] {filepath}")
            for issue in analyzer.issues:
                print(f"  - {issue}")
            return len(analyzer.issues)
    except SyntaxError as e:
        print(f"\n[CRITICAL] Syntax Error in {filepath}: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Failed to analyze {filepath}: {e}")
        return 1
    return 0

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # scripts -> backend
    target_path = os.path.join(root_dir, TARGET_DIR)
    
    print(f"Starting Static Analysis on {target_path}...")
    
    total_issues = 0
    files_checked = 0
    
    for root, dirs, files in os.walk(target_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        for file in files:
            if file.endswith(".py"):
                files_checked += 1
                full_path = os.path.join(root, file)
                total_issues += analyze_file(full_path)

    print(f"\nAnalysis Complete. Checked {files_checked} files. Found {total_issues} issues.")
    if total_issues > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
