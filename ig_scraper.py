import os
import requests

PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")
PAGE_ID = "167069679971123"
NPOINT_URL = "https://api.npoint.io/4b40ba1379d34d30dd69"

def get_instagram_followers():
    if not PAGE_TOKEN:
        raise ValueError("FB_PAGE_TOKEN non trovato nei Secret di GitHub.")

    url = f"https://graph.facebook.com/v20.0/{PAGE_ID}"
    params = {
        "fields": "instagram_business_account{followers_count,username},name",
        "access_token": PAGE_TOKEN
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    # Stampa l'intera risposta nei log di GitHub per capire cosa restituisce Meta
    print("Risposta completa ricevuta da Meta:", data)
    
    if "instagram_business_account" in data and data["instagram_business_account"]:
        ig_info = data["instagram_business_account"]
        followers = ig_info.get("followers_count", 0)
        username = ig_info.get("username", "prophetpublichouse.lecce")
        print(f"Follower trovati per {username}: {followers}")
        return followers
    else:
        raise Exception(f"La Pagina Facebook non restituisce un account Instagram collegato con questo token. Risposta: {data}")

def update_npoint(followers_count):
    payload = {"followers": followers_count}
    response = requests.post(NPOINT_URL, json=payload, timeout=10)
    
    if response.status_code == 200:
        print(f"npoint.io aggiornato con successo a {followers_count} follower!")
    else:
        raise Exception(f"Errore npoint.io ({response.status_code}): {response.text}")

if __name__ == "__main__":
    try:
        count = get_instagram_followers()
        update_npoint(count)
    except Exception as e:
        print(f"Errore durante l'esecuzione: {e}")
        exit(1)
