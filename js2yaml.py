"""
Combined JS var extractor and YAML converter.

Dependencies:
    pip install esprima chompjs pyyaml

Usage:
    python js2yaml.py PROVIDER
Example:
    python js2yaml.py openai
"""

import sys
import pathlib
import yaml
import json
from datetime import datetime, timezone
import shutil

# Optional: esprima import for AST parsing, fallback to regex if not available.
try:
    import esprima
    HAS_ESPRIMA = True
except ImportError:
    HAS_ESPRIMA = False

import chompjs

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------

FEATURE_KEYS = [
    "streaming", "predicted_outputs", "image_input", "structured_outputs", "function_calling",
    "prompt_caching", "evals", "stored_completions", "fine_tuning", "distillation",
    "file_search", "file_uploads", "web_search", "json_mode", "reasoning_effort", "system_messages"
]
INPUT_MODALITY_KEYS = ["text", "image", "audio"]
OUTPUT_MODALITY_KEYS = ["text", "image", "audio", "video"]
SUPPORTED_TOOLS_KEYS = [
    "function_calling", "web_search", "file_search", "file_uploads", "image_generation",
    "code_interpreter", "mcp"
]
SUPPORTED_ENDPOINTS_KEYS = [
    "chat_completions", "completions", "responses", "assistants", "batch", "image_generation",
    "image_edit", "transcription", "translation", "embeddings", "moderation",
    "speech_generation", "realtime"
]

# -----------------------------------------------------------------------------
# MODULES
# -----------------------------------------------------------------------------

def extract_var_declarations(text: str) -> str:
    if HAS_ESPRIMA:
        try:
            ast = esprima.parseScript(text, {'loc': True, 'range': True})
            var_declarations = []
            def visit_node(node):
                if hasattr(node, 'type'):
                    if node.type == 'VariableDeclaration' and node.kind == 'var':
                        start, end = node.range
                        var_text = text[start:end]
                        if not var_text.endswith(';'):
                            var_text += ';'
                        var_declarations.append(var_text)
                    for key, value in node.__dict__.items():
                        if isinstance(value, list):
                            for item in value:
                                if hasattr(item, 'type'):
                                    visit_node(item)
                        elif hasattr(value, 'type'):
                            visit_node(value)
            visit_node(ast)
            return '\n'.join(var_declarations)
        except Exception:
            return extract_var_fallback(text)
    else:
        return extract_var_fallback(text)

def extract_var_fallback(text: str) -> str:
    import re
    pattern = r'var\s+[^;]+;'
    matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
    return '\n'.join(matches)

def extract_var_objects(js_code):
    objects = []
    i = 0
    n = len(js_code)
    while i < n:
        var_pos = js_code.find('var ', i)
        if var_pos == -1: break
        eq_pos = js_code.find('=', var_pos)
        if eq_pos == -1: break
        brace_pos = js_code.find('{', eq_pos)
        if brace_pos == -1: break
        brace_count = 0
        end_pos = brace_pos
        while end_pos < n:
            if js_code[end_pos] == '{':
                brace_count += 1
            elif js_code[end_pos] == '}':
                brace_count -= 1
                if brace_count == 0: break
            end_pos += 1
        if brace_count != 0:
            i = eq_pos + 1
            continue
        obj_str = js_code[brace_pos:end_pos + 1]
        objects.append(obj_str)
        i = end_pos + 1
    return objects

def try_parse_js_object(obj_str):
    try:
        obj = chompjs.parse_js_object(obj_str)
        return obj
    except Exception:
        return None

def bool_dict_from_list_or_dict(obj, keys):
    if isinstance(obj, dict):
        return {k: bool(obj.get(k, False)) for k in keys}
    elif isinstance(obj, list):
        return {k: (k in obj) for k in keys}
    else:
        return {k: False for k in keys}

def model_to_yaml_entry(model):
    name = model.get("name", f"model_{id(model)}")
    model_copy = dict(model)
    if "supported_features" in model_copy:
        model_copy["supported_features"] = bool_dict_from_list_or_dict(
            model_copy["supported_features"], FEATURE_KEYS)
    if "supported_tools" in model_copy:
        model_copy["supported_tools"] = bool_dict_from_list_or_dict(
            model_copy["supported_tools"], SUPPORTED_TOOLS_KEYS)
    if "supported_endpoints" in model_copy:
        model_copy["supported_endpoints"] = bool_dict_from_list_or_dict(
            model_copy["supported_endpoints"], SUPPORTED_ENDPOINTS_KEYS)
    if "modalities" in model_copy:
        mod = model_copy["modalities"]
        if isinstance(mod, dict):
            if "input" in mod:
                mod["input"] = bool_dict_from_list_or_dict(mod["input"], INPUT_MODALITY_KEYS)
            if "output" in mod:
                mod["output"] = bool_dict_from_list_or_dict(mod["output"], OUTPUT_MODALITY_KEYS)
            model_copy["modalities"] = mod
    return (name, model_copy)

def build_models_dict(models):
    models_dict = {}
    for model in models:
        if not model or "name" not in model:
            continue
        key, value = model_to_yaml_entry(model)
        models_dict[key] = value
    return models_dict

def build_yaml_from_models_dict(models_dict, provider_name):
    yaml_dict = {
        "providers": {
            provider_name: {
                "models": models_dict
            }
        }
    }
    return yaml.dump(yaml_dict, sort_keys=False, allow_unicode=True)

def snapshots_detailed_check(models_dict):
    for model_name, model_data in models_dict.items():
        snapshots = model_data.get("snapshots", [])
        if not snapshots:
            continue
        for snapshot in snapshots:
            if snapshot not in models_dict:
                return False
    return True

# -----------------------------------------------------------------------------
# ENTRYPOINT
# -----------------------------------------------------------------------------

def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python js2yaml.py <provider>")

    provider_name = sys.argv[1]

    # Assume raw.js in main directory
    project_root = pathlib.Path().resolve()
    raw_js_path = project_root / "raw.js"

    if not raw_js_path.exists():
        sys.exit("Could not find raw.js in the current directory.")

    # Get today's date in YYYYMMDD format
    date_str = datetime.now(timezone.utc).strftime('%Y%m%d')

    # Create run directory
    run_dir = project_root / "runs" / f"run{date_str}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Target JS file path in run directory
    target_js_name = f"raw{date_str}.js"
    target_js_path = run_dir / target_js_name

    # Overwrite if the file already exists
    if target_js_path.exists():
        target_js_path.unlink()

    # Rename and move raw.js
    shutil.move(str(raw_js_path), str(target_js_path))

    # Prepare output paths
    models_yaml_path = run_dir / "models.yaml"
    meta_json_path = run_dir / "meta.json"

    # Read the JS file for parsing
    js_text = target_js_path.read_text(encoding="utf-8")

    # All meta paths are relative to project root
    input_js_rel = target_js_path.relative_to(project_root)
    models_yaml_rel = models_yaml_path.relative_to(project_root)

    # Step 1: Extract only var declarations (as text)
    var_decls = extract_var_declarations(js_text)
    if not var_decls.strip():
        sys.exit("No var declarations found in the input file.")

    # Step 2: Extract objects and parse them
    obj_strs = extract_var_objects(var_decls)
    objects = [try_parse_js_object(s) for s in obj_strs]

    # Step 3: Build models dict, YAML, and write YAML to output file
    models_dict = build_models_dict(objects)
    yaml_out = build_yaml_from_models_dict(models_dict, provider_name)
    models_yaml_path.write_text(yaml_out, encoding="utf-8")
    print(f"Wrote YAML to {models_yaml_path} for provider '{provider_name}'")

    # Step 4: Checks for metadata
    snapshotsCheck = snapshots_detailed_check(models_dict)

    # Step 5: Write meta.json with relative paths
    meta = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_file": str(input_js_rel),
        "output_file": str(models_yaml_rel),
        "provider": provider_name,
        "snapshotsCheck": snapshotsCheck,
        "model_count": len(models_dict)
    }
    with open(meta_json_path, "w", encoding="utf-8") as mf:
        json.dump(meta, mf, indent=2)
    print(f"Wrote meta.json to {meta_json_path}")

if __name__ == "__main__":
    main()
