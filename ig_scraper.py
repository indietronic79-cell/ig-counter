import os
import requests

# Token salvato nei Secret di GitHub
PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")
PAGE_ID = "167069679971123"

# URL del tuo bin npoint.io estratto dallo script del Raspberry
NPOINT_URL = "https://api.npoint.io/4b40ba1379d34d30dd69"

def get_instagram_followers():
    if not PAGE_TOKEN:
        raise ValueError("FB_PAGE_TOKEN non trovato nei Secret di GitHub.")

    # Recupera i dati da Meta Graph API
    url = f"https://graph.facebook.com/v20.0/{PAGE_ID}"
    params = {
        "fields": "instagram_business_account{followers_count,username}",
        "access_token": PAGE_TOKEN
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if "instagram_business_account" in data:
        followers = data["instagram_business_account"].get("followers_count", 0)
        username = data["instagram_business_account"].get("username", "prophetpublichouse.lecce")
        print(f"Follower trovati per {username}: {followers}")
        return followers
    else:
        raise Exception(f"Errore nella lettura dell'account Instagram: {data}")

def update_npoint(followers_count):
    payload = {
        "followers": followers_count
    }
    
    # Aggiorna il JSON del bin su npoint.io
    response = requests.post(NPOINT_URL, json=payload, timeout=10)
    
    if response.status_code == 200:
        print(f"npoint.io aggiornato con successo a {followers_count} follower!")
    else:
        print(f"Errore aggiornamento npoint.io ({response.status_code}): {response.text}")

if __name__ == "__main__":
    try:
        count = get_instagram_followers()
        update_npoint(count)
    except Exception as e:
        print(f"Errore durante l'esecuzione: {e}")
        exit(1)
