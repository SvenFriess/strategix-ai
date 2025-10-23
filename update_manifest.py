#!/usr/bin/env python3
import json, os, re, sys, datetime, pathlib
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent
CONTENT = ROOT / "content"
MANIFEST = CONTENT / "manifest.json"

class HeadParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title = None
        self.meta = {}

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "title":
            self.in_title = True
        if tag.lower() == "meta":
            d = dict(attrs)
            name = (d.get("name") or d.get("property") or "").lower()
            content = d.get("content") or ""
            if name:
                self.meta[name] = content

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title = (self.title or "") + data

def extract_head(html_text):
    m = re.search(r"<head[^>]*>(.*?)</head>", html_text, flags=re.S|re.I)
    return m.group(1) if m else html_text

def derive_item(path: pathlib.Path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    head = extract_head(text)
    p = HeadParser()
    p.feed(head)

    title = (p.title or path.stem).strip()
    raw_tags = p.meta.get("tags","").strip()
    tags = [t.strip() for t in re.split(r"[;,]", raw_tags) if t.strip()] if raw_tags else []
    if not tags:
        tags = [t for t in re.split(r"[_\-]", path.stem) if t and len(t) > 1][:3]

    dt = datetime.date.fromtimestamp(path.stat().st_mtime).isoformat()

    return {"title": title, "date": dt, "tags": tags, "file": path.name}

def main():
    if not CONTENT.exists():
        print(f"[ERR] content/ not found at {CONTENT}")
        sys.exit(1)

    items = []
    for f in sorted(CONTENT.glob("*.html")):
        if f.name.lower() == "index.html":
            continue
        items.append(derive_item(f))

    data = {"version": 1, "generated": datetime.date.today().isoformat(), "items": items}
    MANIFEST.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] Wrote {MANIFEST} with {len(items)} items.")
    for it in items:
        print(" -", it["title"], "->", it["file"], "|", ", ".join(it["tags"]))

if __name__ == "__main__":
    main()
