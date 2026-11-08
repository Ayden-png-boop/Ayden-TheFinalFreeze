"""GitHub 设备码登录（可重试版，纯标准库）

gh auth login 只有一次机会：POST 抖一次就整轮作废、码也失效。
这里自己走 device flow，轮询阶段遇到网络错误只是重试，同一个码一直有效。

用法：python gh_device_login.py
成功后把 token 写到 _gh_token.txt。
"""
import json
import os
import ssl
import time
import urllib.parse
import urllib.request

CLIENT_ID = "178c6fc778ccc68e1d6a"  # GitHub CLI 官方 OAuth App（公开 client_id）
SCOPE = "repo workflow read:org"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "_gh_token.txt")

_ctx = ssl.create_default_context()
_opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({}),          # 明确不走代理
    urllib.request.HTTPSHandler(context=_ctx),
)


def post(url, data, tries=8):
    body = urllib.parse.urlencode(data).encode()
    last = None
    for i in range(tries):
        req = urllib.request.Request(
            url, data=body,
            headers={"Accept": "application/json",
                     "Content-Type": "application/x-www-form-urlencoded"})
        try:
            with _opener.open(req, timeout=25) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            last = e
            time.sleep(2 + i * 2)
    raise RuntimeError(f"POST {url} failed: {last}")


def main():
    d = post("https://github.com/login/device/code",
             {"client_id": CLIENT_ID, "scope": SCOPE})
    if "device_code" not in d:
        print("DEVICE_CODE_FAILED", json.dumps(d)[:200], flush=True)
        return
    print(f"USER_CODE={d['user_code']}", flush=True)
    print(f"VERIFY_URL={d['verification_uri']}", flush=True)
    print(f"EXPIRES_IN={d['expires_in']}s", flush=True)

    interval = max(5, int(d.get("interval", 5)))
    deadline = time.time() + int(d["expires_in"]) - 10
    while time.time() < deadline:
        time.sleep(interval)
        try:
            body = urllib.parse.urlencode({
                "client_id": CLIENT_ID,
                "device_code": d["device_code"],
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            }).encode()
            req = urllib.request.Request(
                "https://github.com/login/oauth/access_token", data=body,
                headers={"Accept": "application/json",
                         "Content-Type": "application/x-www-form-urlencoded"})
            with _opener.open(req, timeout=25) as r:
                j = json.loads(r.read().decode())
        except Exception as e:
            print(f"poll retry: {type(e).__name__}", flush=True)
            continue

        err = j.get("error")
        if err == "authorization_pending":
            continue
        if err == "slow_down":
            interval += 5
            continue
        if err == "expired_token":
            print("EXPIRED", flush=True)
            return
        if err == "access_denied":
            print("DENIED", flush=True)
            return
        tok = j.get("access_token")
        if tok:
            with open(OUT, "w", encoding="utf-8") as f:
                f.write(tok.strip())
            print("TOKEN_SAVED", OUT, flush=True)
            return
        print("UNKNOWN", json.dumps(j)[:200], flush=True)
        return
    print("TIMEOUT", flush=True)


if __name__ == "__main__":
    main()
