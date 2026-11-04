"""Minimal stdlib xlsx reader: sheets -> list of rows (strings/floats)."""
import re, sys, zipfile, xml.etree.ElementTree as ET
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
def col(ref):
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group():
        n = n * 26 + ord(ch) - 64
    return n - 1
def read(path):
    z = zipfile.ZipFile(path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
            shared.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rid = {r.get("Id"): r.get("Target") for r in rels}
    out = {}
    for s in wb.find("m:sheets", NS):
        target = rid[s.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")]
        target = target.lstrip("/")
        if not target.startswith("xl/"): target = "xl/" + target
        rows = []
        for r in ET.fromstring(z.read(target)).iter("{%s}row" % NS["m"]):
            row = {}
            for c in r.findall("m:c", NS):
                v = c.find("m:v", NS); t = c.get("t")
                if v is None:
                    isel = c.find("m:is", NS)
                    val = "".join(x.text or "" for x in isel.iter("{%s}t" % NS["m"])) if isel is not None else None
                elif t == "s": val = shared[int(v.text)]
                else:
                    try: val = float(v.text)
                    except ValueError: val = v.text
                row[col(c.get("r"))] = val
            rows.append([row.get(i) for i in range(max(row) + 1)] if row else [])
        out[s.get("name")] = rows
    return out
if __name__ == "__main__":
    for name, rows in read(sys.argv[1]).items():
        print(f"## sheet {name!r}: {len(rows)} rows")
        for r in rows[: int(sys.argv[2]) if len(sys.argv) > 2 else 6]: print("  ", r[:30])
