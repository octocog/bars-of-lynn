#!/usr/bin/env python3
"""Build the Bars of Lynn site from transcript.md + bars.json.

Everything on the site is generated. Edit the transcript or the JSON and rerun;
never hand edit site/.
"""
import json, os, re, shutil, html
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "docs")   # GitHub Pages serves from /docs
BARS = json.load(open(os.path.join(HERE, "bars.json"), encoding="utf-8"))
TRANSCRIPT = open(os.path.join(HERE, "transcript.md"), encoding="utf-8").read()

NIGHTS = {}
for n, b in BARS.items():
    NIGHTS.setdefault(b["date"], []).append(int(n))
for d in NIGHTS: NIGHTS[d].sort()
NIGHT_ORDER = sorted(NIGHTS)

MONTH = {"08": "August", "09": "September"}
def pretty_date(iso):
    y, m, d = iso.split("-")
    return f"{int(d)} {MONTH[m]} {y}"

# ---------------------------------------------------------------- transcript
def entry_text(num):
    """Pull the transcribed body for a bar out of transcript.md."""
    b = BARS[str(num)]
    if not b["pages"]: return None, []
    blocks, notes = [], []
    for pg in b["pages"]:
        m = re.search(rf"^## Page {pg} — .*?$(.*?)(?=^---\s*$)", TRANSCRIPT,
                      re.M | re.S)
        if not m: continue
        body = m.group(1)
        # editorial blockquotes become notes, not body text
        for q in re.findall(r"^> (.*(?:\n> .*)*)", body, re.M):
            notes.append(re.sub(r"^> ?", "", q, flags=re.M).strip())
        body = re.sub(r"^> .*$", "", body, flags=re.M)
        # strip the sub heading line if present
        body = re.sub(r"^### .*$", "", body, flags=re.M)
        blocks.append(body.strip())
    return "\n\n".join(x for x in blocks if x), notes

def render_body(txt):
    """Typewriter text: keep line breaks, lift the [*photo*] captions out."""
    out = []
    for para in re.split(r"\n\s*\n", txt):
        para = para.strip()
        if not para: continue
        cap = re.match(r"^\[\*(.*)\*\]$", para, re.S)
        if cap:
            t = inline(cap.group(1).strip())
            out.append(f'<p class="plate-cap">{t}</p>')
        else:
            out.append(f'<p class="typed">{inline(para)}</p>')
    return "\n".join(out)

def inline(t, reflow=None):
    """reflow=None means decide automatically.

    The original is typewritten, so most line breaks are just where the carriage
    returned. Those are reflowed, because the scan beside the text carries the real
    lineation. Breaks that mean something, dialogue, centred signs, indented blocks,
    are kept.
    """
    t = html.escape(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t, flags=re.S)
    t = re.sub(r"\*(.+?)\*", r"<i>\1</i>", t, flags=re.S)
    lines = t.split("\n")
    if reflow is None:
        reflow = is_wrapped(lines)
    if reflow:
        return " ".join(x.strip() for x in lines if x.strip())
    return "<br>\n".join(lines)

def is_wrapped(lines):
    """True when the breaks look like a typewriter margin rather than intent."""
    body = [l for l in lines if l.strip()]
    if len(body) < 2: return True
    if any(re.match(r"^\s{2,}\S", l) for l in body): return False      # indented block
    if any(re.match(r"^(THEM|US)\s*:", l.strip()) for l in body): return False
    if any(l.strip().startswith(("\u201c", '"')) and len(l.strip()) < 55 for l in body): return False
    longest = max(len(l.rstrip()) for l in body)
    shortish = [l for l in body[:-1] if len(l.rstrip()) < longest * 0.72]
    return len(shortish) == 0

# ---------------------------------------------------------------- page shell
def shell(title, body, depth=0, desc="", cls=""):
    up = "../" * depth
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Anton&family=Courier+Prime:ital,wght@0,400;0,700;1,400&display=swap">
<link rel="stylesheet" href="{up}assets/style.css">
</head>
<body class="{cls}">
<a class="skip" href="#main">Skip to content</a>
<header class="masthead">
  <a class="wordmark" href="{up}index.html">THE BARS OF LYNN</a>
  <nav>
    <a href="{up}index.html">The&nbsp;Forty</a>
    <a href="{up}nights/index.html">The&nbsp;Nights</a>
    <a href="{up}about/index.html">About</a>
  </nav>
</header>
<main id="main">
{body}
</main>
<footer class="foot">
  <p><b>A Field Study</b>, by James Francis Murnane II and Grant Arthur Albert.
  Typed by Fran. Lynn, Massachusetts, August to December 1986.</p>
  <p>Reproduced as typed. Nothing corrected, nothing cut.
  <a href="{up}about/index.html#note">Why</a>.</p>
</footer>
</body>
</html>
"""

def badge(b):
    s = b["status"]
    label = {"open": "Still open", "closed": "Closed", "demolished": "Demolished",
             "possibly open": "Possibly open", "unknown": "Fate unknown"}[s]
    return f'<span class="badge b-{s.replace(" ","-")}">{label}</span>'

# ---------------------------------------------------------------- index
def build_index():
    rows = []
    for n in range(1, 41):
        b = BARS[str(n)]
        addr = b.get("address") or b.get("addr_guess") or ""
        acls = "known" if b.get("address") else ("guess" if addr else "none")
        if not addr: addr = "—"
        miss = ' <span class="miss">no entry</span>' if b.get("missing") else ""
        href = f'bars/{b["slug"]}.html'
        rows.append(f"""<a class="row" href="{href}">
  <span class="num">{n:02d}</span>
  <span class="nm">{html.escape(b["name"])}{miss}</span>
  <span class="dt">{pretty_date(b["date"])}</span>
  <span class="ad {acls}">{html.escape(addr)}</span>
  <span class="st">{badge(b)}</span>
</a>""")
    open_n = sum(1 for b in BARS.values() if b["status"] in ("open", "possibly open"))
    known = sum(1 for b in BARS.values() if b.get("address"))
    body = f"""
<section class="hero">
  <p class="kicker">Lynn, Massachusetts &middot; August to September 1986</p>
  <h1>Forty bars,<br>eleven nights,<br>two engineers.</h1>
  <p class="lede">In the summer of 1986 two engineers at General Electric in Lynn
  set out to drink in every bar in the city and write down what they found. They
  typed it up, bound it, and it was lost for thirty years until a photocopy
  surfaced in a desk drawer.</p>
  <blockquote class="thesis">
    <p>So, why'd we bother? Why'd we do it? Who cares? We each have our own reasons:</p>
    <p class="q">&ldquo;Because it's beer.&rdquo; &mdash; Grant.<br>
       &ldquo;I can't remember.&rdquo; &mdash; Jim.</p>
    <p><b>One thing we both want to know is why anyone would read it.</b></p>
    <cite>Afterword, 15 December 1986</cite>
  </blockquote>
  <p class="answer">This is the answer, forty years late.</p>
</section>

<section class="stats">
  <div><b>40</b><span>bars visited</span></div>
  <div><b>11</b><span>nights</span></div>
  <div><b>{open_n}</b><span>still open today</span></div>
  <div><b>{known}</b><span>addresses confirmed</span></div>
</section>

<section class="list">
  <h2>The forty, in the order they drank them</h2>
  <div class="legend">
    <span class="ad known">confirmed address</span>
    <span class="ad guess">best guess</span>
    <span class="ad none">not yet found</span>
  </div>
  <div class="table">
    <div class="row head"><span class="num">#</span><span class="nm">Bar</span>
      <span class="dt">Visited</span><span class="ad">Address</span><span class="st">Fate</span></div>
    {"".join(rows)}
  </div>
</section>
"""
    return shell("The Bars of Lynn", body, 0,
                 "A 1986 field study of forty bars in Lynn, Massachusetts, reproduced in full.",
                 "home")

# ---------------------------------------------------------------- bar pages
def build_bar(n):
    b = BARS[str(n)]
    txt, notes = entry_text(n)
    prev_, next_ = BARS.get(str(n-1)), BARS.get(str(n+1))

    if txt:
        main = f'<div class="entry">{render_body(txt)}</div>'
    else:
        main = """<div class="entry missing">
      <p class="typed">This bar appears in the index of the original document, but no
      entry for it survives. The pages run straight from number 26 to number 28. Either
      it was never written up, or a page is missing from the photocopy.</p></div>"""

    scans = "".join(
        f'<figure class="scan"><img loading="lazy" src="../assets/scans/page-{p:02d}.jpg"'
        f' alt="Page {p} of the original typescript"><figcaption>Original page {p}</figcaption></figure>'
        for p in b["pages"])

    def fact(label, val, cls=""):
        return f'<div class="fact {cls}"><dt>{label}</dt><dd>{val}</dd></div>' if val else ""

    addr = b.get("address")
    if addr:
        a = f'{html.escape(addr)} <span class="conf c-{b["addr_conf"]}">{b["addr_conf"]}</span>'
        if b.get("addr_why"): a += f'<p class="why">{html.escape(b["addr_why"])}</p>'
    elif b.get("addr_guess"):
        a = f'<span class="guessy">{html.escape(b["addr_guess"])}</span><p class="why">Best guess. Not confirmed.</p>'
    else:
        a = '<span class="guessy">Not yet found. The 1986 Lynn directory is not online.</span>'

    nowv = html.escape(b["now"]) if b.get("now") else None
    if nowv and b.get("now_conf"):
        nowv += f' <span class="conf c-{b["now_conf"]}">{b["now_conf"]}</span>'

    facts = "".join([
        fact("Visited", pretty_date(b["date"])),
        fact("1986 address", a),
        fact("Fate", badge(b)),
        fact("There now", nowv),
        fact("Also known as", html.escape(b["former"])) if b.get("former") else "",
        fact("Listed in the index as", html.escape(b["indexed"])) if b.get("indexed") else "",
        fact("Note", html.escape(b["note"])) if b.get("note") else "",
    ])
    notes_html = "".join(f'<li>{inline(x)}</li>' for x in notes)
    notes_block = f'<div class="editorial"><h3>Reading notes</h3><ul>{notes_html}</ul></div>' if notes_html else ""

    nav = '<nav class="pager">'
    nav += f'<a href="{prev_["slug"]}.html">&larr; {html.escape(prev_["name"])}</a>' if prev_ else '<span></span>'
    nav += f'<a href="{next_["slug"]}.html">{html.escape(next_["name"])} &rarr;</a>' if next_ else '<span></span>'
    nav += '</nav>'

    star = '<span class="star" title="Awarded the Gold Star">&#9733; Gold Star</span>' if b.get("gold_star") else ""

    body = f"""
<article class="bar">
  <header class="bar-head">
    <p class="kicker"><a href="../nights/index.html#{b['date']}">Night of {pretty_date(b['date'])}</a></p>
    <h1><span class="bignum">{n:02d}</span> {html.escape(b['name'])}</h1>
    {star}
  </header>
  <div class="two">
    <div class="col-text">
      {main}
      {notes_block}
    </div>
    <aside class="col-facts">
      <dl class="facts">{facts}</dl>
      {scans}
    </aside>
  </div>
  {nav}
</article>
"""
    return shell(f"{b['name']} — The Bars of Lynn", body, 1,
                 f"{b['name']}, visited {pretty_date(b['date'])} during a 1986 field study of forty Lynn bars.")

# ---------------------------------------------------------------- nights
def build_nights():
    secs = []
    for d in NIGHT_ORDER:
        nums = NIGHTS[d]
        stops = "".join(
            f'<li><a href="../bars/{BARS[str(n)]["slug"]}.html">'
            f'<span class="num">{n:02d}</span> {html.escape(BARS[str(n)]["name"])}</a></li>'
            for n in nums)
        secs.append(f"""<section class="night" id="{d}">
  <h2>{pretty_date(d)}</h2>
  <p class="count">{len(nums)} bar{"s" if len(nums)>1 else ""}</p>
  <ol class="route">{stops}</ol>
</section>""")
    body = f"""
<section class="pagehead">
  <p class="kicker">The route</p>
  <h1>Eleven nights</h1>
  <p class="lede">They did not do forty bars in forty nights. They did forty bars in
  eleven, between 2 August and 12 September 1986, with a fortnight off in the middle.
  Bars visited on the same night were usually within walking distance of each other,
  which is the best tool we have for placing the ones whose addresses are still lost.</p>
  <blockquote class="thesis small">
    <p>The lapse between 8.25.86 and 9.8.86 was due to an all-star break (vacation)
    and does not reflect a lack of professionalism on anyone's part.</p>
    <cite>Footnote to the index</cite>
  </blockquote>
</section>
<div class="nights">{"".join(secs)}</div>
"""
    return shell("The Nights — The Bars of Lynn", body, 1,
                 "The eleven nights of the 1986 Lynn bar survey, in order.")

# ---------------------------------------------------------------- about
def build_about():
    body = """
<section class="pagehead">
  <p class="kicker">About</p>
  <h1>What this is</h1>
</section>
<div class="prose">
  <p>In the summer of 1986, two engineers at the General Electric plant in Lynn,
  Massachusetts set out to visit every bar in the city. They managed forty of them
  across eleven nights between 2 August and 12 September, photographed most of them,
  and wrote the whole thing up as a mock academic paper.</p>

  <p>The title page credits <b>James Francis Murnane II, Professor Sclerosis, Mastoid
  Institute of Technology</b> and <b>Grant Arthur Albert, Doctorae un Urinal,
  University of Canned Light Alcohol</b>. The afterword thanks <b>Fran</b>, who
  &ldquo;translated handwritten doggrel into typewritten text&rdquo;. She typed all
  forty five pages.</p>

  <p>It was never published and never meant to be. A photocopy surfaced in a desk
  drawer and was passed on. This site reproduces it in full.</p>

  <h2>Why it matters more than it looks</h2>
  <p>Lynn in 1986 was a city of about seventy eight thousand people in the middle of a
  long industrial decline, and it supported at least forty bars. Many of them were
  shift bars within walking distance of the GE gates. Read as a comic pub crawl it is
  very funny. Read as a record it is a street level account of a working city in the
  year its work was going away.</p>

  <p>The authors knew this, in their way:</p>
  <blockquote class="thesis">
    <p>It is, at best, a moment frozen (well, most of 'em are frozen - the Shawmut's
    petrified). In time, years from now, some will surely have drained the last key and
    rolled on to that great empty keg in the sky or have been remodelled to suit the
    latest fashion.</p>
    <cite>Afterword, 15 December 1986</cite>
  </blockquote>
  <p>They were right. Most are gone. Four are still pouring.</p>

  <h2 id="note">A note on the text</h2>
  <p>Everything here is reproduced as it was typed in 1986. Spelling, punctuation and
  typing errors are left alone. So is the language, some of which belongs to its moment
  and to two men writing for an audience of each other, and would not be written that
  way now.</p>
  <p>Nothing has been corrected, softened or cut. An archive that quietly edits its own
  source is worth less than no archive at all, and a reader in another forty years
  should be able to see what was actually on the page.</p>
  <p>The photographs are reproduced from the same photocopy, at whatever quality the
  Xerox left them.</p>

  <h2>What is still missing</h2>
  <p>The addresses. The original names only the bars, never the streets, and the 1986
  Lynn city directory has not been digitised anywhere reachable. A handful of addresses
  are stated in the text or have been documented since. The rest are marked as guesses
  or left blank, and they will stay that way until somebody opens the physical directory
  at Lynn Public Library.</p>
  <p>Also missing: <b>number 27, The Arena</b>. It is in the index and has no entry.</p>

  <h2>Contributions</h2>
  <p>The authors asked for them:</p>
  <blockquote class="thesis">
    <p>It is not a complete work, rather we liken it to a watershed work designed to
    encourage the reader to his or her own contributions to the literature.</p>
  </blockquote>
  <p>If you drank in any of these, worked in them, or know where they were, that is
  exactly what this needs.</p>
</div>
"""
    return shell("About — The Bars of Lynn", body, 1,
                 "A 1986 field study of forty Lynn bars, how it survived, and how it is reproduced here.")

# ---------------------------------------------------------------- write
def main():
    if os.path.isdir(SITE): shutil.rmtree(SITE)
    for d in ("", "bars", "nights", "about", "assets", "assets/scans"):
        os.makedirs(os.path.join(SITE, d), exist_ok=True)

    shutil.copy(os.path.join(HERE, "assets_style.css"),
                os.path.join(SITE, "assets", "style.css"))
    used = sorted({p for b in BARS.values() for p in b["pages"]})
    for p in used:
        src = os.path.join(HERE, "scans_web", f"page-{p:02d}.jpg")
        if os.path.exists(src):
            shutil.copy(src, os.path.join(SITE, "assets", "scans", f"page-{p:02d}.jpg"))

    open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(build_index())
    for n in range(1, 41):
        open(os.path.join(SITE, "bars", BARS[str(n)]["slug"] + ".html"),
             "w", encoding="utf-8").write(build_bar(n))
    open(os.path.join(SITE, "nights", "index.html"), "w", encoding="utf-8").write(build_nights())
    open(os.path.join(SITE, "about", "index.html"), "w", encoding="utf-8").write(build_about())
    open(os.path.join(SITE, ".nojekyll"), "w").write("")

    n_files = sum(len(f) for _, _, f in os.walk(SITE))
    print(f"built {n_files} files into site/  ({len(used)} scans copied)")

if __name__ == "__main__":
    main()
