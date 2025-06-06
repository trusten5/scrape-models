"""
Extract only var declarations from a raw JavaScript file using esprima parser.

Usage
-----
1. Install esprima: pip install esprima
2. Save the JS file as ``raw.js`` in the same folder.
3. Run ``python parse_js.py``.

The script extracts all var declarations and saves them to 'raw_no_vars.js'.
"""

import esprima
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

RAW_FILE = Path("raw.js")
OUTPUT_FILE = Path("raw_no_vars.js")

# ---------------------------------------------------------------------------
# Main extraction logic
# ---------------------------------------------------------------------------

def extract_var_declarations(text: str) -> str:
    """Extract all var declarations from JavaScript text using esprima parser."""
    
    try:
        # Parse the JavaScript into an AST
        ast = esprima.parseScript(text, {'loc': True, 'range': True})
    except Exception as e:
        print(f"⚠️  Failed to parse JavaScript: {e}")
        print("Falling back to simple text extraction...")
        return extract_var_fallback(text)
    
    var_declarations = []
    
    def visit_node(node):
        """Recursively visit AST nodes to find var declarations."""
        if hasattr(node, 'type'):
            if node.type == 'VariableDeclaration' and node.kind == 'var':
                # Extract the original text for this var declaration
                start = node.range[0]
                end = node.range[1]
                var_text = text[start:end]
                if not var_text.endswith(';'):
                    var_text += ';'
                var_declarations.append(var_text)
            
            # Recursively visit child nodes
            for key, value in node.__dict__.items():
                if isinstance(value, list):
                    for item in value:
                        if hasattr(item, 'type'):
                            visit_node(item)
                elif hasattr(value, 'type'):
                    visit_node(value)
    
    visit_node(ast)
    return '\n'.join(var_declarations)


def extract_var_fallback(text: str) -> str:
    """Fallback method using simple regex if esprima fails."""
    import re
    
    # Simple pattern to match var declarations
    pattern = r'var\s+[^;]+;'
    matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
    return '\n'.join(matches)


def main():
    if not RAW_FILE.exists():
        raise SystemExit(f"❌ Could not find {RAW_FILE}. Put your JS file there.")

    print("Reading raw.js...")
    raw_text = RAW_FILE.read_text(encoding="utf-8")
    print("File read successfully!")

    print("Extracting var declarations...")
    var_declarations = extract_var_declarations(raw_text)
    
    if not var_declarations:
        print("⚠️  No var declarations found!")
        return
    
    print(f"Writing var declarations to {OUTPUT_FILE}...")
    OUTPUT_FILE.write_text(var_declarations, encoding="utf-8")
    
    print(f"✅ Var declarations extracted and saved to {OUTPUT_FILE}")
    
    # Count number of declarations found
    declaration_count = var_declarations.count('var ')
    print(f"📊 Found {declaration_count} var declarations")


if __name__ == "__main__":
    print("Starting var extraction...")
    try:
        main()
    except ImportError:
        print("❌ esprima not found. Install it with: pip install esprima")
        exit(1)
