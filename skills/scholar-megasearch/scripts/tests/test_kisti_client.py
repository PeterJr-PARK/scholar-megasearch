import importlib.util, json, os
from unittest import mock

_here = os.path.dirname(__file__)
_spec = importlib.util.spec_from_file_location(
    "kisti_client", os.path.join(_here, "..", "kisti_client.py"))
kc = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(kc)

FIX = os.path.join(_here, "fixtures")


def test_aes_encrypt_is_url_safe_and_nonempty():
    enc = kc._aes_encrypt('{"datetime":"20260630170000","mac_address":"AA-BB"}',
                          "01234567890123456789012345678901")
    assert enc and "/" not in enc and "+" not in enc


def test_get_access_token_parses_response():
    tok = json.load(open(os.path.join(FIX, "kisti_token_sample.json"), encoding="utf-8"))
    tok["access_token"] = "ACCESS123"
    resp = mock.Mock(); resp.text = json.dumps(tok); resp.raise_for_status = lambda: None
    with mock.patch.object(kc.requests, "get", return_value=resp) as g, \
         mock.patch.dict(os.environ, {"KISTI_CLIENT_ID": "cid",
                                      "KISTI_AUTH_KEY": "01234567890123456789012345678901",
                                      "KISTI_MAC": "AA-BB-CC"}):
        kc._TOKEN_CACHE.clear()
        assert kc.get_access_token() == "ACCESS123"
        url = g.call_args[0][0]
        assert "tokenrequest.do" in url and "client_id=cid" in url and "accounts=" in url


def test_get_access_token_requires_env():
    with mock.patch.dict(os.environ, {}, clear=True):
        kc._TOKEN_CACHE.clear()
        try:
            kc.get_access_token(); assert False, "expected RuntimeError"
        except RuntimeError as e:
            assert "KISTI_" in str(e)
