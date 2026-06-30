#!/usr/bin/env python3
"""KISTI ScienceON OpenAPI client for scholar-megasearch (Bucket H).

Auth flow verified against the official KISTI token sample
(references/_vendor_kisti_token_sample/). Credentials come ONLY from env:
    KISTI_CLIENT_ID, KISTI_AUTH_KEY (=인증키, AES-256 key/32 bytes), KISTI_MAC
Never hardcode or commit secrets/tokens.
"""
import base64
import datetime
import json
import os
import re
from urllib.parse import quote

import requests

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
    if not force and _TOKEN_CACHE.get(cid):
        return _TOKEN_CACHE[cid]
    now = "".join(re.findall(r"\d", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    plain = json.dumps({"datetime": now, "mac_address": mac}).replace(" ", "")
    accounts = _aes_encrypt(plain, key)
    url = f"{_TOKEN_URL}?client_id={cid}&accounts={accounts}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    token = json.loads(resp.text)["access_token"]
    _TOKEN_CACHE[cid] = token
    return token
