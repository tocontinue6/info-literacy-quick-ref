import sys, os, json, glob, re
sys.path.insert(0, "libs")
from pypdf import PdfReader

os.makedirs("out/pdf_text", exist_ok=True)
meta = {}
for p in sorted(glob.glob("pdf/*.pdf")):
    name = os.path.basename(p)
    try:
        r = PdfReader(p)
        info = {}
        try:
            info = dict(r.metadata or {})
        except Exception:
            pass
        pages = len(r.pages)
        texts = []
        limit = min(pages, 25)
        for i in range(limit):
            try:
                texts.append(f"\n--- [page {i+1}] ---\n" + (r.pages[i].extract_text() or ""))
            except Exception as e:
                texts.append(f"\n--- [page {i+1}] EXTRACT ERROR {e}\n")
        full = "".join(texts)
        full = re.sub(r"[ \t]+\n", "\n", full)
        with open(f"out/pdf_text/{name}.txt", "w", encoding="utf-8") as f:
            f.write(f"FILE: {name}\nSIZE: {os.path.getsize(p)} bytes\nPAGES: {pages}\nMETADATA: {json.dumps(info, ensure_ascii=False, default=str)}\n")
            f.write("=" * 70 + "\n")
            f.write(full)
        meta[name] = {"path": p, "pages": pages, "bytes": os.path.getsize(p),
                      "metadata": {k: str(v) for k, v in info.items()},
                      "chars_extracted": len(full), "pages_parsed": limit}
        print(f"OK {name}: pages={pages} chars={len(full)}")
    except Exception as e:
        meta[name] = {"path": p, "error": f"{type(e).__name__}: {e}"}
        print(f"FAIL {name}: {type(e).__name__}: {e}")

json.dump(meta, open("out/pdf_meta.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
