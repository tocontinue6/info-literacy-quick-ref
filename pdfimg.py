import sys, os, glob
sys.path.insert(0, "libs")
from pypdf import PdfReader

os.makedirs("out/pdf_pages", exist_ok=True)
targets = {
    "pdf/scu-ai-tool-regulation-2025.pdf": [0, 1],
    "pdf/文后参考文献著录规则（GB T 7714— 2025）.pdf": [0, 1, 2],
}
for path, pages in targets.items():
    name = os.path.splitext(os.path.basename(path))[0]
    try:
        r = PdfReader(path)
    except Exception as e:
        print("open fail", path, e); continue
    for pno in pages:
        try:
            page = r.pages[pno]
            imgs = list(page.images)
            print(f"{name} page{pno+1}: {len(imgs)} images")
            for i, im in enumerate(imgs[:2]):
                ext = os.path.splitext(im.name)[1] or ".png"
                dest = f"out/pdf_pages/{name}_p{pno+1}_{i+1}{ext}"
                with open(dest, "wb") as f:
                    f.write(im.data)
                print("   wrote", dest, len(im.data))
        except Exception as e:
            print(f"{name} page{pno+1} FAIL {type(e).__name__}: {e}")
