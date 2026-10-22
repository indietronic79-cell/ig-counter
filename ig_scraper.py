import os
import requests
import json

META_TOKEN = os.environ.get("META_TOKEN")
NPOINT_URL = "https://api.npoint.io/4b40ba1379d34d30dd69"

if not META_TOKEN:
    print("ERRORE: Secret META_TOKEN non trovato!")
    exit(1)

def get_instagram_data():
    print("1. Recupero la pagina e l'Account Instagram Business collegato...")
    
    # Chiediamo direttamente le pagine e l'account IG collegato
    me_url = f"https://graph.facebook.com/v19.0/me/accounts?fields=id,name,instagram_business_account&access_token={META_TOKEN}"
    res = requests.get(me_url).json()
    
    if "data" not in res or not res["data"]:
        print("Errore nel recupero delle pagine:", res)
        exit(1)
        
    ig_id = None
    for page in res["data"]:
        if "instagram_business_account" in page:
            ig_id = page["instagram_business_account"]["id"]
            break

    if not ig_id:
        print("Nessun Account Instagram Business collegato trovato nella Pagina Facebook!")
        print("Risposta Meta:", res)
        exit(1)

    print(f"ID Instagram trovato: {ig_id}")
    
    # 2. Ottieni Follower e Username
    profile_url = f"https://graph.facebook.com/v19.0/{ig_id}?fields=followers_count,username&access_token={META_TOKEN}"
    res_profile = requests.get(profile_url).json()
    
    followers = res_profile.get("followers_count", 0)
    username = res_profile.get("username", "prophetpublichouse.lecce")
    
    print(f"--- ACCOUNT: @{username} ---")
    print(f"Follower attuali: {followers}")
    
    # 3. Recupera gli ultimi Post in cui il Pub è stato taggato (Tags / Mentioned Media)
    mentions_list = []
    try:
        tags_url = f"https://graph.facebook.com/v19.0/{ig_id}/tags?fields=id,caption,media_type,media_url,permalink,timestamp&limit=5&access_token={META_TOKEN}"
        res_tags = requests.get(tags_url).json()
        
        if "data" in res_tags:
            for item in res_tags["data"]:
                mentions_list.append({
                    "id": item.get("id"),
                    "caption": item.get("caption", ""),
                    "media_type": item.get("media_type", "IMAGE"),
                    "media_url": item.get("media_url", ""),
                    "permalink": item.get("permalink", ""),
                    "timestamp": item.get("timestamp", "")
                })
    except Exception as e:
        print(f"Nota sulle menzioni: {e}")

    print(f"Menzioni/Tag trovati: {len(mentions_list)}")
    
    # 4. Aggiorna npoint.io con i dati completi
    payload = {
        "account": f"@{username}",
        "followers": followers,
        "mentions_count": len(mentions_list),
        "mentions": mentions_list
    }
    
    headers = {'Content-Type': 'application/json'}
    put_res = requests.post(NPOINT_URL, data=json.dumps(payload), headers=headers)
    print(f"--- ESITO META OK ---")
    print(f"Aggiornamento npoint.io -> Status Code: {put_res.status_code}")

if __name__ == "__main__":
    get_instagram_data()
