import requests
import json

ACCESS_TOKEN = "995535009092790|UeB1t4u-haS7Li8nbnFLAOpyC3M"
USERNAME = "prophetpublichouse.lecce"
NPOINT_URL = "https://api.npoint.io/4b40ba1379d34d30dd69"

try:
    # Proviamo a interrogare la Graph API usando lo username e l'App Token
    url = f"https://graph.facebook.com/v22.0/instagram_oembed"
    # Oppure una chiamata diretta di ricerca profilo
    search_url = f"https://graph.facebook.com/v22.0/ig_hashtag_search" # test di connessione
    
    # Usiamo un endpoint di test standard della Graph API con l'App Token
    test_url = f"https://graph.facebook.com/v22.0/oauth/access_token"
    
    # Proviamo l'endpoint di base di Instagram Graph con l'ID o username
    # Verifichiamo cosa risponde Meta
    res = requests.get(f"https://graph.facebook.com/v22.0/users", params={"username": USERNAME, "access_token": ACCESS_TOKEN})
    print("Risposta API:", res.text)
    
    data = res.json()
    if "id" in data:
        ig_id = data["id"]
        # Se troviamo l'ID, prendiamo i follower
        res_user = requests.get(f"https://graph.facebook.com/v22.0/{ig_id}", params={"fields": "followers_count", "access_token": ACCESS_TOKEN})
        user_data = res_user.json()
        followers = user_data.get("followers_count")
        
        if followers:
            payload = {"username": USERNAME, "followers": followers}
            requests.put(NPOINT_URL, json=payload)
            print(f"Aggiornato con successo via API: {followers} follower")
        else:
            print("Impossibile trovare i follower nella risposta.")
    else:
        print("Il token dell'app non ha restituito l'ID utente diretto. Verifichiamo il formato.")

except Exception as e:
    print(f"Errore durante la richiesta API: {e}")
    
   
       
