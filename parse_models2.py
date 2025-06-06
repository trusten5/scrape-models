import requests


WEIRD_STRING = "rt5YY58dru"
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

URL = f"{BASE_URL}"

response = requests.get(URL, headers=HEADERS)

if response.ok:
    print("Content fetched successfully!")
    print("Saving to test.js...")
    
    with open('test.js', 'w', encoding='utf-8') as f:
        f.write(response.text)
    
    print("✅ Content saved to test.js")
else:
    print(f"Failed to fetch content. Status: {response.status_code}")
    exit(1)


