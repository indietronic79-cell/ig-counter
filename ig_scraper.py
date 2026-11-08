import os
import sys
import logging
from typing import Optional, Dict, Any
import requests

# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("IGScraper")

# ---------------------------------------------------------------------------
# Constants & Environment Configuration
# ---------------------------------------------------------------------------
META_TOKEN = os.getenv("META_TOKEN")
JSON_BIN_URL = os.getenv("JSON_BIN_URL")

API_VERSION = "v18.0"
GRAPH_BASE_URL = f"https://graph.facebook.com/{API_VERSION}"
HTTP_TIMEOUT = 10  # Seconds


# ---------------------------------------------------------------------------
# Session Management & Helper Functions
# ---------------------------------------------------------------------------
def create_authenticated_session(token: str) -> requests.Session:
    """Creates and configures a requests.Session with standard Bearer authentication headers."""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    })
    return session


def extract_ig_id(data: Dict[str, Any]) -> Optional[str]:
    """Safely extracts the Instagram Business account ID from a Meta Graph API response dictionary."""
    if not isinstance(data, dict):
        return None
    
    # 1. Standard nested structure check (e.g., from /me/accounts)
    ig_account = data.get("instagram_business_account")
    if isinstance(ig_account, dict) and "id" in ig_account:
        return ig_account["id"]
        
    # 2. Direct resource node check
    if data.get("id") and "followers_count" in data:
        return data["id"]

    return None


# ---------------------------------------------------------------------------
# Core Logic: Instagram Account Resolution & Data Retrieval
# ---------------------------------------------------------------------------
def fetch_instagram_business_id(session: requests.Session) -> str:
    """Resolves the Instagram Business account ID using multiple fallback strategies

    to support User Tokens, Page Tokens, and System User tokens.
    """
    # Strategy 1: Endpoint /me/accounts (Standard User/System User tokens with page permissions)
    try:
        response = session.get(
            f"{GRAPH_BASE_URL}/me/accounts",
            params={"fields": "instagram_business_account,name"},
            timeout=HTTP_TIMEOUT
        ).json()
        
        if "data" in response and isinstance(response["data"], list):
            for page in response["data"]:
                ig_id = extract_ig_id(page)
                if ig_id:
                    logger.info("Found IG business account linked to Facebook page: '%s'", page.get('name'))
                    return ig_id
    except requests.RequestException as e:
        logger.warning("Attempt via /me/accounts failed: %s", e)

    # Strategy 2: Direct /me endpoint (System User or direct resource token)
    try:
        response = session.get(
            f"{GRAPH_BASE_URL}/me",
            params={"fields": "id,name,instagram_business_account"},
            timeout=HTTP_TIMEOUT
        ).json()
        
        ig_id = extract_ig_id(response)
        if ig_id:
            logger.info("Found IG business account directly from main /me node ('%s')", response.get('name'))
            return ig_id

        # Strategy 3: Explicit query on the returned Page ID
        if "id" in response:
            page_id = response["id"]
            page_res = session.get(
                f"{GRAPH_BASE_URL}/{page_id}",
                params={"fields": "instagram_business_account"},
                timeout=HTTP_TIMEOUT
            ).json()
            
            ig_id = extract_ig_id(page_res)
            if ig_id:
                logger.info("Found IG business account querying Page ID directly: %s", page_id)
                return ig_id
    except requests.RequestException as e:
        logger.warning("Attempt via direct /me lookup failed: %s", e)

    raise RuntimeError("No accessible Instagram professional account found using the provided token.")


def push_to_remote_endpoint(session: requests.Session, target_url: str, followers: int) -> None:
    """Sends the updated followers count to the configured remote storage endpoint."""
    payload = {"followers": followers}
    is_jsonbin = "jsonbin" in target_url

    try:
        if is_jsonbin:
            res = session.post(target_url, json=payload, timeout=HTTP_TIMEOUT)
        else:
            res = session.put(target_url, json=payload, timeout=HTTP_TIMEOUT)

        if res.status_code in (200, 201):
            logger.info("Remote endpoint updated successfully (HTTP %d).", res.status_code)
        else:
            logger.warning("Unexpected status code from remote endpoint: HTTP %d - %s", res.status_code, res.text)
    except requests.RequestException as e:
        logger.error("Failed to update remote endpoint: %s", e)


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------
def main() -> None:
    if not META_TOKEN:
        logger.critical("Configuration error: META_TOKEN environment variable is not set.")
        sys.exit(1)

    session = create_authenticated_session(META_TOKEN)

    try:
        logger.info("Starting Instagram metrics retrieval process...")
        ig_id = fetch_instagram_business_id(session)

        # Retrieve profile metrics (followers and username)
        profile_res = session.get(
            f"{GRAPH_BASE_URL}/{ig_id}",
            params={"fields": "followers_count,username"},
            timeout=HTTP_TIMEOUT
        ).json()

        if "error" in profile_res:
            error_msg = profile_res["error"].get("message", "Unknown Meta API Error")
            raise RuntimeError(f"Meta Graph API Error: {error_msg}")

        followers = profile_res.get("followers_count")
        username = profile_res.get("username", "unknown")

        if followers is None:
            raise ValueError("The 'followers_count' field was not returned by the API.")

        logger.info("Successfully fetched data for @%s (ID: %s) -> Current followers: %d", username, ig_id, followers)

        # Synchronize with remote endpoint if available
        if JSON_BIN_URL:
            push_to_remote_endpoint(session, JSON_BIN_URL, followers)
        else:
            logger.info("JSON_BIN_URL is not set. Skipping remote synchronization.")

    except Exception as err:
        logger.error("Execution failed: %s", err)
        sys.exit(1)


if __name__ == "__main__":
    main()
