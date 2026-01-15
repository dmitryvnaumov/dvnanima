import xml.etree.ElementTree as ET
from pathlib import Path

def sanitize_svg(inp="cw.svg", out="cw_clean.svg"):
    # preserve namespaces
    tree = ET.parse(inp)
    root = tree.getroot()

    def is_path(tag):
        return tag.endswith("path")

    def bad_path(elem):
        if not is_path(elem.tag):
            return False
        d = elem.attrib.get("d")
        return (d is None) or (d.strip() == "")

    def hidden(elem):
        style = (elem.attrib.get("style") or "").replace(" ", "")
        disp = (elem.attrib.get("display") or "").strip()
        return ("display:none" in style) or (disp == "none")

    def clean(parent):
        for child in list(parent):
            if bad_path(child) or hidden(child):
                parent.remove(child)
            else:
                clean(child)

    clean(root)

    # also remove <use> that references nothing or empty href
    # (some exporters create broken <use>)
    def is_use(tag): return tag.endswith("use")
    def bad_use(elem):
        if not is_use(elem.tag): return False
        href = elem.attrib.get("{http://www.w3.org/1999/xlink}href") or elem.attrib.get("href")
        return (href is None) or (href.strip() == "")

    def clean_use(parent):
        for child in list(parent):
            if bad_use(child):
                parent.remove(child)
            else:
                clean_use(child)

    clean_use(root)

    tree.write(out)
    return out

if __name__ == "__main__":
    out = sanitize_svg()
    print("Wrote:", out)
    # quick check
    s = Path(out).read_text(encoding="utf-8", errors="ignore")
    print("paths total:", s.count("<path"))
    print("paths without d=:", s.count("<path") - s.count(" d="))
