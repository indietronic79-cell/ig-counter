import os
import requests

# Legge il token in sicurezza dalle variabili d'ambiente di GitHub Actions
ACCESS_TOKEN = os.environ.get("META_TOKEN")
NPOINT_URL = "https://api.npoint.io/4b40ba1379d34d30dd69"

def get_instagram_followers():
    if not ACCESS_TOKEN:
        print("Errore: Token di Meta non trovato nelle variabili d'ambiente!")
        return None, None
        
    print("1. Chiedo a Meta le pagine associate al Token...")
    url_accounts = f"https://graph.facebook.com/v19.0/me/accounts?fields=id,name,instagram_business_account&access_token={ACCESS_TOKEN}"
    
    try:
        res = requests.get(url_accounts, timeout=10).json()
        pages = res.get("data", [])
        
        ig_id = None
        for page in pages:
            if "instagram_business_account" in page:
                ig_id = page["instagram_business_account"]["id"]
                break
                
        if not ig_id:
            print("Nessun account Instagram collegato.")
            return None, None

        # 2. Leggo i follower
        url_followers = f"https://graph.facebook.com/v19.0/{ig_id}?fields=followers_count,username&access_token={ACCESS_TOKEN}"
        final_res = requests.get(url_followers, timeout=10).json()
        
        if "followers_count" in final_res:
            return final_res["username"], final_res["followers_count"]
            
    except Exception as e:
        print(f"Errore HTTP Meta: {e}")
        
    return None, None

username, followers = get_instagram_followers()

if followers is not None:
    print(f"\n--- ESITO META OK ---")
    print(f"Account: @{username}")
    print(f"Follower: {followers}")
    
    payload = {"username": username, "followers": followers}
    headers = {"Content-Type": "application/json"}
    
    update_res = requests.post(NPOINT_URL, json=payload, headers=headers)
    if update_res.status_code != 200:
        update_res = requests.put(NPOINT_URL, json=payload, headers=headers)

    print(f"Aggiornamento npoint.io -> Status Code: {update_res.status_code}")
else:
    print("\n--- TEST FALLITO ---")
