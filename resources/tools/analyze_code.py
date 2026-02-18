import os
import re

PROJECT_ROOT = "/home/jrodriiguezg/backup/codigos/TIO_AI"
OUTPUT_FILE = "resumen.md"

EXCLUDE_DIRS = {
    "venv", "tio.venv", "unsloth_env", ".git", "__pycache__", 
    "vosk-models", "piper", "tts_cache", "logs", "docs", "static", "templates", "jsons", "data", "tests", "tools"
}
# We might want to include tools or tests, but usually "codebase" implies source code. 
# Let's include 'modules' and root files. 
# Actually, let's include everything but the heavy binary/env folders.
# Re-evaluating exclusions based on user request "todo el proyecto".
EXCLUDE_DIRS = {
    "venv", "tio.venv", "unsloth_env", ".git", "__pycache__", 
    "vosk-models", "piper", "tts_cache", "logs", ".tools", ".gemini"
}

def analyze_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception:
        return None

    loc = len(lines)
    classes = 0
    functions = 0
    variables = 0 # Very rough approximation
    
    class_names = []
    function_names = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("class "):
            classes += 1
            # Extract name "class Name:" or "class Name(Parent):"
            match = re.search(r"class\s+([a-zA-Z0-9_]+)", stripped)
            if match:
                class_names.append(match.group(1))
        elif stripped.startswith("def "):
            functions += 1
            # Extract name "def name("
            match = re.search(r"def\s+([a-zA-Z0-9_]+)", stripped)
            if match:
                function_names.append(match.group(1))
        elif "=" in stripped and not stripped.startswith("if") and not stripped.startswith("def") and not stripped.startswith("class"):
            # This is very noisy, but gives an idea of assignments
            variables += 1

    return {
        "loc": loc,
        "classes": classes,
        "class_names": class_names,
        "functions": functions,
        "function_names": function_names,
        "variables": variables,
        "todos": [line.strip() for line in lines if "# TODO" in line or "# FIXME" in line]
    }

def get_project_tree(startpath):
    tree_str = "```\n"
    for root, dirs, files in os.walk(startpath):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        tree_str += f"{indent}{os.path.basename(root)}/\n"
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            if f.endswith(".py") or f.endswith(".sh") or f.endswith(".md"):
                tree_str += f"{subindent}{f}\n"
    tree_str += "```"
    return tree_str

def get_requirements():
    reqs = []
    req_path = os.path.join(PROJECT_ROOT, "requirements.txt")
    if os.path.exists(req_path):
        with open(req_path, 'r') as f:
            reqs = [l.strip() for l in f.readlines() if l.strip() and not l.startswith("#")]
    return reqs

def main():
    total_stats = {"loc": 0, "classes": 0, "functions": 0, "variables": 0, "todos": 0}
    file_stats = []
    all_todos = []

    for root, dirs, files in os.walk(PROJECT_ROOT):
        # Filter directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            if file.endswith(".py") or file.endswith(".sh"):
                filepath = os.path.join(root, file)
                stats = analyze_file(filepath)
                if stats:
                    rel_path = os.path.relpath(filepath, PROJECT_ROOT)
                    stats["path"] = rel_path
                    file_stats.append(stats)
                    
                    total_stats["loc"] += stats["loc"]
                    total_stats["classes"] += stats["classes"]
                    total_stats["functions"] += stats["functions"]
                    total_stats["variables"] += stats["variables"]
                    total_stats["todos"] += len(stats["todos"])
                    
                    for todo in stats["todos"]:
                        all_todos.append(f"- [{rel_path}] {todo}")

    # Generate Markdown
    md_content = f"# Resumen del Proyecto OpenKompai Nano\n\n"
    
    md_content += "## Estructura del Proyecto\n"
    md_content += get_project_tree(PROJECT_ROOT) + "\n\n"

    md_content += "## Estadísticas Generales\n"
    md_content += f"- **Total Líneas de Código:** {total_stats['loc']}\n"
    md_content += f"- **Total Clases:** {total_stats['classes']}\n"
    md_content += f"- **Total Funciones:** {total_stats['functions']}\n"
    md_content += f"- **Total Asignaciones de Variables (Aprox):** {total_stats['variables']}\n"
    md_content += f"- **Total TODOs/FIXMEs:** {total_stats['todos']}\n\n"
    
    md_content += "## Dependencias (requirements.txt)\n"
    reqs = get_requirements()
    if reqs:
        for r in reqs:
            md_content += f"- {r}\n"
    else:
        md_content += "No se encontró requirements.txt o está vacío.\n"
    md_content += "\n"

    if all_todos:
        md_content += "## Tareas Pendientes (TODOs/FIXMEs)\n"
        for todo in all_todos:
            md_content += f"{todo}\n"
        md_content += "\n"
    
    md_content += "## Detalle por Archivo\n\n"
    
    # Sort by LOC descending
    file_stats.sort(key=lambda x: x["loc"], reverse=True)
    
    for fs in file_stats:
        md_content += f"### {fs['path']}\n"
        md_content += f"- **Líneas:** {fs['loc']}\n"
        md_content += f"- **Clases:** {len(fs['class_names'])}\n"
        if fs['class_names']:
            for c in fs['class_names']:
                md_content += f"  - `class {c}`\n"
        md_content += f"- **Funciones:** {len(fs['function_names'])}\n"
        if fs['function_names']:
            for f_name in fs['function_names']:
                md_content += f"  - `def {f_name}`\n"
        md_content += f"- **Variables (Est.):** {fs['variables']}\n"
        if fs['todos']:
             md_content += f"- **TODOs:** {len(fs['todos'])}\n"
        md_content += "\n---\n\n"

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    print(f"Resumen generado en {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
