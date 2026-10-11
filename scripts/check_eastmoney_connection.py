
import requests

URL = "https://82.push2.eastmoney.com/"

def check(name: str, session: requests.Session) -> None:
    try:
        response = session.get(URL, timeout=10)
        print(f"{name}: HTTP {response.status_code}")
    except requests.RequestException as exc:
        # 不输出完整 URL 或代理凭据
        print(f"{name}: {type(exc).__name__}: {exc.__class__.__name__}")

default_session = requests.Session()
direct_session = requests.Session()
direct_session.trust_env = False

check("Default network", default_session)
check("Without environment proxy", direct_session)
