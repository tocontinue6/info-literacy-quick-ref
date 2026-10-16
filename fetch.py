"""Polite fetch helper: downloads a URL to a file or returns text."""
import sys, os, json, time, urllib.request, urllib.error, ssl

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def req(url, method="GET", data=None, headers=None, timeout=45):
    h = {"User-Agent": UA, "Accept": "*/*", "Accept-Language": "zh-CN,zh;q=0.9"}
    if headers:
        h.update(headers)
    body = None
    if data is not None:
        body = json.dumps(data).encode() if not isinstance(data, (bytes, str)) else (
            data.encode() if isinstance(data, str) else data)
        h.setdefault("Content-Type", "application/json")
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    with urllib.request.urlopen(r, timeout=timeout, context=CTX) as resp:
        return resp.status, dict(resp.headers), resp.read()


def main():
    cmd = sys.argv[1]
    url = sys.argv[2]
    if cmd == "save":
        out = sys.argv[3]
        try:
            st, hd, b = req(url)
            with open(out, "wb") as f:
                f.write(b)
            print(f"OK {st} {len(b)} -> {out}")
        except urllib.error.HTTPError as e:
            print(f"HTTPError {e.code} for {url}")
        except Exception as e:
            print(f"ERROR {type(e).__name__} {e} for {url}")
    elif cmd == "text":
        out = sys.argv[3] if len(sys.argv) > 3 else None
        try:
            st, hd, b = req(url)
            txt = b.decode("utf-8", "replace")
            if out:
                with open(out, "w", encoding="utf-8") as f:
                    f.write(txt)
                print(f"OK {st} {len(b)} -> {out}")
            else:
                sys.stdout.buffer.write(b)
        except Exception as e:
            print(f"ERROR {type(e).__name__} {e} for {url}")
    elif cmd == "json":
        # POST json: fetch.py json <url> <json-body-file> <out>
        with open(sys.argv[3], encoding="utf-8") as f:
            payload = json.load(f)
        try:
            st, hd, b = req(url, method="POST", data=payload)
            with open(sys.argv[4], "wb") as f:
                f.write(b)
            print(f"OK {st} {len(b)} -> {sys.argv[4]}")
        except urllib.error.HTTPError as e:
            print(f"HTTPError {e.code}: {e.read()[:500]!r}")
        except Exception as e:
            print(f"ERROR {type(e).__name__} {e}")


if __name__ == "__main__":
    main()
