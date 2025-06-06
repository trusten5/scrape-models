import sys
import pathlib
import chompjs
import yaml

# to run python vars2yaml.py [datafoldername].js > [outputfolder name]

# EDIT: Define all possible values for the boolean map fields.
FEATURE_KEYS = [
    "streaming",
    "predicted_outputs",
    "image_input",
    "structured_outputs",
    "function_calling",
    "prompt_caching",
    "evals",
    "stored_completions",
    "fine_tuning",
    "distillation",
    "file_search",
    "file_uploads",
    "web_search",
    "json_mode",            # If present in your JS
    "reasoning_effort",     # If present in your JS
    "system_messages",      # (not "system_message" - but keep if used elsewhere)
]

INPUT_MODALITY_KEYS = [
    "text",
    "image",
    "audio"
]

OUTPUT_MODALITY_KEYS = [
    "text", "image", "audio", "video"
]
SYSTEM_INSTRUCTION_SUPPORT_KEYS = [
    "system_message",
    "developer_message"
]

BUILT_IN_TOOLS_KEYS = [
    "function_calling",
    "web_search",
    "file_search",
    "file_uploads",
    "image_generation",
    "code_interpreter",
    "mcp",
]

SUPPORTED_ENDPOINTS_KEYS = [
    "chat_completions",
    "completions",
    "responses",
    "assistants",
    "batch",
    "image_generation",
    "image_edit",
    "transcription",
    "translation",
    "embeddings",
    "moderation",
    "speech_generation",
    "realtime",
    # Add other possible endpoint keys you expect
]


def extract_var_objects(js_code):
    # ... (unchanged)
    print("[*] Extracting JS object blocks assigned by `var XXX = {...}` ...", file=sys.stderr)
    objects = []
    i = 0
    n = len(js_code)
    while i < n:
        var_pos = js_code.find('var ', i)
        if var_pos == -1:
            break
        eq_pos = js_code.find('=', var_pos)
        if eq_pos == -1:
            break
        brace_pos = js_code.find('{', eq_pos)
        if brace_pos == -1:
            break
        brace_count = 0
        end_pos = brace_pos
        while end_pos < n:
            if js_code[end_pos] == '{':
                brace_count += 1
            elif js_code[end_pos] == '}':
                brace_count -= 1
                if brace_count == 0:
                    break
            end_pos += 1
        if brace_count != 0:
            print(f"[!] Malformed object after 'var' at {var_pos}. Skipping.", file=sys.stderr)
            i = eq_pos + 1
            continue
        obj_str = js_code[brace_pos:end_pos + 1]
        objects.append(obj_str)
        i = end_pos + 1
    print(f"[*] Found {len(objects)} JS object blocks.", file=sys.stderr)
    return objects

def try_parse_js_object(obj_str, idx=None):
    # ... (unchanged)
    try:
        obj = chompjs.parse_js_object(obj_str)
        if isinstance(obj, dict) and "name" in obj:
            print(f"    [+] Parsed model '{obj.get('name','?')}'", file=sys.stderr)
        else:
            print(f"    [!] Parsed object #{idx} has no 'name', will show as 'N/A'", file=sys.stderr)
        return obj
    except Exception as e:
        print(f"    [!] Warning: could not parse object #{idx}: {e}", file=sys.stderr)
        return None

def clean_date(val):
    # ... (unchanged)
    import re
    from datetime import datetime, timezone
    if isinstance(val, str):
        if 'Date(' in val:
            try:
                num = float(val.split('Date(')[1].split(')')[0])
                return datetime.fromtimestamp(num / 1000, tz=timezone.utc).date().isoformat()
            except Exception:
                return "N/A"
        elif len(val) >= 10 and val[:4].isdigit():
            return val
    elif isinstance(val, (int, float)):
        try:
            return datetime.fromtimestamp(val / 1000, tz=timezone.utc).date().isoformat()
        except Exception:
            return "N/A"
    return "N/A"

def safe_get(d, keys, default="N/A"):
    # ... (unchanged)
    curr = d
    for k in keys:
        if not isinstance(curr, dict) or k not in curr:
            return default
        curr = curr[k]
    return curr

# EDIT: Helper to turn a possibly partial dict/list into a dict of all keys -> bool
def bool_dict_from_list_or_dict(obj, keys):
    # Accepts a dict with boolean values, a list of keys present, or None
    if isinstance(obj, dict):
        return {k: bool(obj.get(k, False)) for k in keys}
    elif isinstance(obj, list):
        # If input is a list of enabled keys, treat as True, else False
        return {k: (k in obj) for k in keys}
    else:
        return {k: False for k in keys}

def model_to_yaml_entry(model):
    name = model.get("name", f"model_{id(model)}")
    model_copy = dict(model)  # Avoid mutating input

    # Normalize supported_features
    if "supported_features" in model_copy:
        model_copy["supported_features"] = bool_dict_from_list_or_dict(
            model_copy["supported_features"], FEATURE_KEYS
        )
    # Normalize supported_tools
    if "supported_tools" in model_copy:
        model_copy["supported_tools"] = bool_dict_from_list_or_dict(
            model_copy["supported_tools"], BUILT_IN_TOOLS_KEYS
        )
    # Normalize supported_endpoints
    if "supported_endpoints" in model_copy:
        model_copy["supported_endpoints"] = bool_dict_from_list_or_dict(
            model_copy["supported_endpoints"], SUPPORTED_ENDPOINTS_KEYS
        )
    # Normalize input/output modalities (nested under "modalities")
    if "modalities" in model_copy:
        mod = model_copy["modalities"]
        if isinstance(mod, dict):
            # Convert input
            if "input" in mod:
                mod["input"] = bool_dict_from_list_or_dict(mod["input"], INPUT_MODALITY_KEYS)
            # Convert output
            if "output" in mod:
                mod["output"] = bool_dict_from_list_or_dict(mod["output"], OUTPUT_MODALITY_KEYS)
            model_copy["modalities"] = mod

    return (name, model_copy)



def build_yaml(models):
    # ... (unchanged)
    models_yaml = {}
    for model in models:
        if not model or "name" not in model:
            continue
        key, value = model_to_yaml_entry(model)
        models_yaml[key] = value
    yaml_dict = {
        "providers": {
            "openai": {
                "models": models_yaml
            }
        }
    }
    return yaml.dump(yaml_dict, sort_keys=False, allow_unicode=True)

if __name__ == "__main__":
    # ... (unchanged)
    if len(sys.argv) == 2:
        path = pathlib.Path(sys.argv[1]).expanduser()
        print(f"[*] Reading JS from file: {path}", file=sys.stderr)
        raw_js = path.read_text(encoding="utf-8")
    elif not sys.stdin.isatty():
        print("[*] Reading JS from stdin...", file=sys.stderr)
        raw_js = sys.stdin.read()
    else:
        print("Usage: python vars2yaml.py <file.js>  OR  cat file.js | python vars2yaml.py",
              file=sys.stderr)
        sys.exit(1)

    obj_strs = extract_var_objects(raw_js)
    objects = [try_parse_js_object(s, idx=i+1) for i, s in enumerate(obj_strs)]
    print("[*] Building YAML output ...", file=sys.stderr)
    print(build_yaml(objects))
