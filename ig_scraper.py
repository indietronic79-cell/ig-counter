
import os
import sys
import logging
import requests

# ============================================================
# CONFIGURAZIONE
# ============================================================

META_TOKEN = os.environ.get("META_TOKEN")

# Endpoint npoint già utilizzato dal Raspberry Pi
NPOINT_URL = "https://api.npoint.io/4b40ba1379d34d30dd69"

# Versione Graph API configurabile tramite variabile d'ambiente
GRAPH_VERSION = os.getenv("META_GRAPH_VERSION", "v25.0")
BASE_URL = f"https://graph.facebook.com/{GRAPH_VERSION}"

REQUEST_TIMEOUT = 20
USER_AGENT = "InstagramCounter/3.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})


# ============================================================
# RICHIESTE HTTP E GESTIONE ERRORI
# ============================================================

def graph_get(path, params=None):
    """Esegue una richiesta Meta e restituisce errori dettagliati."""

    if not META_TOKEN:
        raise RuntimeError("Secret META_TOKEN mancante")

    response = session.get(
        f"{BASE_URL}/{path.lstrip('/')}",
        params={
            **(params or {}),
            "access_token": META_TOKEN
        },
        timeout=REQUEST_TIMEOUT
    )

    try:
        data = response.json()
    except ValueError:
        data = {}

    if not response.ok:
        error = data.get("error", {})
        message = error.get("message", response.reason)
        code = error.get("code", "N/D")
        subcode = error.get("error_subcode", "N/D")

        # Non registrare mai il token nei log.
        raise RuntimeError(
            f"Meta API HTTP {response.status_code}; "
            f"code={code}; subcode={subcode}: {message}"
        )

    if not isinstance(data, dict):
        raise RuntimeError("Risposta Meta non valida: JSON inatteso")

    if "error" in data:
        error = data["error"]
        raise RuntimeError(
            f"Meta API error {error.get('code', 'N/D')}: "
            f"{error.get('message', 'Errore sconosciuto')}"
        )

    return data


# ============================================================
# RECUPERO ACCOUNT INSTAGRAM
# ============================================================

def trova_account_instagram():
    """Trova un account Instagram professionale accessibile."""

    logging.info("Recupero pagine Facebook e account Instagram")

    pages_data = graph_get(
        "me/accounts",
        {
            "fields": "id,name,instagram_business_account",
            "limit": 100
        }
    )

    pages = pages_data.get("data", [])

    if not isinstance(pages, list):
        raise RuntimeError("Elenco pagine Facebook non valido")

    for page in pages:
        instagram = page.get("instagram_business_account")

        if instagram and instagram.get("id"):
            logging.info(
                "Account Instagram trovato tramite una pagina accessibile"
            )
            return instagram["id"]

    raise RuntimeError(
        "Nessun account Instagram professionale collegato "
        "alle pagine accessibili dal token"
    )


# ============================================================
# RECUPERO CONTENUTI TAGGATI
# ============================================================

def recupera_contenuti_tagged(ig_id):
    """
    Recupera i media taggati accessibili tramite /tags.

    Non rappresenta il totale di tutte le menzioni Instagram.
    Se il recupero fallisce, restituisce None per distinguere
    un errore da un elenco effettivamente vuoto.
    """

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

        items = result.get("data", [])

        if not isinstance(items, list):
            raise RuntimeError("Elenco dei contenuti taggati non valido")

        mentions = []

        for item in items:
            mentions.append({
                "id": item.get("id"),
                "caption": item.get("caption") or "",
                "media_type": item.get("media_type") or "IMAGE",
                "media_url": item.get("media_url") or "",
                "permalink": item.get("permalink") or "",
                "timestamp": item.get("timestamp") or ""
            })

        logging.info(
            "Contenuti taggati recuperati: %s",
            len(mentions)
        )

        return mentions

    except (
        requests.RequestException,
        RuntimeError,
        ValueError
    ) as exc:
        logging.warning(
            "Recupero contenuti taggati non riuscito: %s",
            exc
        )
        return None


# ============================================================
# AGGIORNAMENTO NPOINT
# ============================================================

def aggiorna_npoint(payload):
    """Pubblica i dati su npoint e verifica la risposta HTTP."""

    response = session.post(
        NPOINT_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=REQUEST_TIMEOUT
    )

    if not response.ok:
        raise RuntimeError(
            f"Aggiornamento npoint fallito: HTTP "
            f"{response.status_code}"
        )

    logging.info(
        "Aggiornamento npoint completato: HTTP %s",
        response.status_code
    )


# ============================================================
# PROCEDURA PRINCIPALE
# ============================================================

def get_instagram_data():
    if not META_TOKEN:
        raise RuntimeError("Secret META_TOKEN mancante")

    ig_id = trova_account_instagram()

    profile = graph_get(
        ig_id,
        {"fields": "followers_count,username"}
    )

    if "followers_count" not in profile:
        raise RuntimeError(
            "followers_count assente nella risposta Meta"
        )

    followers_raw = profile["followers_count"]

    if isinstance(followers_raw, bool):
        raise RuntimeError("followers_count non valido")

    try:
        followers = int(followers_raw)
    except (ValueError, TypeError) as exc:
        raise RuntimeError("followers_count non numerico") from exc

    username = profile.get("username")

    if followers < 0 or not isinstance(username, str) or not username.strip():
        raise RuntimeError("Profilo Instagram incompleto o non valido")

    logging.info(
        "Profilo @%s: %s follower",
        username,
        followers
    )

    mentions = recupera_contenuti_tagged(ig_id)

    # Non sovrascrivere dati precedenti con un falso zero
    # se il recupero dei contenuti taggati fallisce.
    if mentions is None:
        logging.warning(
            "Aggiornamento follower mantenuto; "
            "dati dei tag precedenti da preservare"
        )

        # Legge il documento esistente per preservare i tag.
        try:
            existing_response = session.get(
                NPOINT_URL,
                timeout=REQUEST_TIMEOUT
            )
            existing_response.raise_for_status()
            existing_data = existing_response.json()

            if not isinstance(existing_data, dict):
                raise ValueError("JSON npoint non valido")

            mentions = existing_data.get("mentions", [])

            if not isinstance(mentions, list):
                mentions = []

        except (
            requests.RequestException,
            ValueError
        ) as exc:
            raise RuntimeError(
                "Impossibile preservare i dati dei tag esistenti: "
                f"{exc}"
            ) from exc

    payload = {
        "account": f"@{username}",
        "followers": followers,
        "mentions_count": len(mentions),
        "mentions": mentions
    }

    aggiorna_npoint(payload)


# ============================================================
# AVVIO
# ============================================================

if __name__ == "__main__":
    try:
        get_instagram_data()

    except Exception as exc:
        logging.error("%s", exc)
        sys.exit(1)

    finally:
        session.close()
