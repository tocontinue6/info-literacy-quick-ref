import re, sys

path = sys.argv[1]
pat = sys.argv[2]
width = int(sys.argv[3]) if len(sys.argv) > 3 else 160
limit = int(sys.argv[4]) if len(sys.argv) > 4 else 40

data = open(path, encoding="utf-8", errors="replace").read()
rx = re.compile(pat)
n = 0
for m in rx.finditer(data):
    n += 1
    if n > limit:
        print(f"... more than {limit} matches, stopping")
        break
    s = max(0, m.start() - width)
    e = min(len(data), m.end() + width)
    print(f"[{m.start()}] ...{data[s:e]}...")
    print("-" * 100)
print(f"TOTAL MATCHES: {n}")
