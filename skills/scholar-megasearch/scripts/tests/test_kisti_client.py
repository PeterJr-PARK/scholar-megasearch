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
    resp = mock.Mock(); resp.status_code = 200; resp.text = json.dumps(tok)
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


def test_aes_encrypt_matches_official_sample():
    import importlib.util
    vpath = os.path.join(_here, "..", "..", "references",
                         "_vendor_kisti_token_sample", "AES256Util.py")
    vs = importlib.util.spec_from_file_location("aes256util", vpath)
    vmod = importlib.util.module_from_spec(vs); vs.loader.exec_module(vmod)
    plain = '{"datetime":"20260630170000","mac_address":"AA-BB"}'
    key = "01234567890123456789012345678901"
    expected = vmod.AESTestClass(plain, key).encrypt()
    assert kc._aes_encrypt(plain, key) == expected


def test_token_cache_reuses_then_force_refetches():
    resp = mock.Mock(); resp.status_code = 200
    resp.text = json.dumps({"access_token": "T1"})
    with mock.patch.object(kc.requests, "get", return_value=resp) as g, \
         mock.patch.dict(os.environ, {"KISTI_CLIENT_ID": "cid",
                                      "KISTI_AUTH_KEY": "01234567890123456789012345678901",
                                      "KISTI_MAC": "AA-BB-CC"}):
        kc._TOKEN_CACHE.clear()
        assert kc.get_access_token() == "T1"
        assert kc.get_access_token() == "T1"
        assert g.call_count == 1            # second call served from cache
        kc.get_access_token(force=True)
        assert g.call_count == 2            # force bypasses cache


def test_load_env_reads_dotenv_and_shell_wins(tmp_path):
    if importlib.util.find_spec("dotenv") is None:
        import pytest; pytest.skip("python-dotenv not installed")
    envf = tmp_path / ".env"
    envf.write_text("KISTI_CLIENT_ID=fromdotenv\nKISTI_MAC=DD-EE-FF\n", encoding="utf-8")
    for k in ("KISTI_CLIENT_ID", "KISTI_MAC"):
        os.environ.pop(k, None)
    try:
        # .env populates missing vars
        assert kc.load_env(str(envf)) is True
        assert os.environ["KISTI_CLIENT_ID"] == "fromdotenv"
        # existing shell env always wins (override=False)
        os.environ["KISTI_CLIENT_ID"] = "fromshell"
        kc.load_env(str(envf))
        assert os.environ["KISTI_CLIENT_ID"] == "fromshell"
    finally:
        for k in ("KISTI_CLIENT_ID", "KISTI_MAC"):
            os.environ.pop(k, None)
