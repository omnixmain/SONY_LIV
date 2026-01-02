import requests
import re
import json
import time
import datetime


SOURCE_M3U_URL = "https://raw.githubusercontent.com/omnixmain/OMNIX-OTT-TV/refs/heads/main/sony_php_links.m3u"
OUTPUT_FILE = "sony_streams.m3u"


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://allinonereborn.xyz/"
}

def fetch_m3u(url):
    print(f"Fetching source M3U from {url}...")
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def extract_stream_url(php_url):
    try:
        # print(f"  Resolving {php_url}...")
        response = requests.get(php_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        # Look for the JSON object in the HTML
        # pattern: const channelData = {...};
        match = re.search(r'const channelData\s*=\s*(\{.*?\});', response.text)
        if match:
            json_str = match.group(1)
            data = json.loads(json_str)
            if 'm3u8' in data:
                return data['m3u8']
        
        # Fallback regex if json parse fails or structure changes
        match_url = re.search(r'"m3u8":"(https?://[^"]+)"', response.text)
        if match_url:
             return match_url.group(1).replace('\\/', '/')

    except Exception as e:
        print(f"  Error resolving {php_url}: {e}")
    
    return None

def process_m3u(content):
    lines = content.splitlines()
    today = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
    header = f"""#EXTM3U
#=================================
# Developed By: OMNIX EMPIRE
# Telegram Channels: https://t.me/omnix_Empire
# Last Updated: {today}
# Disclaimer:
# This tool does NOT host any content.
# It aggregates publicly available data for informational purposes only.
# For any issues or concerns, please contact the developer.
#=================================="""

    new_lines = [header]
    
    current_extinf = None
    
    total_lines = len(lines)
    processed_count = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith("#EXTINF"):
            current_extinf = line
        elif line.startswith("http"):
            processed_count += 1
            print(f"Processing channel {processed_count}...")
            
            stream_url = extract_stream_url(line)
            
            if stream_url:
                if current_extinf:
                    new_lines.append(current_extinf)
                    new_lines.append(stream_url)
                    # Add referrer header for player compatibility if needed, 
                    # though the user asked for simple streaming URL.
                    # Usually these tokens need the referer, but m3u8 has token inside.
                else:
                    # In case there was no EXTINF before (unlikely in valid M3U)
                    new_lines.append(f"#EXTINF:-1,Channel {processed_count}")
                    new_lines.append(stream_url)
            else:
                print(f"  Failed to extract stream for {line}")
                # Optionally keep the original link or skip? User wants "streaming url nikal kar do"
                # I will skip if not found to ensure only working links.
            
            current_extinf = None
            time.sleep(0.5) # Be nice to the server

    return "\n".join(new_lines)



def main():
    try:
        content = fetch_m3u(SOURCE_M3U_URL)
        new_m3u_content = process_m3u(content)
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(new_m3u_content)
            
        print(f"\nSuccess! Saved to {OUTPUT_FILE}")
        

        
    except Exception as e:
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    main()
