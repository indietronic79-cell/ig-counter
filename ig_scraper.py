
import os
import sys
import logging
import requests

META_TOKEN = os.environ.get("META_TOKEN")
NPOINT_URL = "https://api.npoint.io/4b40ba1379d34d30dd69"
GRAPH_VERSION = os.getenv("META_GRAPH_VERSION", "v19.0")
BASE_URL = f"https://graph.facebook.com/{GRAPH_VERSION}"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

session = requests.Session()
session.headers.update({"User-Agent": "InstagramCounter/2.0"})


def graph_get(path, params=None):
    """Esegue una richiesta Meta e segnala gli errori reali."""
    response = session.get(
        f"{BASE_URL}/{path.lstrip('/')}",
        params={**(params or {}), "access_token": META_TOKEN},
        timeout=20
    )
    response.raise_for_status()

    data = response.json()

    if "error" in data:
        error = data["error"]
        raise RuntimeError(
            f"Meta API error {error.get('code')}: "
            f"{error.get('message', 'Errore sconosciuto')}"
        )

    return data


def get_instagram_data():
    if not META_TOKEN:
        raise RuntimeError("Secret META_TOKEN mancante")

    logging.info("Recupero pagine Facebook e account Instagram")

    pages_data = graph_get(
        "me/accounts",
        {"fields": "id,name,instagram_business_account", "limit": 100}
    )

    pages = pages_data.get("data", [])
    ig_id = None

    for page in pages:
        instagram = page.get("instagram_business_account")
        if instagram and instagram.get("id"):
            ig_id = instagram["id"]
            break

    if not ig_id:
        raise RuntimeError(
            "Nessun account Instagram professionale collegato "
            "alle pagine accessibili dal token"
        )

    logging.info("Account Instagram ID trovato")

    profile = graph_get(
        ig_id,
        {"fields": "followers_count,username"}
    )

    # Non pubblicare dati incompleti o un falso zero.
    if "followers_count" not in profile:
        raise RuntimeError(
            f"followers_count assente nella risposta Meta: {profile}"
        )

    followers = int(profile["followers_count"])
    username = profile.get("username")

    if followers < 0 or not username:
        raise RuntimeError("Profilo Instagram incompleto o non valido")

    logging.info("Profilo @%s: %s follower", username, followers)

    mentions = []

    # /tags restituisce i media in cui l'account è taggato,
    # non tutte le menzioni presenti su Instagram.
    try:
        result = graph_get(
            f"{ig_id}/tags",
            {
                "fields": (
                    "id,caption,media_type,media_url,"
                    "permalink,timestamp"
                ),
                "limit": 5
            }
        )

        for item in result.get("data", []):
            mentions.append({
                "id": item.get("id"),
                "caption": item.get("caption", ""),
                "media_type": item.get("media_type", "IMAGE"),
                "media_url": item.get("media_url", ""),
                "permalink": item.get("permalink", ""),
                "timestamp": item.get("timestamp", "")
            })

    except (requests.RequestException, RuntimeError, ValueError) as exc:
        # I dati principali possono essere salvati anche se
        # l'endpoint dei tag non è accessibile.
        logging.warning("Recupero tag non riuscito: %s", exc)

    payload = {
        "account": f"@{username}",
        "followers": followers,
        "mentions_count": len(mentions),
        "mentions": mentions
    }

    # Non aggiornare il cloud se Meta non ha restituito
    # un profilo valido.
    response = session.post(
        NPOINT_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=20
    )
    response.raise_for_status()

    logging.info(
        "Aggiornamento npoint completato: HTTP %s",
        response.status_code
    )


if __name__ == "__main__":
    try:
        get_instagram_data()
    except Exception as exc:
        logging.error("%s", exc)
        sys.exit(1)
    finally:
        session.close()
