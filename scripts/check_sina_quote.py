import requests

url = "https://hq.sinajs.cn/list=sh600000"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://finance.sina.com.cn/",
}

try:
    response = requests.get(
        url,
        headers=headers,
        timeout=10,
    )

    print("HTTP status:", response.status_code)
    print("Response:", response.text[:500])
    response.raise_for_status()

except requests.RequestException as exc:
    print("Request failed:", type(exc).__name__, str(exc))