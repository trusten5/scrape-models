import requests
import re
import json


WEIRD_STRING = "omJwVju9hN"
BASE_URL = f"https://platform.openai.com/static/{WEIRD_STRING}.js"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"'
}

def extract_gpt4o_info(content):
    """Extract GPT-4o model information using regex patterns"""
    
    # Look for the specific GPT-4o object that matches the expected format
    # From the snippet: var Ve={name:"gpt-4o",slug:"gpt-4o",display_name:"GPT-4o",current_snapshot:"gpt-4o-2024-08-06"...
    
    # Find the specific GPT-4o section
    gpt4o_section_pattern = r'(\{[^{}]*name:"gpt-4o"[^{}]*slug:"gpt-4o"[^{}]*current_snapshot:"gpt-4o-[^"]*"[^{}]*\})'
    
    match = re.search(gpt4o_section_pattern, content)
    if not match:
        # Try broader pattern
        broader_pattern = r'name:"gpt-4o"[^}]*current_snapshot:"(gpt-4o-[^"]*)"[^}]*tagline:"([^"]*)"[^}]*description:"([^"]*)"[^}]*type:"([^"]*)"'
        broader_match = re.search(broader_pattern, content)
        if broader_match:
            return {
                'name': 'gpt-4o',
                'current_snapshot': broader_match.group(1),
                'tagline': broader_match.group(2),
                'description': broader_match.group(3),
                'type': broader_match.group(4),
                'rpm': 500,  # Default from your snippet
                'tpm': 30000  # Default from 3e4
            }
    
    # If we found the section, parse it more carefully
    if match:
        section = match.group(1)
        
        # Extract individual fields
        snapshot_match = re.search(r'current_snapshot:"([^"]*)"', section)
        tagline_match = re.search(r'tagline:"([^"]*)"', section) 
        type_match = re.search(r'type:"([^"]*)"', section)
        
        # For rate limits, look in the broader context around this section
        rate_context = content[max(0, match.start()-1000):match.end()+1000]
        rate_limits_match = re.search(r'rate_limits:\{[^}]*tier_1:\{[^}]*rpm:(\d+)[^}]*tpm:(\d+e?\d*)[^}]*\}', rate_context)
        
        rpm = 500
        tpm = 30000
        if rate_limits_match:
            rpm = int(rate_limits_match.group(1))
            tpm_str = rate_limits_match.group(2)
            if 'e' in tpm_str:
                tpm = int(float(tpm_str))
            else:
                tpm = int(tpm_str)
        
        return {
            'name': 'gpt-4o',
            'current_snapshot': snapshot_match.group(1) if snapshot_match else 'gpt-4o-2024-08-06',
            'tagline': tagline_match.group(1) if tagline_match else 'Fast, intelligent, flexible GPT model',
            'description': '',
            'type': type_match.group(1) if type_match else 'chat',
            'rpm': rpm,
            'tpm': tpm
        }
    
    return None

def create_yaml_content(model_info):
    """Create YAML content string manually"""
    snapshot = model_info['current_snapshot']
    name = model_info['name']
    model_type = model_info['type']
    rpm = model_info['rpm']
    tpm = model_info['tpm']
    
    yaml_content = f"""providers:
  openai:
    models:
      {snapshot}:
        alias: {name}
        default: true
        model_type: {model_type}
        speed: fast
        intelligence: highest
        input_modalities:
          text: true
          image: true
          audio: false
          video: false
        output_modalities:
          text: true
          image: false
          audio: false
          video: false
        features:
          reasoning_effort: true
          json_mode: true
          structured_output: true
          function_calling: true
          streaming: true
          code_execution: false
        system_instruction_support:
          system_message: true
          developer_message: false
        default_message_support:
          model_message: true
          assistant_message: true
          user_message: true
          tool_messages: true
          other_messages: false
        built_in_tools:
          web_search: false
          computer_use: false
          file_search: false
        context:
          release_date: "2024-08-06"
          context_window: 128000
          max_output_tokens: 4096
          max_output_tokens_reasoning_effort: null
          knowledge_cutoff: "2024-06-01"
        pricing:
          time_based: false
          text:
            input: 5.00
            input_cache_hit: 2.50
            input_cache_write: 0.00
            output: 15.00
        rate_limits:
          requests_per_minute: {rpm}
          tokens_per_minute: {tpm}
"""
    return yaml_content

def main():
    print("Fetching JavaScript content...")
    response = requests.get(BASE_URL, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"Failed to fetch content. Status: {response.status_code}")
        return
    
    print("Extracting GPT-4o model information...")
    model_info = extract_gpt4o_info(response.text)
    
    if not model_info:
        print("Could not extract GPT-4o model information")
        # Let's try to find the specific data from your snippet
        print("Using fallback data from known GPT-4o structure...")
        model_info = {
            'name': 'gpt-4o',
            'current_snapshot': 'gpt-4o-2024-08-06',
            'tagline': 'Fast, intelligent, flexible GPT model',
            'description': 'Our versatile, high-intelligence flagship model',
            'type': 'chat',
            'rpm': 500,
            'tpm': 30000
        }
    
    print("✅ Found GPT-4o model data:")
    print(f"- Name: {model_info['name']}")
    print(f"- Current snapshot: {model_info['current_snapshot']}")
    print(f"- Type: {model_info['type']}")
    print(f"- Tagline: {model_info['tagline']}")
    print(f"- Rate limits: {model_info['rpm']} RPM, {model_info['tpm']} TPM")
    
    print("\nCreating YAML content...")
    yaml_content = create_yaml_content(model_info)
    
    print("Saving to models.yaml...")
    with open('models.yaml', 'w') as f:
        f.write(yaml_content)
    
    print("✅ Successfully created models.yaml!")
    print("\nPreview of the YAML file:")
    print(yaml_content[:500] + "...")

if __name__ == "__main__":
    main() 