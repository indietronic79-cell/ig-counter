import os
import requests
import json

# Recupera il Token dall'ambiente
META_TOKEN = os.environ.get("META_TOKEN")
NPOINT_URL = "https://api.npoint.io/4b40ba1379d34d30dd69"

if not META_TOKEN:
    print("ERRORE: Secret META_TOKEN non trovato!")
    exit(1)

def get_instagram_data():
    print("1. Interrogo Meta API per Pagine, Follower e Tag...")
    
    # 1. Recupera la Pagina Facebook e l'Account Instagram Business collegato
    me_url = f"https://graph.facebook.com/v19.0/me/accounts?access_token={META_TOKEN}"
    res = requests.get(me_url).json()
    
    if "data" not in res or not res["data"]:
        print("Errore nel recupero della pagina:", res)
        exit(1)
        
    page_id = res["data"][0]["id"]
    
    # 2. Ottieni l'ID Account Instagram Business
    ig_acc_url = f"https://graph.facebook.com/v19.0/{page_id}?fields=instagram_business_account&access_token={META_TOKEN}"
    res_ig = requests.get(ig_acc_url).json()
    
    if "instagram_business_account" not in res_ig:
        print("Account Instagram Business non trovato:", res_ig)
        exit(1)
        
    ig_id = res_ig["instagram_business_account"]["id"]
    
    # 3. Chiedi Follower e Username
    profile_url = f"https://graph.facebook.com/v19.0/{ig_id}?fields=followers_count,username&access_token={META_TOKEN}"
    res_profile = requests.get(profile_url).json()
    
    followers = res_profile.get("followers_count", 0)
    username = res_profile.get("username", "prophetpublichouse.lecce")
    
    print(f"--- ACCOUNT: @{username} ---")
    print(f"Follower attuali: {followers}")
    
    # 4. Recupera gli ultimi Post in cui il Pub è stato taggato (Mentioned Media)
    mentions_url = f"https://graph.facebook.com/v19.0/{ig_id}/tags?fields=id,caption,media_type,media_url,permalink,timestamp&limit=5&access_token={META_TOKEN}"
    res_mentions = requests.get(mentions_url).json()
    
    mentions_list = []
    if "data" in res_mentions:
        for item in res_mentions["data"]:
            mentions_list.append({
                "id": item.get("id"),
                "caption": item.get("caption", ""),
                "media_type": item.get("media_type", "IMAGE"),
                "media_url": item.get("media_url", ""),
                "permalink": item.get("permalink", ""),
                "timestamp": item.get("timestamp", "")
            })
    
    print(f"Menzioni/Tag trovati: {len(mentions_list)}")
    
    # 5. Prepara il payload per npoint.io
    payload = {
        "account": f"@{username}",
        "followers": followers,
        "mentions_count": len(mentions_list),
        "mentions": mentions_list
    }
    
    # 6. Aggiorna npoint.io
    headers = {'Content-Type': 'application/json'}
    put_res = requests.post(NPOINT_URL, data=json.dumps(payload), headers=headers)
    print(f"Aggiornamento npoint.io -> Status Code: {put_res.status_code}")

if __name__ == "__main__":
    get_instagram_data()
