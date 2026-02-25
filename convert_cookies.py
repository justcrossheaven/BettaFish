"""
Utility to convert Playwright cookie format to twikit-compatible format

Playwright stores cookies in this format:
{
  "cookies": [ ... array of cookies ... ],
  "origins": [ ... ]
}

Twikit expects cookies in the standard Python cookie jar format.
"""

import json
import os
from pathlib import Path

def convert_playwright_cookies_to_twikit(playwright_cookies_path: str, twikit_cookies_path: str = None):
    """
    Convert Playwright cookies to twikit format.
    
    Args:
        playwright_cookies_path: Path to Playwright cookies JSON file
        twikit_cookies_path: Output path for twikit cookies (default: same name with _twikit suffix)
    """
    if twikit_cookies_path is None:
        base = Path(playwright_cookies_path).stem
        twikit_cookies_path = str(Path(playwright_cookies_path).parent / f"{base}_twikit.json")
    
    # Load Playwright cookies
    with open(playwright_cookies_path, 'r', encoding='utf-8') as f:
        playwright_data = json.load(f)
    
    # Extract cookies array from Playwright format
    cookies = playwright_data.get('cookies', [])
    
    # Convert to simple cookie dict array (twikit/httpx compatible)
    # twikit uses httpx which expects cookies as a simple dict
    twikit_cookies = {}
    for cookie in cookies:
        name = cookie.get('name')
        value = cookie.get('value')
        if name and value:
            twikit_cookies[name] = value
    
    # Save in twikit format (simple dict)
    with open(twikit_cookies_path, 'w', encoding='utf-8') as f:
        json.dump(twikit_cookies, f, indent=2)
    
    print(f"✓ Converted {len(cookies)} cookies from Playwright format")
    print(f"✓ Saved twikit-compatible cookies to: {twikit_cookies_path}")
    return twikit_cookies_path


if __name__ == "__main__":
    # Convert the default twitter_cookies.json
    playwright_file = "twitter_cookies.json"
    
    if not os.path.exists(playwright_file):
        print(f"Error: {playwright_file} not found")
        print("Run the get_twitter_cookies.js script first to generate cookies")
        exit(1)
    
    twikit_file = convert_playwright_cookies_to_twikit(playwright_file)
    print(f"\nYou can now use {twikit_file} with twikit!")
