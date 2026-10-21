import requests
import re
import json

USERNAME = "prophetpublichouse.lecce"
NPOINT_URL = "https://api.npoint.io/4b40ba1379d34d30dd69"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

try:
    url = f"https://www.instagram.com/{USERNAME}/"
    res = requests.get(url, headers=headers)
    
    # Tentativo 1: JSON interno
    match = re.search(r'"edge_followed_by":\{"count":([0-9]+)\}', res.text)
    if not match:
        # Tentativo 2: meta tag followerCount
        match = re.search(r'"followerCount":([0-9]+)', res.text)
    if not match:
        # Tentativo 3: testo Followers
        match = re.search(r'([0-9,.]+)\s*Followers', res.text)
        
    if match:
        raw_val = match.group(1).replace(',', '').replace('.', '')
        followers = int(raw_val)
        
        payload = {"username": USERNAME, "followers": followers}
        requests.put(NPOINT_URL, json=payload)
        print(f"Aggiornato con successo: {followers} follower")
    else:
        print("Impossibile trovare il conteggio dei follower.")
except Exception as e:
    print(f"Errore durante lo scraping: {e}")
