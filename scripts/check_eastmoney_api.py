
import requests

URL = "https://82.push2.eastmoney.com/api/qt/clist/get"

PARAMS = {
    "pn": "1",
    "pz": "1",
    "po": "1",
    "np": "1",
    "ut": "bd1d9ddb04089700cf9c27f6f7426281",
    "fltt": "2",
    "invt": "2",
    "fid": "f12",
    "fs": "m:0 t:6",
    "fields": "f1,f2,f12,f14",
}

def test_connection(name: str, trust_env: bool) -> None:
    session = requests.Session()
    session.trust_env = trust_env

    try:
        response = session.get(
            URL,
            params=PARAMS,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        print(f"{name}: HTTP {response.status_code}")
        print("Response:", response.text[:300])
    except requests.RequestException as exc:
        # 不输出代理地址或凭据
        print(f"{name}: {type(exc).__name__}")
        print("Details:", str(exc).split("HTTPSConnectionPool")[0][:200])
    finally:
        session.close()

test_connection("Default", True)
test_connection("Without environment proxy", False)
