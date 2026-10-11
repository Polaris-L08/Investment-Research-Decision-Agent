import requests

URLS = {
    "Eastmoney": "https://82.push2.eastmoney.com/",
    "Baidu": "https://www.baidu.com/",
    "Sina Finance": "https://finance.sina.com.cn/",
}

for name, url in URLS.items():
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        print(f"{name}: HTTP {response.status_code}")
    except requests.RequestException as exc:
        print(f"{name}: {type(exc).__name__}: {exc}")