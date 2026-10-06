"""Builds the static inventory site from data/*.csv into site/. Standard library only."""
import csv, html, os, shutil, sys, datetime
from collections import defaultdict
E = html.escape
rd = lambda n: list(csv.DictReader(open(f"data/{n}.csv", encoding="utf-8-sig")))
loc, itm, stk = rd("locations"), rd("items"), rd("stock")
L = {r["location_id"].strip(): r for r in loc}
I = {r["item_id"].strip(): r for r in itm}
par = {k: r["parent_id"].strip() for k, r in L.items()}
kids, here, where = defaultdict(list), defaultdict(lambda: defaultdict(int)), defaultdict(lambda: defaultdict(int))
errs = []
for k, p in par.items():
    if p and p not in L: errs.append(f"locations: '{k}' has unknown parent '{p}'")
    kids[p].append(k)
for r in stk:
    l, i = r["location_id"].strip(), r["item_id"].strip()
    try: q = int(r["qty"])
    except ValueError: errs.append(f"stock: bad qty '{r['qty']}' for {l}/{i}"); continue
    if l not in L: errs.append(f"stock: unknown location '{l}'")
    elif i not in I: errs.append(f"stock: unknown item '{i}'")
    else: here[l][i] += q; where[i][l] += q
if errs: sys.exit("DATA ERRORS:\n" + "\n".join(errs))

def anc(l): return ([] if not par[l] else anc(par[l])) + [l]
def sub(l): return [l] + [x for c in kids[l] for x in sub(c)]
def units(l): return sum(sum(here[x].values()) for x in sub(l))
roots = kids[""]
total_units = sum(sum(h.values()) for h in here.values())

CSS = """body{font:16px/1.5 system-ui,sans-serif;margin:0;color:#1d2b2a;background:#fff}
main{max-width:60rem;margin:0 auto;padding:1rem}nav{background:#0f4c47;padding:.6rem 1rem}
nav a{color:#fff;margin-right:1.2rem;text-decoration:none;font-weight:600}a{color:#0f6b63}
.crumbs{font-size:.9rem;margin-bottom:.5rem;color:#555}h1{margin:.3rem 0 1rem}
table{border-collapse:collapse;width:100%;margin:.5rem 0 1.5rem}th,td{text-align:left;padding:.35rem .6rem;border-bottom:1px solid #dde5e3}
th{cursor:pointer;background:#eef4f3}input{font:inherit;padding:.4rem;width:100%;max-width:24rem;margin:.5rem 0}
details{margin-left:1rem}summary{cursor:pointer;padding:.1rem 0}ul{margin:.2rem 0 .2rem 1rem;padding-left:1rem}
.n{color:#666;font-size:.9rem}img{max-width:20rem;border-radius:4px}
.cl{columns:3;column-gap:1.2rem;font-size:8pt;line-height:1.25}.cl section{break-inside:avoid;margin-bottom:.5rem}
.cl h3{font-size:9pt;margin:0 0 .1rem;border-bottom:1px solid #000;break-after:avoid}.cl .r{display:flex;justify-content:space-between;gap:.4rem}
.cl .b{font-size:10pt;letter-spacing:0;text-align:right}.cl .c{color:#555}
@media print{@page{size:A4;margin:8mm}nav,.noprint{display:none}main{max-width:none;padding:0}h1{font-size:12pt;margin:0 0 .3rem}}
@media(max-width:700px){.cl{columns:1}}"""
JS = """document.querySelectorAll('th').forEach(h=>h.onclick=()=>{const t=h.closest('table'),i=h.cellIndex,b=t.tBodies[0],
d=h.dataset.d=h.dataset.d=='1'?'-1':'1';[...b.rows].sort((x,y)=>{const a=x.cells[i].textContent,c=y.cells[i].textContent,n=a-c;
return d*(isNaN(n)?a.localeCompare(c):n)}).forEach(r=>b.append(r))});
const q=document.getElementById('q');if(q)q.oninput=()=>document.querySelectorAll('tbody tr').forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q.value.toLowerCase()))"""

def page(path, title, body, crumbs=None):
    root = "../" * path.count("/")
    cr = f'<div class=crumbs>{" › ".join([f"<a href={root}index.html>Home</a>"] + crumbs)}</div>' if crumbs else ""
    nav = "".join(f'<a href="{root}{h}">{t}</a>' for h, t in [("index.html", "Home"), ("tree.html", "Tree"), ("summary.html", "Summary"), ("checklist.html", "Checklist")])
    os.makedirs(os.path.dirname(f"site/{path}") or "site", exist_ok=True)
    open(f"site/{path}", "w", encoding="utf-8").write(f'<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>{E(title)} – Lab inventory</title><style>{CSS}</style><nav>{nav}</nav><main>{cr}{body}</main><script>{JS}</script>')

la = lambda l, r: f'<a href="{r}locations/{l}/">{E(L[l]["name"])}</a>'
ia = lambda i, r: f'<a href="{r}items/{i}/">{E(I[i]["name"])}</a>'
crumb = lambda l, r, upto=None: [la(x, r) for x in anc(l)]
shutil.rmtree("site", ignore_errors=True)
if os.path.isdir("photos"): shutil.copytree("photos", "site/photos")

# landing
page("index.html", "Home", f"<h1>Lab inventory</h1><p>{len(I)} item types · {total_units} units · {len(L)} locations. Built {datetime.date.today()}.</p>"
     "<p><a href=tree.html>Browse the tree</a><br><a href=summary.html>Search items and counts</a><br><a href=checklist.html>Print the audit checklist</a></p>")

# tree
def node(l, r, op=False):
    items = "".join(f'<li>{ia(i, r)} <span class=n>×{q}</span></li>' for i, q in sorted(here[l].items(), key=lambda x: I[x[0]]["name"]))
    return f'<details{" open" if op else ""}><summary>{la(l, r)} <span class=n>({units(l)})</span></summary>' + (f"<ul>{items}</ul>" if items else "") + "".join(node(c, r) for c in kids[l]) + "</details>"
page("tree.html", "Tree", "<h1>Tree</h1>" + "".join(node(x, "", True) for x in roots))

# summary
rows = "".join(f'<tr><td>{ia(i, "")}</td><td>{E(I[i]["catalog_code"])}</td><td>{sum(w.values())}</td><td>{", ".join(la(l, "") + f" ({q})" for l, q in w.items())}</td></tr>' for i, w in sorted(where.items(), key=lambda x: I[x[0]]["name"].lower()))
lrows = "".join(f'<tr><td>{la(l, "")}</td><td>{sum(here[l].values())}</td><td>{units(l)}</td></tr>' for l in L)
page("summary.html", "Summary", f'<h1>Summary</h1><input id=q placeholder="Search items, codes, locations" class=noprint><table><thead><tr><th>Item<th>Code<th>Total<th>Where</tr></thead><tbody>{rows}</tbody></table>'
     f'<h2>Locations</h2><table><thead><tr><th>Location<th>Items here<th>Items incl. below</tr></thead><tbody>{lrows}</tbody></table>')

# location pages
for l in L:
    r = "../../"
    sl = "".join(f"<li>{la(c, r)} <span class=n>({units(c)})</span></li>" for c in kids[l])
    t = "".join(f'<tr><td>{ia(i, r)}</td><td>{q}</td><td>{la(x, r) if x != l else "here"}</td></tr>' for x in sub(l) for i, q in sorted(here[x].items(), key=lambda y: I[y[0]]["name"]))
    page(f"locations/{l}/index.html", L[l]["name"], f"<h1>{E(L[l]['name'])}</h1>" + (f"<h2>Inside</h2><ul>{sl}</ul>" if sl else "") +
         (f"<h2>Everything here and below ({units(l)})</h2><table><thead><tr><th>Item<th>Qty<th>Location</tr></thead><tbody>{t}</tbody></table>" if t else "<p>Nothing recorded here.</p>"), crumb(l, r)[:-1] + [E(L[l]["name"])])

# item pages
for i, it in I.items():
    r, w = "../../", where[i]
    ph = f'<p><img src="{r}photos/{E(it["photo"])}" alt=""></p>' if it["photo"].strip() else ""
    man = f'<p><a href="{E(it["manual_link"])}">Manual</a></p>' if it["manual_link"].strip() else ""
    meta = " · ".join(x for x in [f'Code {E(it["catalog_code"])}' if it["catalog_code"] else "", f'Serial {E(it["serial"])}' if it["serial"] else ""] if x)
    t = "".join(f'<tr><td>{" › ".join(la(x, r) for x in anc(l))}</td><td>{q}</td></tr>' for l, q in w.items())
    page(f"items/{i}/index.html", it["name"], f'<h1>{E(it["name"])}</h1>{ph}<p class=n>{meta}</p><p>{E(it["description"])}</p>{man}<h2>Total: {sum(w.values())}</h2><table><thead><tr><th>Location<th>Qty</tr></thead><tbody>{t}</tbody></table>', ['<a href="../../summary.html">Items</a>', E(it["name"])])

# checklist (A4 print): one box per unit, in groups of 5
box = lambda q: "".join("☐" + (" " if (k + 1) % 5 == 0 else "") for k in range(q))
def cl(l):
    h = " › ".join(L[x]["name"] for x in anc(l)[-2:])
    rs = "".join(f'<div class=r><span>{"<span class=c>"+E(I[i]["catalog_code"])+"</span> " if I[i]["catalog_code"] else ""}{E(I[i]["name"])}</span><span class=b>{box(q)}</span></div>' for i, q in sorted(here[l].items(), key=lambda x: I[x[0]]["name"]))
    own = f"<section><h3>{E(h)}</h3>{rs or ('' if kids[l] else '<div class=c>empty</div>')}</section>" if rs or not kids[l] else ""
    return own + "".join(cl(c) for c in kids[l])
page("checklist.html", "Checklist", f'<h1>Audit checklist · {datetime.date.today()} · {total_units} units</h1><p class=noprint>Print on A4 (Ctrl+P). Tick one box per unit found.</p><div class=cl>{"".join(cl(x) for x in roots)}</div>')
print(f"Built {len(L)} locations, {len(I)} items, {total_units} units.")
