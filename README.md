# JS2YAML: JavaScript Model Extractor and YAML Converter

## Overview

**js2yaml.py** is a command-line Python tool that automates the extraction and transformation of model configuration data from a raw JavaScript file into a structured, provider-ready YAML file, along with a detailed metadata summary.

- **Input:** JavaScript file (`raw.js`) with model objects defined using `var`.
- **Output:**
  - `models.yaml` (YAML model definitions, for a specified provider)
  - `meta.json` (run metadata for audit and reproducibility)
- **Workflow:** Organizes each run in a date-stamped subfolder for clarity and repeatability.

---

## Features

- Extracts all `var` object definitions from input JavaScript using Esprima (AST) or regex fallback.
- Parses JS objects using [chompjs](https://github.com/Nv7-GitHub/chompjs) for robust handling of JS syntax.
- Converts model lists and booleans into a consistent YAML structure.
- Supports any provider name—just specify as a CLI argument.
- Automatically organizes outputs in a dated run folder:  
  `runs/runYYYYMMDD/`
- Overwrites any previous run for the same date, ensuring deterministic output.
- Outputs all paths in `meta.json` as relative paths for maximum portability.

---

## Directory Structure

Example after a run on 2025-06-09:

/project-root/
├── js2yaml.py
├── runs/
│   └── run20250609/
│       ├── raw20250609.js
│       ├── models.yaml
│       └── meta.json


---

## Dependencies

- Python 3.7+
- [esprima](https://pypi.org/project/esprima/)
- [chompjs](https://pypi.org/project/chompjs/)
- [PyYAML](https://pypi.org/project/PyYAML/)

Install dependencies:
```sh
pip install esprima chompjs pyyaml
```

## Usage

1. **Place `raw.js` in the main directory.**  
   This file should contain all model definitions using `var`, e.g.:
   ```js
   var gpt4 = { name: "gpt-4", ... };
   var gpt3 = { name: "gpt-3", ... };
`

2. **Run the script with your provider name:**

python js2yaml.py PROVIDER
Example:

python js2yaml.py openai
The script will:

3. **Move and rename raw.js to runs/runYYYYMMDD/rawYYYYMMDD.js**
Write models.yaml and meta.json to the same folder
Arguments

Argument	Required	Example	Description
PROVIDER	Yes	openai	The provider key for YAML
No output file argument needed. All outputs are organized by date.

## Output Files

**models.yaml**
Contains models formatted for the specified provider, ready for direct YAML import.

**meta.json**
Contains run metadata:
timestamp: ISO 8601 UTC datetime of run
input_file: Relative path to input JS file
output_file: Relative path to output YAML file
provider: Provider string as specified on command line
snapshotsCheck: Boolean, ensures all listed snapshots have corresponding model data
model_count: Number of models extracted and written

## Error Handling

If raw.js is missing: The script aborts with an informative error.
If the run folder or output files already exist: They will be overwritten.
If parsing fails or no valid models are found: The script aborts with a clear message.
Example Workflow

# 1. Place raw.js in your project root
cp source_models.js raw.js

# 2. Run extraction and conversion for OpenAI provider
python js2yaml.py openai

# 3. Outputs are now in runs/runYYYYMMDD/
ls runs/run20250609/
# raw20250609.js  models.yaml  meta.json
Notes

The script only supports model definitions using var (not let or const).
For consistent, portable output, all paths in meta.json are relative to the project root.
Overwriting is automatic—be sure to back up your run folders if needed.

Author

Trusten Lehmann-Karp