#!/usr/bin/env python3
"""KISTI ScienceON OpenAPI client for scholar-megasearch (Bucket H).

Auth flow verified against the official KISTI token sample
(references/_vendor_kisti_token_sample/). Credentials come from env:
    KISTI_CLIENT_ID, KISTI_AUTH_KEY (=인증키, AES-256 key/32 bytes), KISTI_MAC
They may optionally be supplied via a .env file in the working directory
(python-dotenv is auto-loaded if installed; real shell env vars always win).
Never hardcode or commit secrets/tokens. A real .env must stay gitignored.
"""
import base64
import datetime
import json
import os
import re
from urllib.parse import quote

import requests

try:  # optional .env support; shell env always wins (override=False)
    from dotenv import load_dotenv as _load_dotenv
except ImportError:  # python-dotenv not installed -> .env files are ignored
    _load_dotenv = None


def load_env(path=None):
    """Best-effort load of KISTI_* vars from a .env file (optional).

    Requires python-dotenv. Shell/OS env vars are NOT overridden. Returns True
    if a .env was found and loaded, False otherwise (incl. dotenv not installed).
    SECURITY: never commit a real .env — it is gitignored.
    """
    if _load_dotenv is None:
        return False
    return bool(_load_dotenv(dotenv_path=path, override=False))


load_env()  # auto-load ./.env (searched from CWD upward) at import, if present


_AES_IV = "jvHJ1EFA0IXBrxxz"  # 고정값 (official sample)
_AES_BLOCK = 16
_TOKEN_URL = "https://apigateway.kisti.re.kr/tokenrequest.do"
_TOKEN_CACHE = {}  # client_id -> access_token (reused for process lifetime)


def _aes_encrypt(plain_txt, key):
    """AES-256-CBC + PKCS7 pad -> urlsafe base64 -> percent-encode (official scheme)."""
    from Crypto.Cipher import AES
    pad = _AES_BLOCK - len(plain_txt.encode("utf-8")) % _AES_BLOCK
    padded = plain_txt + chr(pad) * pad
    cipher = AES.new(key.encode("utf-8"), AES.MODE_CBC, _AES_IV.encode("utf-8"))
    enc = cipher.encrypt(padded.encode("utf-8"))
    return quote(base64.urlsafe_b64encode(enc).decode("utf-8"))


def _require_env():
    cid = os.environ.get("KISTI_CLIENT_ID")
    key = os.environ.get("KISTI_AUTH_KEY")
    mac = os.environ.get("KISTI_MAC")
    missing = [n for n, v in (("KISTI_CLIENT_ID", cid), ("KISTI_AUTH_KEY", key),
                              ("KISTI_MAC", mac)) if not v]
    if missing:
        raise RuntimeError("missing env: " + ", ".join(missing))
    return cid, key, mac


def get_access_token(force=False):
    """Issue (or reuse cached) an access token via tokenrequest.do."""
    cid, key, mac = _require_env()
    if len(key.encode("utf-8")) != 32:
        raise RuntimeError("KISTI_AUTH_KEY must be 32 bytes for AES-256 (got %d)" % len(key.encode("utf-8")))
    if not force and _TOKEN_CACHE.get(cid):
        return _TOKEN_CACHE[cid]
    now = "".join(re.findall(r"\d", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    plain = json.dumps({"datetime": now, "mac_address": mac}).replace(" ", "")
    accounts = _aes_encrypt(plain, key)
    url = f"{_TOKEN_URL}?client_id={cid}&accounts={accounts}"
    resp = requests.get(url, timeout=30)
    if resp.status_code != 200:
        # Do NOT include the URL (it carries client_id + encrypted accounts).
        raise RuntimeError(f"KISTI token request failed: HTTP {resp.status_code}")
    data = json.loads(resp.text)
    if "access_token" not in data:
        # KISTI returns 200 + error JSON for bad client_id / clock skew / IP block.
        raise RuntimeError(f"KISTI token request returned no access_token: {resp.text[:300]}")
    token = data["access_token"]
    _TOKEN_CACHE[cid] = token
    return token
