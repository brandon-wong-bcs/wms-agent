# wms_client.py
import os, time, requests
from dotenv import load_dotenv

load_dotenv()
BASE_URL   = os.environ["WMS_BASE_URL"]      # e.g. https://localhost:44300
TOKEN_URL  = os.environ["WMS_TOKEN_URL"]     # the token URL you used in Thunder Client
VERIFY_SSL = os.getenv("WMS_VERIFY_SSL", "true").lower() == "true"

_token = {"value": None, "expires_at": 0}

def _get_token():
    if _token["value"] and time.time() < _token["expires_at"] - 60:
        return _token["value"]                      # reuse until ~1 min before expiry
    resp = requests.post(TOKEN_URL, data={
        "grant_type": "password",
        "client_id": os.environ["WMS_CLIENT_ID"],   # Wms_Mobile
        "username":  os.environ["WMS_USERNAME"],
        "password":  os.environ["WMS_PASSWORD"],
        "scope":     os.getenv("WMS_SCOPE", ""),
    }, verify=VERIFY_SSL, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    _token["value"] = data["access_token"]
    _token["expires_at"] = time.time() + data.get("expires_in", 3600)
    return _token["value"]

def call_wms(path, params=None):
    """GET only. The agent can never write through this."""
    params = {k: v for k, v in (params or {}).items() if v not in (None, "")}
    for attempt in range(2):
        headers = {"Authorization": f"Bearer {_get_token()}"}

        resp = requests.get(BASE_URL + path, headers=headers, params=params,
                            verify=VERIFY_SSL, timeout=30)
        if resp.status_code == 401 and attempt == 0:
            _token["value"] = None                  # expired, so get a new one and retry once
            continue
        resp.raise_for_status()
        return resp.json()

def pick(row, fields):
    """Keep only the fields the model needs."""
    return {f: row.get(f) for f in fields if f in row}