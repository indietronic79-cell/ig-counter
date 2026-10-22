import requests
import json
import re

USERNAME = "prophetpublichouse.lecce"
NPOINT_URL = "https://api.npoint.io/4b40ba1379d34d30dd69"

def fetch_instagram_followers():
    url = f"https://www.instagram.com/{USERNAME}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            # Cerchiamo il meta tag con la descrizione che di solito contiene i follower (es. "1,234 Followers")
            match = re.search(r'"edge_followed_by":\{"count":(\d+)\}', response.text)
            if match:
                return int(match.group(1))
            
            # Secondo tentativo con i meta tag standard di condivisione
            match_meta = re.search(r'content="(\d+[\d,]*)\s+Followers', response.text)
            if match_meta:
                clean_num = match_meta.group(1).replace(",", "").replace(".", "")
                return int(clean_num)
                
    except Exception as e:
        print(f"Errore durante lo scraping: {e}")
        
    return None

followers = fetch_instagram_followers()

if followers:
    print(f"Trovati {followers} follower!")
    payload = {"username": USERNAME, "followers": followers}
    res = requests.put(NPOINT_URL, json=payload)
    print(f"npoint.io aggiornato con successo! Status: {res.status_code}")
else:
    print("Impossibile estrarre i follower direttamente, mantengo l'ultimo valore valido.")
