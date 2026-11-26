#!/usr/bin/env python3
"""Generate the HyperFrames composition for the strawberry plant-spacing video.

Reads data/cut_plan.json (segments, produced by tools/build_cut.py) and
data/aroll_tr.json (word timings re-transcribed from the cut A-roll) and writes
index.html, compositions/*.html and data/captions.srt.
Every graphic, caption and sound effect is timed to a spoken word.

    python3 tools/build.py
"""
import json, os, re, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
plan = json.load(open(os.path.join(ROOT, "data/cut_plan.json")))
TAIL = 2.5  # frozen tail added to aroll.mp4 so the end card can be read
DUR = round(plan["duration"] + TAIL, 3)
SEGS = plan["segs"]
# Word times come from the cut A-roll's own transcript (exact); segment labels
# come from the cut plan, matched word by word in order.
import difflib
_plan_w = plan["words"]
_tr = [w for s in json.load(open(os.path.join(ROOT, "data/aroll_tr.json"))) for w in s["words"]]
_n = lambda t: re.sub(r"[^\w]", "", t.lower())
_sm = difflib.SequenceMatcher(None, [_n(w["text"]) for w in _plan_w], [_n(w["w"]) for w in _tr], autojunk=False)
_lab = [None] * len(_tr)
for blk in _sm.get_matching_blocks():
    for k in range(blk.size):
        _lab[blk.b + k] = _plan_w[blk.a + k]["seg"]
for i in range(len(_lab)):
    if _lab[i] is None:
        _lab[i] = _lab[i - 1] if i else "hook"
WORDS = [dict(text=w["w"].strip(), start=round(w["s"], 3), end=round(w["e"], 3), seg=_lab[i]) for i, w in enumerate(_tr)]
FPS = 30
W, H = 1080, 1920

# --------------------------------------------------------------- word lookup
def norm(t):
    return re.sub(r"[^\w]", "", t.lower())

def T(seg, word, nth=0):
    """Output-time start of the nth word in a segment whose text starts with `word`."""
    hits = [w for w in WORDS if w["seg"] == seg and norm(w["text"]).startswith(norm(word))]
    if len(hits) <= nth:
        raise KeyError(f"{seg}:{word}")
    return hits[nth]["start"]

def S(seg):
    return SEGS[seg][0]

def E(seg):
    return SEGS[seg][1]

# --------------------------------------------------------------- caption text
FIX = {
    "rabut": "serabut", "sulu": "sulur", "tanamai": "tanaman", "report": "repot",
    "soberi": "strawberry", "stroberi": "strawberry", "stroberinya": "strawberrynya",
    "perpaksian": "perkongsian", "14cm": "14 cm", "20cm": "20 cm", "takde": "takde", "11cm": "11 cm", "kau": "korang",
}

def fix_word(t):
    m = re.match(r"^(\W*)(.*?)(\W*)$", t)
    pre, core, post = m.groups()
    rep = FIX.get(core.lower())
    if rep:
        core = rep
    return pre + core + post

# --------------------------------------------------------------- shared style
FONT = "Montserrat"
C = dict(green="#0E3B2C", leaf="#3DDC84", berry="#E63946", cream="#FFF4E0",
         amber="#FFB703", yellow="#FFE14D", water="#4CC9F0", ink="#0B1F17")

BASE_CSS = f"""
#root {{ position:absolute; inset:0; font-family:'{FONT}',sans-serif; color:#fff; overflow:visible; }}
.card {{ position:absolute; left:60px; width:960px; top:230px; background:rgba(9,28,20,.88);
  border-radius:44px; padding:40px 46px 44px; box-shadow:0 30px 70px rgba(0,0,0,.45);
  border:2px solid rgba(255,255,255,.10); box-sizing:border-box; }}
.tag {{ display:inline-block; padding:12px 28px 12px; border-radius:999px; font-weight:800;
  font-size:32px; letter-spacing:.08em; text-transform:uppercase; color:{C['ink']}; background:{C['leaf']}; }}
.tag.red {{ background:{C['berry']}; color:#fff; }}
.tag.amber {{ background:{C['amber']}; }}
.tag.yellow {{ background:{C['yellow']}; }}
.h1 {{ font-weight:900; font-size:78px; line-height:1.02; letter-spacing:-.015em; margin-top:22px; }}
.row {{ display:flex; align-items:center; gap:24px; font-size:46px; font-weight:700; line-height:1.15; margin-top:28px; }}
.ico {{ width:66px; height:66px; border-radius:50%; flex:none; display:flex; align-items:center; justify-content:center; }}
.ico svg {{ width:38px; height:38px; }}
.ok {{ background:#22B455; }} .no {{ background:{C['berry']}; }} .drop {{ background:{C['water']}; }}
.big {{ position:absolute; left:40px; right:40px; text-align:center; font-weight:900; line-height:1.0;
  letter-spacing:-.02em; paint-order:stroke fill; -webkit-text-stroke:14px rgba(0,0,0,.85);
  text-shadow:0 10px 30px rgba(0,0,0,.55); }}
.hl {{ color:{C['yellow']}; }} .red {{ color:{C['berry']}; }} .grn {{ color:{C['leaf']}; }}
.blk {{ display:inline-block; }}
.scrim-top {{ position:absolute; left:0; top:0; width:{W}px; height:1150px;
  background:linear-gradient(180deg, rgba(0,0,0,.62) 0%, rgba(0,0,0,.35) 55%, rgba(0,0,0,0) 100%); }}
"""

CHECK = '<svg viewBox="0 0 24 24"><path d="M4 12.5l5 5L20 6.5" fill="none" stroke="#fff" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
CROSS = '<svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18" fill="none" stroke="#fff" stroke-width="3.6" stroke-linecap="round"/></svg>'
DROP = '<svg viewBox="0 0 24 24"><path d="M12 2.5C9 7 5.5 10.6 5.5 14.4a6.5 6.5 0 0013 0C18.5 10.6 15 7 12 2.5z" fill="#fff"/></svg>'

def pot_svg(sid, w=300, water=True, label=""):
    """A terracotta pot with a clipped water level rect (#{sid}-water)."""
    wat = ""
    if water:
        wat = (f'<g clip-path="url(#{sid}-clip)"><rect id="{sid}-water" x="0" y="280" width="300" height="0" '
               f'fill="{C["water"]}" opacity=".85"/></g>')
    return f'''<svg width="{w}" height="{w}" viewBox="0 0 300 300" style="overflow:visible">
  <defs><clipPath id="{sid}-clip"><path d="M48 74 L252 74 L228 276 L72 276 Z"/></clipPath></defs>
  <path d="M48 74 L252 74 L228 276 L72 276 Z" fill="#5B3A29"/>
  {wat}
  <path d="M30 52 L270 52 L264 82 L36 82 Z" fill="#D9573B"/>
  <path d="M48 82 L252 82 L228 280 L72 280 Z" fill="none" stroke="#D9573B" stroke-width="16" stroke-linejoin="round"/>
  {label}
</svg>'''


class Scene:
    """One graphics sub-composition. Times passed in are GLOBAL seconds."""

    def __init__(self, sid, start, end, css=""):
        self.id, self.start, self.end = sid, round(start, 3), round(end, 3)
        self.css, self.html, self.js = css, [], []

    def L(self, t):
        return round(max(0.0, t - self.start), 3)

    def add(self, s):
        self.html.append(s)

    def tw(self, s):
        self.js.append(s)

    # ---- motion vocabulary (fromTo only; seek-safe) ----
    def pop(self, sel, t, scale=0.6, dur=0.42, ease="back.out(1.8)"):
        self.tw(f'tl.fromTo("{sel}",{{opacity:0,scale:{scale}}},{{opacity:1,scale:1,duration:{dur},ease:"{ease}"}},{self.L(t)});')

    def blurin(self, sel, t, dur=0.2, y=0):
        self.tw(f'tl.fromTo("{sel}",{{opacity:0,filter:"blur(10px)",y:{y}}},{{opacity:1,filter:"blur(0px)",y:0,duration:{dur},ease:"power4.out"}},{self.L(t)});')

    def rise(self, sel, t, dur=0.5, y=60):
        self.tw(f'tl.fromTo("{sel}",{{opacity:0,y:{y}}},{{opacity:1,y:0,duration:{dur},ease:"expo.out"}},{self.L(t)});')

    def slidein(self, sel, t, x=-80, dur=0.42):
        self.tw(f'tl.fromTo("{sel}",{{opacity:0,x:{x},filter:"blur(8px)"}},{{opacity:1,x:0,filter:"blur(0px)",duration:{dur},ease:"expo.out"}},{self.L(t)});')

    def cardin(self, sel, t):
        self.tw(f'tl.fromTo("{sel}",{{opacity:0,y:-40,scale:.94,filter:"blur(12px)"}},{{opacity:1,y:0,scale:1,filter:"blur(0px)",duration:.5,ease:"expo.out"}},{self.L(t)});')

    def out(self, sel, t, dur=0.22):
        self.tw(f'tl.to("{sel}",{{opacity:0,filter:"blur(8px)",duration:{dur},ease:"power2.in"}},{self.L(t)});')

    def punch(self, sel, t, s=1.14):
        lt = self.L(t)
        self.tw(f'tl.fromTo("{sel}",{{scale:1}},{{scale:{s},duration:.09,ease:"power2.out"}},{lt});')
        self.tw(f'tl.to("{sel}",{{scale:1,duration:.35,ease:"elastic.out(1,0.5)"}},{round(lt+0.09,3)});')

    def shake(self, sel, t):
        lt = self.L(t)
        seq = [14, -12, 9, -6, 3, 0]
        for i, x in enumerate(seq):
            self.tw(f'tl.to("{sel}",{{x:{x},duration:.035,ease:"none"}},{round(lt+i*0.035,3)});')

    def write(self):
        body = "\n".join(self.html)
        # every fromTo after a selector's first one must not render at build time
        firsts = {}
        for line in self.js:
            m = re.match(r'tl\.fromTo\("([^"]+)".*,([\d.]+)\);$', line)
            if m:
                firsts.setdefault(m.group(1), []).append(float(m.group(2)))
        out = []
        for line in self.js:
            m = re.match(r'tl\.fromTo\("([^"]+)".*,([\d.]+)\);$', line)
            if m and len(firsts[m.group(1)]) > 1 and float(m.group(2)) > min(firsts[m.group(1)]):
                pos = m.group(2)
                line = line[: line.rindex("}," + pos + ");")] + ",immediateRender:false}," + pos + ");"
            out.append(line)
        js = "\n    ".join(out)
        doc = f'''<template>
  <style>{BASE_CSS}{self.css}</style>
  <div id="root" data-composition-id="{self.id}" data-width="{W}" data-height="{H}" data-layout-allow-overlap>
{body}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    {js}
    window.__timelines["{self.id}"] = tl;
  </script>
</template>
'''
        open(os.path.join(ROOT, "compositions", f"{self.id}.html"), "w").write(doc)


scenes = []
sfx = []  # (name, visual_time, volume)

PEAK = {"whoosh": .162, "whoosh-short": .162, "whoosh-cinematic": 2.503, "pop": .12, "click-soft": .073,
        "impact-bass-1": .073, "impact-bass-2": 1.986, "sparkle": .027, "chime": .418, "error": .745,
        "ping": .324, "glitch-3": 1.823}
FILE_DUR = {"whoosh": .575, "whoosh-short": .575, "whoosh-cinematic": 5.544, "pop": .72, "click-soft": .366,
            "impact-bass-1": 2.116, "impact-bass-2": 2.592, "sparkle": 1.802, "chime": 2.544, "error": 1.62,
            "ping": 1.32, "glitch-3": 3.096}
_wh = ["whoosh", "whoosh-cinematic", "whoosh-short"]
_whi = [0]

def whoosh(t, vol=0.32):
    name = _wh[_whi[0] % len(_wh)]
    _whi[0] += 1
    sfx.append((name, t, vol if name != "whoosh-cinematic" else vol * 0.8))

def S_(name, t, vol):
    sfx.append((name, t, vol))



# ---------------------------------------------------------------- icons for the three reasons
SUN = f'<svg viewBox="0 0 48 48"><circle cx="24" cy="24" r="9" fill="{C["amber"]}"/><g stroke="{C["amber"]}" stroke-width="4" stroke-linecap="round"><line x1="24" y1="3" x2="24" y2="9"/><line x1="24" y1="39" x2="24" y2="45"/><line x1="3" y1="24" x2="9" y2="24"/><line x1="39" y1="24" x2="45" y2="24"/><line x1="9" y1="9" x2="13" y2="13"/><line x1="35" y1="35" x2="39" y2="39"/><line x1="9" y1="39" x2="13" y2="35"/><line x1="35" y1="13" x2="39" y2="9"/></g></svg>'
WIND = f'<svg viewBox="0 0 48 48" fill="none" stroke="{C["water"]}" stroke-width="4.5" stroke-linecap="round"><path d="M4 18h26a6 6 0 1 0-6-6"/><path d="M4 28h34a6 6 0 1 1-6 6"/><path d="M4 38h16"/></svg>'
BUG = f'<svg viewBox="0 0 48 48"><g stroke="{C["berry"]}" stroke-width="3.5" stroke-linecap="round"><line x1="10" y1="20" x2="17" y2="23"/><line x1="38" y1="20" x2="31" y2="23"/><line x1="8" y1="30" x2="16" y2="30"/><line x1="40" y1="30" x2="32" y2="30"/><line x1="10" y1="40" x2="17" y2="36"/><line x1="38" y1="40" x2="31" y2="36"/><line x1="20" y1="10" x2="17" y2="5"/><line x1="28" y1="10" x2="31" y2="5"/></g><ellipse cx="24" cy="30" rx="9" ry="12" fill="{C["berry"]}"/><circle cx="24" cy="15" r="6" fill="{C["berry"]}"/></svg>'
UP = f'<svg viewBox="0 0 24 24"><path d="M12 4v16M5 11l7-7 7 7" fill="none" stroke="#fff" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/></svg>'

CARD_TOP = 330  # below the corner watermark (y 178-282)

# =============================================================== 1. HOOK
sc = Scene("hook", 0, E("hook"), css=f"""
#hook-a {{ top:300px; font-size:74px; color:{C['cream']}; }}
#hook-b {{ top:388px; font-size:116px; color:{C['yellow']}; white-space:nowrap; }}
#hook-cw {{ position:absolute; left:0; right:0; top:560px; text-align:center; }}
#hook-c {{ display:inline-block; background:{C['berry']}; color:#fff; font-weight:900; font-size:92px; white-space:nowrap;
  padding:6px 40px 14px; border-radius:26px; letter-spacing:-.02em; box-shadow:0 18px 50px rgba(230,57,70,.55); }}
""")
sc.add('<div class="scrim-top"></div>')
sc.add('<div id="hook-a" class="big">TANAM STRAWBERRY</div><div id="hook-b" class="big">RAPAT-RAPAT?</div>')
sc.add('<div id="hook-cw"><div id="hook-c">SEBENARNYA TIDAK!</div></div>')
tno = T("hook", "sebenarnya")
sc.punch("#hook-b", T("hook", "rapat"), 1.08)
sc.tw('tl.fromTo("#hook-cw",{opacity:0},{opacity:0,duration:.01},0);')
sc.tw(f'tl.fromTo("#hook-cw",{{opacity:0,scale:2.2,rotation:-6}},{{opacity:1,scale:1,rotation:-3,duration:.28,ease:"expo.out",immediateRender:false}},{sc.L(tno)});')
sc.shake("#hook-cw", tno + 0.28)
sc.out("#hook-a,#hook-b,#hook-cw,.scrim-top", E("hook") - 0.18, 0.16)
scenes.append(sc)
S_("impact-bass-1", 0.0, 0.5)
S_("impact-bass-1", tno, 0.6)

# =============================================================== 2. TOPIC (after the watermark lands)
sc = Scene("topik", T("intro", "membincangkan") - 0.15, E("intro"), css="")
sc.add(f'''<div id="tp-c" class="card" style="top:{CARD_TOP}px"><div class="tag">Topik hari ni</div>
  <div class="h1">Jarak tanam<br><span class="grn">antara pokok strawberry</span></div></div>''')
sc.cardin("#tp-c", sc.start + 0.02)
sc.out("#tp-c", E("intro") - 0.22)
scenes.append(sc)
whoosh(sc.start + 0.02)

# =============================================================== 3. MYTH vs FACT
sc = Scene("mitos", S("ruang"), E("ruang"), css=f"""
#mf-c .row {{ font-size:44px; margin-top:22px; }}
.mf-l {{ font-weight:900; font-size:30px; letter-spacing:.08em; padding:6px 16px; border-radius:12px; margin-right:6px; }}
""")
sc.add(f'''<div id="mf-c" class="card" style="top:{CARD_TOP}px">
  <div id="mf-r0" class="row"><div class="ico no">{CROSS}</div><span><span class="mf-l" style="background:{C['berry']}">MITOS</span> Boleh tanam rapat-rapat</span></div>
  <div id="mf-r1" class="row"><div class="ico ok">{CHECK}</div><span><span class="mf-l" style="background:#22B455">FAKTA</span> Pokok perlukan <b style="color:{C['yellow']}">ruang</b> untuk membesar</span></div>
</div>''')
sc.cardin("#mf-c", S("ruang") + 0.02)
sc.tw('tl.fromTo("#mf-r1",{opacity:0},{opacity:0,duration:.01},0);')
sc.tw('tl.fromTo("#mf-r0",{opacity:1},{opacity:1,duration:.01},0);')
tr_ = T("ruang", "memerlukan")
sc.slidein("#mf-r1", tr_)
sc.tw(f'tl.to("#mf-r0",{{opacity:.45,duration:.3}},{sc.L(tr_)});')
sc.out("#mf-c", E("ruang") - 0.22)
scenes.append(sc)
whoosh(S("ruang") + 0.02); S_("click-soft", tr_, 0.5)

# =============================================================== 4. THREE REASONS
sc = Scene("sebab", S("s1"), E("s3"), css=f"""
#sb-c .row {{ font-size:44px; margin-top:24px; }}
.sb-n {{ width:58px; height:58px; border-radius:50%; background:{C['yellow']}; color:{C['ink']}; font-weight:900; font-size:34px;
  display:flex; align-items:center; justify-content:center; flex:none; }}
.sb-i {{ width:74px; height:74px; flex:none; }}
.sb-i svg {{ width:74px; height:74px; }}
""")
rows = [("Rebut cahaya matahari", SUN, T("s1", "pertama")),
        ("Pengudaraan terhad", WIND, T("s2", "kedua")),
        ("Serangga &amp; penyakit mudah merebak", BUG, T("s3", "ketiga"))]
rows_html = "".join(f'<div id="sb-r{i}" class="row"><div class="sb-n">{i+1}</div><div class="sb-i">{ico}</div><span>{txt}</span></div>'
                    for i, (txt, ico, _) in enumerate(rows))
sc.add(f'<div id="sb-c" class="card" style="top:{CARD_TOP}px"><div class="tag red">Kalau tanam rapat</div>{rows_html}</div>')
sc.cardin("#sb-c", T("s1", "pertama") - 0.45)
for i, (_, _, t) in enumerate(rows):
    sc.tw(f'tl.fromTo("#sb-r{i}",{{opacity:0}},{{opacity:0,duration:.01}},0);')
    sc.slidein(f"#sb-r{i}", t)
    if i:
        sc.tw(f'tl.to("#sb-r{i-1}",{{opacity:.5,duration:.3}},{sc.L(t)});')
    S_("pop", t, 0.45)
sc.tw(f'tl.to("#sb-r0,#sb-r1",{{opacity:1,duration:.3}},{sc.L(T("s3", "lain"))});')
sc.out("#sb-c", E("s3") - 0.22)
scenes.append(sc)
whoosh(T("s1", "pertama") - 0.45)

# =============================================================== 5. BEST SPACING 14-20 cm (diagram)
def side_pot(x):
    return (f'<path d="M{x} 70 L{x+180} 70 L{x+160} 230 L{x+20} 230 Z" fill="#C8442F"/>'
            f'<rect x="{x-8}" y="56" width="196" height="24" rx="6" fill="#D9573B"/>'
            f'<path d="M{x+90} 56 C{x+40} 0 {x+20} 10 {x+30} -10 M{x+90} 56 C{x+140} 0 {x+170} 10 {x+150} -10 M{x+90} 56 L{x+90} -20" '
            f'stroke="{C["leaf"]}" stroke-width="10" fill="none" stroke-linecap="round"/>')
sc = Scene("jarak", S("jarak"), E("jarak") + 0.8, css=f"""
#jk-svg {{ display:block; margin:40px auto 0; overflow:visible; }}
#jk-nw {{ position:relative; height:100px; margin-top:6px; }}
#jk-n, #jk-b {{ position:absolute; left:0; right:0; font-weight:900; font-size:96px; color:{C['yellow']}; text-align:center; line-height:1; }}
#jk-s {{ font-weight:700; font-size:38px; text-align:center; opacity:.85; margin-top:10px; }}
""")
sc.add(f'''<div id="jk-c" class="card" style="top:{CARD_TOP}px"><div class="tag">Jarak terbaik antara pasu</div>
  <svg id="jk-svg" width="860" height="250" viewBox="0 -30 860 280">
    {side_pot(60)}{side_pot(620)}
    <g id="jk-ar"><line x1="250" y1="150" x2="610" y2="150" stroke="{C['yellow']}" stroke-width="8" stroke-dasharray="18 12"/>
      <path d="M250 150 l24 -16 v32z M610 150 l-24 -16 v32z" fill="{C['yellow']}"/></g>
  </svg>
  <div id="jk-nw"><div id="jk-n">14 cm</div><div id="jk-b">14–20 cm</div></div>
  <div id="jk-s">ruang kosong antara tepi pasu</div></div>''')
sc.cardin("#jk-c", S("jarak") + 0.02)
t14, t20 = T("jarak", "14"), T("contoh", "20") if any(w["seg"] == "contoh" and norm(w["text"]).startswith("20") for w in WORDS) else T("jarak", "20")
for s_ in ["#jk-ar", "#jk-n", "#jk-b", "#jk-s"]:
    sc.tw(f'tl.fromTo("{s_}",{{opacity:0}},{{opacity:0,duration:.01}},0);')
sc.tw(f'tl.fromTo("#jk-ar",{{opacity:0,scaleX:0,transformOrigin:"430px 150px"}},{{opacity:1,scaleX:1,duration:.45,ease:"power3.out"}},{sc.L(t14 - 0.3)});')
sc.pop("#jk-n", t14)
t20 = T("jarak", "hinggalah")
sc.out("#jk-n", t20 - 0.08, 0.08)
sc.pop("#jk-b", t20, 0.7)
sc.rise("#jk-s", t20 + 0.3, 0.4, 20)
sc.out("#jk-c", E("jarak") + 0.6)
scenes.append(sc)
whoosh(S("jarak") + 0.02); S_("pop", t14, 0.5); S_("pop", T("jarak", "hinggalah"), 0.5)

# =============================================================== 6. HOW TO MEASURE (steps over the demo)
sc = Scene("ukur", S("contoh"), E("demo3") + 0.75, css=f"""
#uk-tag {{ position:absolute; left:60px; top:{CARD_TOP}px; }}
.uk-s {{ position:absolute; left:60px; right:60px; top:950px; display:flex; align-items:center; gap:22px;
  background:rgba(9,28,20,.9); border-radius:30px; padding:20px 28px; font-size:44px; font-weight:800; line-height:1.15;
  box-shadow:0 18px 50px rgba(0,0,0,.45); }}
.uk-n {{ width:62px; height:62px; border-radius:50%; background:{C['yellow']}; color:{C['ink']}; font-weight:900; font-size:36px;
  display:flex; align-items:center; justify-content:center; flex:none; }}
.uk-s b {{ color:{C['yellow']}; }}
""")
steps = [("Guna pasu <b>±14 cm</b> sebagai pembaris", T("demo1", "ambil", 1)),
         ("Letak di <b>ruang antara</b> pasu", T("demo2", "letak")),
         ("<b>Tepi bertemu tepi</b> = jarak 14 cm", T("demo2", "hujung")),
         ("Ulang untuk <b>pasu yang lain</b>", T("demo3", "teruskan"))]
sc.add('<div id="uk-tag" class="tag yellow">Cara mudah ukur jarak</div>')
for i, (txt, _) in enumerate(steps):
    sc.add(f'<div id="uk-s{i}" class="uk-s"><div class="uk-n">{i+1}</div><span>{txt}</span></div>')
sc.slidein("#uk-tag", E("jarak") + 0.85)
for i, (_, t) in enumerate(steps):
    sc.tw(f'tl.fromTo("#uk-s{i}",{{opacity:0}},{{opacity:0,duration:.01}},0);')
    sc.rise(f"#uk-s{i}", t, 0.4, 40)
    if i + 1 < len(steps):
        sc.out(f"#uk-s{i}", steps[i + 1][1] - 0.15, 0.13)
    S_("pop", t, 0.45)
sc.out(f"#uk-s{len(steps)-1},#uk-tag", E("demo3") + 0.55)
scenes.append(sc)
whoosh(E("jarak") + 0.85)

# =============================================================== 7. WHY? -> CONSEQUENCES
sc = Scene("akibat", S("kenapa"), E("akibat"), css=f"""
#ak-q {{ top:520px; font-size:92px; }}
#ak-c .row {{ font-size:46px; margin-top:24px; }}
""")
sc.add('<div id="ak-q" class="big">Kenapa jarak<br><span class="hl">PENTING?</span></div>')
sc.add(f'''<div id="ak-c" class="card" style="top:{CARD_TOP}px"><div class="tag red">Bila pokok bersaing</div>
  <div id="ak-r0" class="row"><div class="ico" style="background:{C['amber']}">{UP}</div>Pokok jadi tinggi</div>
  <div id="ak-r1" class="row"><div class="ico no">{CROSS}</div>Hasil tak ada, buah tak jadi</div>
  <div id="ak-r2" class="row"><div class="ico no">{CROSS}</div>Serangga pun banyak</div></div>''')
tq_ = T("kenapa", "kenapa")
sc.blurin("#ak-q", tq_ - 0.1)
sc.out("#ak-q", E("kenapa") + 0.25, 0.16)
sc.tw('tl.fromTo("#ak-c",{opacity:0},{opacity:0,duration:.01},0);')
sc.cardin("#ak-c", T("akibat", "tinggi") - 0.5)
ak = [T("akibat", "tinggi"), T("akibat", "tapi"), T("akibat", "buah") + 0.75]
for i, t in enumerate(ak):
    sc.tw(f'tl.fromTo("#ak-r{i}",{{opacity:0}},{{opacity:0,duration:.01}},0);')
    sc.slidein(f"#ak-r{i}", t)
    S_("click-soft" if i == 0 else "error", t, 0.5 if i == 0 else 0.22)
sc.out("#ak-c", E("akibat") - 0.22)
scenes.append(sc)
S_("pop", tq_, 0.4); whoosh(T("akibat", "tinggi") - 0.5)

# =============================================================== 8. SUMMARY
sc = Scene("rumusan", S("tutup"), E("tutup") + 0.35, css=f"""
#rm-c {{ border:4px solid {C['leaf']}; }}
#rm-c .row {{ font-size:44px; margin-top:22px; }}
#rm-big {{ font-weight:900; font-size:84px; color:{C['yellow']}; margin-top:18px; line-height:1; }}
""")
sc.add(f'''<div id="rm-c" class="card" style="top:{CARD_TOP}px"><div class="tag">Kesimpulan</div>
  <div id="rm-big">Jarak 14–20 cm</div>
  <div id="rm-r0" class="row"><div class="ico ok">{CHECK}</div>Pokok membesar dengan baik</div>
  <div id="rm-r1" class="row"><div class="ico ok">{CHECK}</div>Dapat hasil yang lebih</div></div>''')
sc.cardin("#rm-c", S("tutup") + 0.02)
tb_ = T("tutup", "bertumbuh"); th_ = T("tq", "hasil") if any(w["seg"] == "tq" for w in WORDS) else T("tutup", "kita", 1)
for i, t in enumerate([tb_, min(th_, tb_ + 0.6)]):
    sc.tw(f'tl.fromTo("#rm-r{i}",{{opacity:0}},{{opacity:0,duration:.01}},0);')
    sc.slidein(f"#rm-r{i}", min(t, sc.end - 1.0))
    S_("click-soft", min(t, sc.end - 1.0), 0.5)
sc.out("#rm-c", sc.end - 0.2, 0.18)
scenes.append(sc)
whoosh(S("tutup") + 0.02)
END_SUM = sc.end

# =============================================================== 9. OUTRO
sc = Scene("penutup", END_SUM, DUR, css=f"""
#pn-bg {{ position:absolute; inset:0; background:rgba(9,28,20,.72); }}
#pn-a {{ top:600px; font-size:124px; color:{C['yellow']}; }}
#pn-b {{ position:absolute; left:0; right:0; top:780px; text-align:center; font-weight:800; font-size:50px; line-height:1.25; }}
#pn-c {{ position:absolute; left:0; right:0; top:930px; text-align:center; }}
#pn-c span {{ display:inline-block; background:{C['berry']}; font-weight:900; font-size:54px; padding:14px 40px 18px; border-radius:999px; }}
""")
sc.add('<div id="pn-bg"></div><div id="pn-a" class="big">Terima kasih!</div>')
sc.add('<div id="pn-b">Jarakkan pokok,<br>buah pun lebat</div><div id="pn-c"><span>Follow untuk tips seterusnya</span></div>')
sc.tw('tl.fromTo("#pn-bg",{opacity:0},{opacity:1,duration:.4,ease:"power2.out"},0);')
sc.pop("#pn-a", END_SUM + 0.05, 0.7)
sc.rise("#pn-b", END_SUM + 0.1, 0.4, 30)
sc.pop("#pn-c", END_SUM + 0.08, 0.6)
scenes.append(sc)
S_("chime", END_SUM + 0.05, 0.4)

# =============================================================== WATERMARK
# Appears big in the centre after the hook, then shrinks into the top-left corner
# (inside the platform-safe band) and stays there at 70% opacity with a soft pulsing glow.
WM_IN = E("hook") + 0.08
WM_MIN = WM_IN + 1.6
WM_W, WM_H = 1320, 593
big_w, small_w = 780, 270
sx = small_w / big_w
big_x, big_y = (W - big_w) / 2, 640
small_x, small_y = 30, 172
wm = Scene("watermark", WM_IN, DUR, css=f"""
#wm {{ position:absolute; left:{big_x:.0f}px; top:{big_y}px; width:{big_w}px; height:{big_w*WM_H/WM_W:.0f}px; opacity:.7; transform-origin:0 0; }}
#wm img {{ width:100%; height:100%; display:block; }}
""")
wm.add('<div id="wm"><img src="assets/img/watermark.png" alt="The Agro Guy"></div>')
wm.tw('tl.fromTo("#wm",{opacity:0,scale:.82,filter:"blur(14px) drop-shadow(0 0 0px rgba(255,214,120,0))"},'
      '{opacity:.7,scale:1,filter:"blur(0px) drop-shadow(0 0 26px rgba(255,214,120,.95))",duration:.55,ease:"expo.out"},0);')
wm.tw('tl.to("#wm",{filter:"drop-shadow(0 2px 5px rgba(0,0,0,.55)) drop-shadow(0 0 20px rgba(255,214,120,1))",duration:.3},.6);')
dx, dy = small_x - big_x, small_y - big_y
wm.tw(f'tl.to("#wm",{{x:{dx:.1f},y:{dy:.1f},scale:{sx:.4f},duration:.75,ease:"power3.inOut"}},{WM_MIN - WM_IN - 0.75:.3f});')
# glow pulse: explicit yoyo segments so every frame is a function of time (no repeat:-1)
t, k = WM_MIN - WM_IN, 0
while t < DUR - WM_IN - 0.1:
    strong = (k % 2 == 0)
    g = "drop-shadow(0 2px 5px rgba(0,0,0,.55)) drop-shadow(0 0 20px rgba(255,214,120,1))" if strong else "drop-shadow(0 2px 5px rgba(0,0,0,.55)) drop-shadow(0 0 6px rgba(255,214,120,.5))"
    wm.tw(f'tl.to("#wm",{{filter:"{g}",duration:1.2,ease:"sine.inOut"}},{t:.3f});')
    t += 1.2; k += 1
scenes.append(wm)
S_("sparkle", WM_IN, 0.4)
S_("whoosh-short", WM_MIN - 0.4, 0.28)

# =============================================================== CAPTIONS
NO_CAP = {"hook"}
caps = [w for w in WORDS if w["seg"] not in NO_CAP]
# join hyphen continuations ("siap" + "-silap")
merged = []
for w in caps:
    if w["text"].startswith("-") and merged and merged[-1]["seg"] == w["seg"]:
        merged[-1] = dict(merged[-1], text=merged[-1]["text"] + w["text"], end=w["end"])
    else:
        merged.append(dict(w))
for w in merged:
    w["text"] = fix_word(w["text"])

groups, cur = [], []
for i, w in enumerate(merged):
    cur.append(w)
    nxt = merged[i + 1] if i + 1 < len(merged) else None
    chars = sum(len(x["text"]) + 1 for x in cur)
    brk = (nxt is None or nxt["seg"] != w["seg"] or re.search(r"[.,?!]$", w["text"])
           or len(cur) >= 4 or chars >= 20 or (nxt["start"] - w["end"]) > 0.3
           or chars + len(nxt["text"]) > 24)
    if brk:
        groups.append(cur); cur = []

cap_html, cap_js = [], []
prev_end = 0.0
for gi, g in enumerate(groups):
    seg = g[0]["seg"]
    gs = max(prev_end, g[0]["start"] - 0.06)
    nxt_start = groups[gi + 1][0]["start"] - 0.06 if gi + 1 < len(groups) else DUR
    ge = min(max(g[-1]["end"] + 0.2, gs + 0.5), nxt_start, E(seg) + 0.05, DUR)
    ge = max(ge, gs + 0.2)
    prev_end = ge
    txt = " ".join(re.sub(r"[.,!]$", "", w["text"]) for w in g)
    n = len(txt)
    fs = 66 if n <= 16 else (60 if n <= 20 else 54)
    spans = []
    for wi, w in enumerate(g):
        t = re.sub(r"[.,!]$", "", w["text"])
        spans.append(f'<span id="cw{gi}-{wi}" class="cw">{html.escape(t)}</span>')
        cap_js.append(f'tl.set("#cw{gi}-{wi}",{{color:"{C["yellow"]}"}},{max(gs, w["start"]):.3f});')
        if wi + 1 < len(g):
            cap_js.append(f'tl.set("#cw{gi}-{wi}",{{color:"#fff"}},{g[wi+1]["start"]:.3f});')
    cap_html.append(f'    <div id="cg{gi}" class="clip cg" data-start="{gs:.3f}" data-duration="{ge-gs:.3f}">'
                    f'<div class="cgi" style="font-size:{fs}px">{" ".join(spans)}</div></div>')
    cap_js.append(f'tl.fromTo("#cg{gi} .cgi",{{opacity:0,scale:.82,y:14}},{{opacity:1,scale:1,y:0,duration:.14,ease:"back.out(2)"}},{gs:.3f});')

cap_doc = f'''<template>
  <style>
    #root {{ position:absolute; inset:0; }}
    .cg {{ position:absolute; left:0; top:1150px; width:{W}px; height:170px; overflow:visible; }}
    .cgi {{ position:absolute; left:0; right:0; top:0; text-align:center; padding:0 70px; font-family:'{FONT}',sans-serif;
      font-weight:900; line-height:1.12; color:#fff; text-transform:uppercase; letter-spacing:-.005em;
      paint-order:stroke fill; -webkit-text-stroke:12px #000; text-shadow:0 6px 18px rgba(0,0,0,.6); }}
    .cw {{ display:inline-block; }}
  </style>
  <div id="root" data-composition-id="captions" data-width="{W}" data-height="{H}">
{chr(10).join(cap_html)}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    {chr(10).join("    " + j for j in cap_js).strip()}
    window.__timelines["captions"] = tl;
  </script>
</template>
'''

# =============================================================== CAMERA (punch-ins)
# Hard punch-ins at every segment and alternate scale at jump cuts inside a segment
ZOOM = {"hook": (1.0, "50% 45%"), "s1": (1.06, "50% 55%"), "s2": (1.06, "50% 55%"), "s3": (1.06, "50% 55%"),
        "demo2": (1.08, "50% 35%"), "kenapa": (1.12, "50% 45%"), "akibat": (1.04, "50% 50%")}
cam_js = []
cam_js.append('tl.fromTo("#cam",{scale:1.18},{scale:1.0,duration:.18,ease:"expo.out"},0);')
last_seg, alt = None, 0
for p in plan["pieces"]:
    z, org = ZOOM.get(p["seg"], (1.0, "50% 45%"))
    if p["seg"] != last_seg:
        alt = 0
    else:
        alt ^= 1
    s = round(z * (1.07 if alt else 1.0), 3)
    if p["o"] > 0:
        cam_js.append(f'tl.set("#cam",{{scale:{s},transformOrigin:"{org}"}},{p["o"]:.3f});')
    last_seg = p["seg"]

# =============================================================== SFX elements
sfx_html = []
for i, (name, t, vol) in enumerate(sorted(sfx, key=lambda x: x[1])):
    st = t + 1 / FPS - PEAK[name]
    ms = 0.0
    if st < 0:
        ms, st = -st, 0.0
    dur = {"whoosh-cinematic": 3.2}.get(name, FILE_DUR[name])
    dur = min(dur - ms, DUR - st)
    dur_attr = f' data-duration="{dur:.3f}"'
    sfx_html.append(f'      <audio id="sfx{i}" class="clip" src="assets/sfx/{name}.mp3" data-start="{st:.3f}"'
                    f' data-media-start="{ms:.3f}"{dur_attr} data-volume="{vol}" data-track-index="{3 + i % 6}"></audio>')

# =============================================================== MUSIC BED
# HeyGen catalog track 2a2b3177 (120 bpm acoustic guitar), trimmed to the film with a
# 1.8 s fade-out (assets/bgm/bed.mp3). Louder under the hook and the end card, ducked under the voice.
BED = 0.11
pts = [(0, 0.30), (E("hook") - 0.05, 0.30), (E("hook") + 0.35, BED),
       (END_SUM - 0.25, BED), (END_SUM + 0.5, 0.30), (DUR, 0.30)]
lane = json.dumps({"version": 1, "lanes": [{"target": "volume",
       "points": [{"t": round(t, 3), "v": v} for t, v in pts]}]}, separators=(",", ":"))
bgm_html = (f"      <audio id=\"bgm\" class=\"clip\" src=\"assets/bgm/bed.mp3\" data-start=\"0\" "
            f"data-duration=\"{DUR:.3f}\" data-track-index=\"9\" data-automation='{lane}'></audio>")

# =============================================================== INDEX
hosts = []
for sc in scenes:
    hosts.append(f'      <div id="{sc.id}" data-composition-id="{sc.id}" data-composition-src="compositions/{sc.id}.html" '
                 f'data-start="{sc.start:.3f}" data-duration="{sc.end - sc.start:.3f}" data-track-index="1" '
                 f'data-track-kind="graphics" data-width="{W}" data-height="{H}" style="z-index:{30 if sc.id == "watermark" else 10}"></div>')
index = f'''<!doctype html>
<html lang="ms" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <title>Jarak Tanam Strawberry</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      html, body {{ margin:0; width:{W}px; height:{H}px; overflow:hidden; background:#000; }}
      #root {{ position:relative; width:{W}px; height:{H}px; overflow:hidden; font-family:'{FONT}',sans-serif; }}
      #cam {{ position:absolute; left:0; top:0; width:{W}px; height:{H}px; }}
      #aroll {{ position:absolute; left:0; top:0; width:{W}px; height:{H}px; object-fit:cover; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{DUR:.3f}" data-width="{W}" data-height="{H}">
      <div id="cam">
        <video id="aroll" class="clip" src="assets/aroll.mp4" data-start="0" data-duration="{DUR:.3f}" data-track-index="0"
          playsinline data-has-audio="true" data-volume="1"></video>
      </div>
{chr(10).join(hosts)}
      <div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0"
        data-duration="{DUR:.3f}" data-track-index="2" data-track-kind="captions" data-width="{W}" data-height="{H}" style="z-index:20"></div>
{bgm_html}
{chr(10).join(sfx_html)}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      {chr(10).join("      " + j for j in cam_js).strip()}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
'''

os.makedirs(os.path.join(ROOT, "compositions"), exist_ok=True)
for f in os.listdir(os.path.join(ROOT, "compositions")):
    if f.endswith(".html"):
        os.remove(os.path.join(ROOT, "compositions", f))
for sc in scenes:
    sc.write()
open(os.path.join(ROOT, "compositions/captions.html"), "w").write(cap_doc)
open(os.path.join(ROOT, "index.html"), "w").write(index)
print(f"scenes={len(scenes)} caption_groups={len(groups)} sfx={len(sfx)} duration={DUR}")

# =============================================================== SRT sidecar (all speech, corrected)
def _ts(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
allw = []
for w in WORDS:
    if w["text"].startswith("-") and allw and allw[-1]["seg"] == w["seg"]:
        allw[-1] = dict(allw[-1], text=allw[-1]["text"] + w["text"], end=w["end"])
    else:
        allw.append(dict(w))
lines, cur = [], []
for i, w in enumerate(allw):
    cur.append(dict(w, text=fix_word(w["text"])))
    nxt = allw[i + 1] if i + 1 < len(allw) else None
    if nxt is None or nxt["seg"] != w["seg"] or re.search(r"[.?!]$", w["text"]) or len(cur) >= 8:
        lines.append(cur); cur = []
with open(os.path.join(ROOT, "data/captions.srt"), "w") as f:
    for n, l in enumerate(lines, 1):
        f.write(f"{n}\n{_ts(l[0]['start'])} --> {_ts(l[-1]['end'] + 0.1)}\n{' '.join(x['text'] for x in l)}\n\n")
