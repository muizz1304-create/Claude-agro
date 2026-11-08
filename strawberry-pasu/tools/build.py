#!/usr/bin/env python3
"""Generate the HyperFrames composition for the strawberry pot-size video.

Reads data/cut_plan.json (the edited A-roll's word timings, produced by
tools/build_cut.py) and writes index.html, compositions/*.html.
Every graphic, caption and sound effect is timed to a spoken word.

    python3 tools/build.py
"""
import json, os, re, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
plan = json.load(open(os.path.join(ROOT, "data/cut_plan.json")))
TAIL = 2.5  # frozen tail added to aroll.mp4 so the end card can be read
DUR = round(plan["duration"] + TAIL, 3)
SEGS = plan["segs"]
WORDS = plan["words"]
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
    "perpaksian": "perkongsian", "14cm": "14 cm", "11cm": "11 cm", "kau": "korang",
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


# =============================================================== 1. HOOK
sc = Scene("hook", 0, E("hook"), css=f"""
#hook-l1 {{ top:300px; font-size:66px; color:{C['cream']}; }}
#hook-l2 {{ top:390px; font-size:94px; white-space:nowrap; left:0; right:0; }}
#hook-l3w {{ position:absolute; left:0; right:0; top:520px; text-align:center; }}
#hook-l3 {{ display:inline-block; background:{C['berry']}; color:#fff; font-weight:900; font-size:132px;
  padding:6px 40px 14px; border-radius:26px; letter-spacing:-.02em; box-shadow:0 18px 50px rgba(230,57,70,.55); }}
#hook-flash {{ position:absolute; inset:0; background:radial-gradient(ellipse at center, rgba(230,57,70,0) 40%, rgba(230,57,70,.55) 100%); opacity:0; }}
""")
sc.add('<div class="scrim-top"></div><div id="hook-flash"></div>')
sc.add('<div id="hook-l1" class="big">SALAH PILIH PASU?</div>')
sc.add('<div id="hook-l2" class="big">AKAR STRAWBERRY</div>')
sc.add('<div id="hook-l3w"><div id="hook-l3">BOLEH MATI!</div></div>')
# frame 0 already shows the full line (thumbnail); the slam lands on "mati"
sc.tw('tl.fromTo("#hook-l1",{opacity:1},{opacity:1,duration:.01},0);')
tm = T("hook", "mati")
sc.punch("#hook-l3", tm, 1.16)
sc.shake("#hook-l3w", tm)
sc.tw(f'tl.fromTo("#hook-flash",{{opacity:0}},{{opacity:1,duration:.06}},{sc.L(tm)});')
sc.tw(f'tl.to("#hook-flash",{{opacity:0,duration:.4}},{sc.L(tm)+0.08:.3f});')
sc.punch("#hook-l2", T("hook", "akar"), 1.06)
sc.out("#hook-l1,#hook-l2,#hook-l3w", E("hook") - 0.2, 0.18)
scenes.append(sc)
S_("impact-bass-1", 0.0, 0.55)
S_("impact-bass-1", tm, 0.6)

# =============================================================== 2. QUESTION
sc = Scene("soalan", S("q"), E("q"), css=f"""
#soalan-t {{ top:250px; font-size:84px; }}
.lbl {{ position:absolute; font-weight:900; font-size:76px; padding:10px 30px 16px; border-radius:24px; color:{C['ink']}; }}
#soalan-b {{ left:150px; top:480px; background:{C['amber']}; }}
#soalan-k {{ left:700px; top:610px; background:{C['leaf']}; }}
.lbl:after {{ content:''; position:absolute; left:50%; bottom:-22px; margin-left:-22px; border:22px solid transparent; border-bottom:0; border-top-color:inherit; }}
#soalan-b:after {{ border-top-color:{C['amber']}; }} #soalan-k:after {{ border-top-color:{C['leaf']}; }}
""")
sc.add('<div id="soalan-t" class="big">Saiz pasu apa<br>yang <span class="hl">BETUL?</span></div>')
sc.add('<div id="soalan-b" class="lbl">BESAR?</div><div id="soalan-k" class="lbl">KECIL?</div>')
sc.blurin("#soalan-t", S("q") + 0.05, 0.22)
sc.pop("#soalan-b", T("q", "nak"))
sc.pop("#soalan-k", T("q", "nak", 1))
sc.out("#soalan-t,#soalan-b,#soalan-k", E("q") - 0.13, 0.12)
scenes.append(sc)
whoosh(S("q"))
S_("pop", T("q", "nak"), 0.45)
S_("pop", T("q", "nak", 1), 0.45)

# =============================================================== 3. ROOTS (B-roll photo)
sc = Scene("akar", S("akar"), E("akar2"), css=f"""
#akar-card {{ position:absolute; left:60px; top:230px; width:960px; }}
#akar-ph {{ position:relative; width:960px; height:638px; border-radius:40px; overflow:hidden; border:6px solid #fff;
  box-shadow:0 30px 70px rgba(0,0,0,.5); box-sizing:border-box; }}
#akar-ph img {{ width:100%; height:100%; object-fit:cover; display:block; }}
#akar-tag {{ position:absolute; left:28px; top:26px; }}
#akar-line {{ position:absolute; left:0; top:352px; width:100%; height:0; border-top:6px dashed {C['yellow']}; transform-origin:left center; }}
#akar-ll {{ position:absolute; right:26px; top:296px; font-weight:800; font-size:34px; color:{C['ink']}; background:{C['yellow']}; padding:6px 18px; border-radius:12px; }}
#akar-chips {{ position:absolute; left:0; right:0; top:676px; display:flex; gap:22px; justify-content:center; }}
.chip {{ font-weight:900; font-size:60px; padding:12px 34px 16px; border-radius:22px; background:{C['leaf']}; color:{C['ink']}; }}
#akar-rows {{ position:absolute; left:0; top:666px; width:960px; background:rgba(9,28,20,.88); border-radius:36px; padding:6px 36px 30px; box-sizing:border-box; }}
""")
sc.add('''<div id="akar-card">
  <div id="akar-ph"><img src="assets/img/akar-cetek.jpg" alt="Akar strawberry">
    <div id="akar-tag" class="tag">Sistem akar strawberry</div>
    <div id="akar-line"></div><div id="akar-ll">permukaan tanah</div></div>
  <div id="akar-chips"><div id="akar-c1" class="chip">SERABUT</div><div id="akar-c2" class="chip">CETEK</div></div>
  <div id="akar-rows">
    <div id="akar-r1" class="row"><div class="ico no">''' + CROSS + '''</div>Tak masuk jauh ke dalam</div>
    <div id="akar-r2" class="row"><div class="ico ok">''' + CHECK + '''</div>Hidup dekat permukaan tanah</div>
  </div>
</div>''')
sc.cardin("#akar-card", S("akar"))
sc.tw('tl.fromTo("#akar-ph img",{scale:1.12},{scale:1,duration:%.2f,ease:"power1.out"},0);' % (E("akar2") - S("akar")))
sc.tw('tl.fromTo("#akar-rows",{opacity:0},{opacity:0,duration:.01},0);')
sc.tw('tl.fromTo("#akar-line",{scaleX:0},{scaleX:0,duration:.01},0);')
sc.tw('tl.fromTo("#akar-ll",{opacity:0},{opacity:0,duration:.01},0);')
sc.pop("#akar-c1", T("akar", "rabut"))
sc.pop("#akar-c2", T("akar", "cetek"))
sc.out("#akar-chips", T("akar2", "jauh") - 0.25, 0.15)
sc.rise("#akar-rows", T("akar2", "jauh") - 0.1, 0.4, 40)
sc.tw('tl.fromTo("#akar-r2",{opacity:0},{opacity:0,duration:.01},0);')
sc.slidein("#akar-r2", T("akar2", "hidup"))
sc.tw(f'tl.fromTo("#akar-line",{{scaleX:0}},{{scaleX:1,duration:.5,ease:"power2.inOut"}},{sc.L(T("akar2","permukaan"))});')
sc.pop("#akar-ll", T("akar2", "permukaan") + 0.3)
sc.out("#akar-card", E("akar2") - 0.25)
scenes.append(sc)
whoosh(S("akar"))
S_("pop", T("akar", "rabut"), 0.42)
S_("pop", T("akar", "cetek"), 0.42)
S_("click-soft", T("akar2", "jauh"), 0.5)
S_("click-soft", T("akar2", "hidup"), 0.5)

# =============================================================== 4. IN A POT?
sc = Scene("pasuq", S("pasu?"), E("pasu?"), css="""
#pasuq-a { top:330px; font-size:74px; }
#pasuq-b { top:420px; font-size:132px; }
""")
sc.add('<div id="pasuq-a" class="big">Kalau tanam</div><div id="pasuq-b" class="big"><span class="hl">DALAM PASU?</span></div>')
sc.blurin("#pasuq-a", S("pasu?") + 0.05)
sc.pop("#pasuq-b", T("pasu?", "pasu"), 0.7)
sc.out("#pasuq-a,#pasuq-b", E("pasu?") - 0.2)
scenes.append(sc)
S_("pop", T("pasu?", "pasu"), 0.4)

# =============================================================== 5/6. TOO BIG / TOO SMALL
def pot_card(sid, seg_a, seg_b, tag_cls, tag, title, rows, water_from, water_to, potw):
    sc = Scene(sid, S(seg_a), E(seg_b), css=f"""
#{sid}-card {{ height:auto; }}
#{sid}-pot {{ position:absolute; right:40px; top:40px; }}
#{sid}-txt {{ width:560px; }}
""")
    rows_html = "".join(
        f'<div id="{sid}-r{i}" class="row"><div class="ico {cls}">{ico}</div><span>{txt}</span></div>'
        for i, (cls, ico, txt, _) in enumerate(rows))
    sc.add(f'''<div id="{sid}-card" class="card">
  <div id="{sid}-pot">{pot_svg(sid, potw)}</div>
  <div id="{sid}-txt"><div class="tag {tag_cls}">{tag}</div><div class="h1">{title}</div></div>
  <div style="height:8px"></div>{rows_html}
</div>''')
    sc.cardin(f"#{sid}-card", S(seg_a))
    hw = lambda f: round(202 * f, 1)
    sc.tw(f'tl.fromTo("#{sid}-water",{{attr:{{y:{276-hw(water_from)},height:{hw(water_from)}}}}},'
          f'{{attr:{{y:{276-hw(water_to)},height:{hw(water_to)}}},duration:{E(seg_b)-S(seg_a)-0.8:.2f},ease:"power1.inOut"}},0.4);')
    for i, (_, _, _, t) in enumerate(rows):
        sc.tw(f'tl.fromTo("#{sid}-r{i}",{{opacity:0}},{{opacity:0,duration:.01}},0);')
        sc.slidein(f"#{sid}-r{i}", t)
        S_("click-soft", t, 0.5)
    sc.out(f"#{sid}-card", E(seg_b) - 0.25)
    scenes.append(sc)
    whoosh(S(seg_a))

pot_card("besar", "besar", "besar2", "red", "Pasu terlalu besar", "Media lambat<br>kering",
         [("drop", DROP, "Air lama bertakung", T("besar", "lambat")),
          ("no", CROSS, "Akar tak dapat serap air berlebihan", S("besar2") + 0.05)],
         0.15, 0.95, 330)
pot_card("kecil", "kecil", "kecil", "amber", "Pasu terlalu kecil", "Air cepat<br>kering",
         [("drop", DROP, "Media cepat mengering", T("kecil", "cepat")),
          ("no", CROSS, "Pokok stres, kurang air", T("kecil", "stres"))],
         0.75, 0.04, 210)

# =============================================================== 7/8. HOW? -> ANSWER
sc = Scene("jawapan", S("how"), E("ans"), css=f"""
#jaw-q {{ top:420px; font-size:96px; }}
#jaw-panel {{ position:absolute; left:60px; width:960px; top:300px; padding:46px 40px 52px; box-sizing:border-box;
  background:{C['green']}; border-radius:48px; text-align:center; box-shadow:0 30px 80px rgba(0,0,0,.5); border:4px solid {C['leaf']}; }}
#jaw-panel .tag {{ margin-bottom:18px; }}
.jw {{ display:block; font-weight:900; letter-spacing:-.02em; line-height:1.0; }}
#jaw-1 {{ font-size:72px; color:{C['cream']}; }}
#jaw-2 {{ font-size:132px; color:{C['yellow']}; }}
#jaw-3 {{ font-size:112px; color:#fff; }}
#jaw-4 {{ font-size:46px; color:{C['leaf']}; margin-top:16px; font-weight:800; }}
""")
sc.add('<div id="jaw-q" class="big">Jadi, macam mana<br><span class="hl">nak pilih?</span></div>')
sc.add('''<div id="jaw-panel"><div class="tag yellow">Jawapannya</div>
  <span id="jaw-1" class="jw">IKUT</span><span id="jaw-2" class="jw">PERINGKAT</span>
  <span id="jaw-3" class="jw">PERTUMBUHAN</span><span id="jaw-4" class="jw">pokok strawberry</span></div>''')
sc.blurin("#jaw-q", S("how") + 0.05)
sc.out("#jaw-q", E("how") - 0.18, 0.16)
sc.cardin("#jaw-panel", S("ans") - 0.05)
for i in range(1, 5):
    sc.tw(f'tl.fromTo("#jaw-{i}",{{opacity:0}},{{opacity:0,duration:.01}},0);')
sc.blurin("#jaw-1", T("ans", "mengikut"))
sc.pop("#jaw-2", T("ans", "peringkat"), 1.4, 0.38, "expo.out")
sc.pop("#jaw-3", T("ans", "pertumbuhan"), 1.4, 0.38, "expo.out")
sc.blurin("#jaw-4", T("ans", "pokok"))
sc.out("#jaw-panel", E("ans") - 0.25)
scenes.append(sc)
whoosh(S("how"))
S_("impact-bass-1", T("ans", "peringkat"), 0.5)
S_("sparkle", T("ans", "pertumbuhan"), 0.4)

# =============================================================== 9. STAGE 1
sc = Scene("fasa1", S("start"), E("start"), css="""
#fasa1-c { padding:34px 44px 40px; }
""")
sc.add('<div id="fasa1-c" class="card"><div class="tag">Peringkat 1</div><div id="fasa1-h" class="h1">Anak benih baru<br><span class="grn">dari semaian sulur</span></div></div>')
sc.cardin("#fasa1-c", S("start"))
sc.out("#fasa1-c", E("start") - 0.22)
scenes.append(sc)
whoosh(S("start"))

# =============================================================== 10. POT 14 x 11 cm
ARROWS = f'''
  <g id="p14-wd" opacity="0"><line x1="30" y1="22" x2="270" y2="22" stroke="{C['yellow']}" stroke-width="7"/>
    <path d="M30 22 l16 -11 v22z M270 22 l-16 -11 v22z" fill="{C['yellow']}"/></g>
  <g id="p14-hd" opacity="0"><line x1="292" y1="52" x2="292" y2="280" stroke="{C['leaf']}" stroke-width="7"/>
    <path d="M292 52 l-11 16 h22z M292 280 l-11 -16 h22z" fill="{C['leaf']}"/></g>'''
sc = Scene("pasu14", S("dim"), E("air"), css=f"""
#pasu14-c {{ min-height:0; }}
#pasu14-pot {{ position:relative; width:340px; height:340px; margin:0 auto; }}
#p14-w {{ position:absolute; left:0; right:0; top:-34px; text-align:center; font-weight:900; font-size:64px; color:{C['yellow']}; }}
#p14-h {{ position:absolute; left:350px; top:130px; font-weight:900; font-size:64px; color:{C['leaf']}; white-space:nowrap; }}
#pasu14-txt {{ display:flex; justify-content:space-between; align-items:center; }}
""")
sc.add(f'''<div id="pasu14-c" class="card">
  <div id="pasu14-txt"><div class="tag">Pasu permulaan</div><div style="font-weight:800;font-size:36px;opacity:.75">saiz yang disyorkan</div></div>
  <div style="height:56px"></div>
  <div id="pasu14-pot">{pot_svg("p14", 340, water=False, label=ARROWS)}
    <div id="p14-w">⌀ 14 cm</div><div id="p14-h">11 cm<br><span style="font-size:34px;color:#fff;opacity:.8">dalam</span></div></div>
  <div id="pasu14-r0" class="row"><div class="ico ok">{CHECK}</div>Saiz sederhana, tak terlalu besar</div>
  <div id="pasu14-r1" class="row"><div class="ico ok">{CHECK}</div>Air tak bertakung lama</div>
</div>''')
sc.cardin("#pasu14-c", S("dim"))
for s_ in ["#p14-w", "#p14-h", "#pasu14-r0", "#pasu14-r1"]:
    sc.tw(f'tl.fromTo("{s_}",{{opacity:0}},{{opacity:0,duration:.01}},0);')
t14, t11 = T("dim", "14"), T("dim", "11")
sc.tw(f'tl.fromTo("#p14-wd",{{opacity:0,scaleX:0,transformOrigin:"150px 22px"}},{{opacity:1,scaleX:1,duration:.4,ease:"power3.out"}},{sc.L(t14)});')
sc.pop("#p14-w", t14 + 0.05)
sc.tw(f'tl.fromTo("#p14-hd",{{opacity:0,scaleY:0,transformOrigin:"292px 166px"}},{{opacity:1,scaleY:1,duration:.4,ease:"power3.out"}},{sc.L(t11)});')
sc.pop("#p14-h", t11 + 0.05)
sc.slidein("#pasu14-r0", T("why", "sedang"))
sc.slidein("#pasu14-r1", T("air", "bertakung"))
sc.out("#pasu14-c", E("air") - 0.25)
scenes.append(sc)
whoosh(S("dim"))
S_("pop", t14, 0.45); S_("pop", t11, 0.45)
S_("click-soft", T("why", "sedang"), 0.5); S_("click-soft", T("air", "bertakung"), 0.5)

# =============================================================== 11. HOW LONG?
sc = Scene("lama", S("lama"), E("lama"), css="""
#lama-a { top:330px; font-size:76px; } #lama-b { top:420px; font-size:120px; }
""")
sc.add('<div id="lama-a" class="big">Berapa lama boleh</div><div id="lama-b" class="big"><span class="hl">BERTAHAN?</span></div>')
sc.blurin("#lama-a", S("lama") + 0.04)
sc.pop("#lama-b", T("lama", "sustain"), 0.7)
sc.out("#lama-a,#lama-b", E("lama") - 0.2)
scenes.append(sc)
S_("pop", T("lama", "sustain"), 0.4)

# =============================================================== 12. 9-10 MONTHS
sc = Scene("bulan", S("910"), E("910"), css=f"""
#bulan-tag {{ position:absolute; left:60px; top:230px; }}
#bulan-n {{ top:300px; font-size:260px; color:{C['yellow']}; }}
#bulan-u {{ top:540px; font-size:110px; }}
#bulan-s {{ position:absolute; left:0; right:0; top:690px; text-align:center; }}
#bulan-s span {{ display:inline-block; background:rgba(9,28,20,.88); font-weight:800; font-size:46px; padding:14px 30px; border-radius:20px; }}
""")
sc.add('<div class="scrim-top"></div><div id="bulan-tag" class="tag">Peringkat 2</div>')
sc.add('<div id="bulan-n" class="big">9–10</div><div id="bulan-u" class="big">BULAN</div>')
sc.add('<div id="bulan-s"><span>Pasu 14 cm · masih boleh bertahan</span></div>')
sc.tw('tl.fromTo(".scrim-top",{opacity:0},{opacity:1,duration:.3},0);')
sc.slidein("#bulan-tag", S("910") + 0.05)
t9 = T("910", "9")
sc.pop("#bulan-n", t9, 1.5, 0.4, "expo.out")
sc.blurin("#bulan-u", t9 + 0.25)
sc.rise("#bulan-s", T("910", "masih"), 0.45, 30)
sc.out("#bulan-tag,#bulan-n,#bulan-u,#bulan-s,.scrim-top", E("910") - 0.25)
scenes.append(sc)
whoosh(S("910")); S_("impact-bass-1", t9, 0.45); S_("click-soft", T("910", "masih"), 0.5)

# =============================================================== 13. FROM BELOW
sc = Scene("bawah", S("bawah"), E("bawah"), css=f"""
#bawah-a {{ position:absolute; left:0; right:0; top:820px; text-align:center; }}
#bawah-a span {{ display:inline-block; background:{C['berry']}; font-weight:900; font-size:76px; padding:10px 34px 16px; border-radius:22px; box-shadow:0 18px 50px rgba(0,0,0,.45); }}
#bawah-b {{ position:absolute; left:0; right:0; top:945px; text-align:center; }}
#bawah-b span {{ display:inline-block; background:rgba(9,28,20,.9); font-weight:800; font-size:50px; padding:10px 30px 14px; border-radius:18px; }}
#bawah-t {{ position:absolute; left:60px; top:230px; }}
""")
sc.add('<div id="bawah-t" class="tag yellow">Tengok bawah pasu</div>')
sc.add('<div id="bawah-a"><span>AKAR DAH PENUH</span></div><div id="bawah-b"><span>&amp; berselirat dalam pasu</span></div>')
sc.slidein("#bawah-t", S("bawah") + 0.05)
sc.pop("#bawah-a", T("bawah", "penuh"))
sc.rise("#bawah-b", T("bawah", "berselirat"), 0.4, 30)
sc.out("#bawah-t,#bawah-a,#bawah-b", E("bawah") - 0.22)
scenes.append(sc)
S_("pop", T("bawah", "penuh"), 0.5); S_("click-soft", T("bawah", "berselirat"), 0.5)

# =============================================================== 14. UPSIZE
sc = Scene("upsize", S("upsize"), E("baru"), css=f"""
#ups-art {{ display:flex; align-items:flex-end; justify-content:center; gap:30px; margin-top:20px; height:300px; }}
#ups-arrow {{ font-weight:900; font-size:110px; color:{C['yellow']}; padding-bottom:70px; }}
""")
sc.add(f'''<div id="ups-c" class="card"><div class="tag">Masa untuk</div><div class="h1">UPSIZE <span class="grn">PASU</span></div>
  <div id="ups-art"><div id="ups-p1">{pot_svg("u1", 170, water=False)}</div><div id="ups-arrow">→</div><div id="ups-p2">{pot_svg("u2", 290, water=False)}</div></div>
  <div id="ups-r0" class="row"><div class="ico no">{CROSS}</div>Akar dah mula penuh</div>
  <div id="ups-r1" class="row"><div class="ico ok">{CHECK}</div>Akar baru boleh berkembang</div>
  <div id="ups-r2" class="row"><div class="ico ok">{CHECK}</div>Teroka media yang baru</div>
</div>''')
sc.cardin("#ups-c", S("upsize"))
for s_ in ["#ups-p2", "#ups-arrow", "#ups-r0", "#ups-r1", "#ups-r2"]:
    sc.tw(f'tl.fromTo("{s_}",{{opacity:0}},{{opacity:0,duration:.01}},0);')
tt = T("upsize", "tambah")
sc.slidein("#ups-arrow", tt, -40, 0.3)
sc.pop("#ups-p2", tt + 0.15, 0.4, 0.5)
sc.slidein("#ups-r0", T("upsize", "penuh"))
sc.slidein("#ups-r1", T("baru", "develop"))
sc.slidein("#ups-r2", T("baru", "explore"))
sc.out("#ups-c", E("baru") - 0.25)
scenes.append(sc)
whoosh(S("upsize")); S_("pop", tt + 0.15, 0.5)
for t in [T("upsize", "penuh"), T("baru", "develop"), T("baru", "explore")]:
    S_("click-soft", t, 0.5)

# =============================================================== 15/16. WARNING -> DROWNING
sc = Scene("amaran", S("jangan"), E("lemas"), css=f"""
#am-c {{ border:4px solid {C['berry']}; }}
#am-flow {{ display:flex; align-items:center; gap:18px; margin-top:28px; font-weight:900; font-size:44px; white-space:nowrap; }}
.am-pill {{ background:rgba(255,255,255,.1); padding:16px 26px; border-radius:22px; }}
#am-x {{ position:absolute; left:40px; right:40px; top:200px; height:120px; }}
#am-lemas {{ margin-top:30px; text-align:center; }}
#am-l1 {{ font-weight:800; font-size:40px; color:{C['water']}; }}
#am-l2 {{ font-weight:900; font-size:124px; white-space:nowrap; color:{C['berry']}; line-height:1; letter-spacing:-.02em; }}
""")
sc.add(f'''<div id="am-c" class="card"><div class="tag red">Amaran</div><div class="h1">Jangan terus<br>pasu besar!</div>
  <div id="am-flow"><div class="am-pill">Anak sulur</div><div style="color:{C['berry']}">→</div><div class="am-pill">Pasu besar</div><div id="am-xi" class="ico no">{CROSS}</div></div>
  <div id="am-lemas"><div id="am-l1">Air berlebihan, media terlalu lama basah</div><div id="am-l2">AKAR LEMAS</div></div>
</div>''')
sc.cardin("#am-c", S("jangan"))
for s_ in ["#am-flow", "#am-xi", "#am-l1", "#am-l2"]:
    sc.tw(f'tl.fromTo("{s_}",{{opacity:0}},{{opacity:0,duration:.01}},0);')
sc.rise("#am-flow", T("jangan", "anak"), 0.45, 30)
tb = T("jangan", "besar")
sc.pop("#am-xi", tb, 0.3, 0.4)
sc.blurin("#am-l1", T("lemas", "lebihan"))
tl_ = T("lemas", "mati")
sc.pop("#am-l2", tl_, 1.5, 0.35, "expo.out")
sc.shake("#am-c", tl_)
sc.out("#am-c", E("lemas") - 0.25)
scenes.append(sc)
whoosh(S("jangan")); S_("error", tb, 0.32); S_("click-soft", T("lemas", "lebihan"), 0.5)
S_("impact-bass-1", tl_, 0.6)

# =============================================================== 17. PROOF 14 -> 20
sc = Scene("bukti", S("20"), E("hasil"), css=f"""
#bk-c {{ padding:34px 44px 40px; }}
#bk-flow {{ display:flex; align-items:center; justify-content:center; gap:26px; margin-top:26px; }}
.bk-p {{ font-weight:900; font-size:70px; padding:12px 34px 16px; border-radius:24px; }}
#bk-a {{ background:rgba(255,255,255,.12); }} #bk-b {{ background:{C['leaf']}; color:{C['ink']}; }}
#bk-ar {{ font-weight:900; font-size:80px; color:{C['yellow']}; }}
#bk-h {{ position:absolute; left:60px; top:230px; width:960px; box-sizing:border-box; padding:30px 40px 34px; background:rgba(9,28,20,.9); border-radius:40px; }}
#bk-h .row {{ font-size:52px; margin-top:20px; }}
""")
sc.add('''<div id="bk-c" class="card"><div class="tag yellow">Bukti · lepas repot</div>
  <div id="bk-flow"><div id="bk-a" class="bk-p">14 cm</div><div id="bk-ar">→</div><div id="bk-b" class="bk-p">20 cm</div></div></div>''')
sc.add(f'''<div id="bk-h"><div class="tag">Hasilnya</div>
  <div id="bk-r0" class="row"><div class="ico ok">{CHECK}</div>Keluar bunga baru</div>
  <div id="bk-r1" class="row"><div class="ico ok">{CHECK}</div>Daun lebih besar</div>
  <div id="bk-r2" class="row"><div class="ico ok">{CHECK}</div>Lebih cantik</div></div>''')
sc.cardin("#bk-c", S("20"))
for s_ in ["#bk-ar", "#bk-b", "#bk-h", "#bk-r0", "#bk-r1", "#bk-r2"]:
    sc.tw(f'tl.fromTo("{s_}",{{opacity:0}},{{opacity:0,duration:.01}},0);')
t20 = T("20", "20")
sc.slidein("#bk-ar", t20 - 0.25, -40, 0.3)
sc.pop("#bk-b", t20)
sc.out("#bk-c", S("hasil") - 0.2, 0.2)
sc.cardin("#bk-h", S("hasil") + 0.05)
for i, w in enumerate([("hasil", "bunga"), ("hasil", "daun"), ("hasil", "cantik")]):
    sc.pop(f"#bk-r{i}", T(*w), 0.7, 0.4)
    S_("pop", T(*w), 0.45)
sc.out("#bk-h", E("hasil") - 0.25)
scenes.append(sc)
whoosh(S("20")); S_("pop", t20, 0.45); whoosh(S("hasil")); S_("sparkle", T("hasil", "bunga"), 0.35)

# =============================================================== 18. BUT... (2-year JC plant)
sc = Scene("tapi", S("tapi"), E("masih"), css=f"""
#tp-big {{ top:360px; font-size:200px; color:{C['yellow']}; }}
#tp-sub {{ position:absolute; left:0; right:0; top:600px; text-align:center; }}
#tp-sub span {{ display:inline-block; background:rgba(9,28,20,.9); font-weight:800; font-size:50px; padding:12px 30px 16px; border-radius:20px; }}
#jc-c {{ padding:34px 44px 40px; }}
#jc-n {{ font-weight:900; font-size:150px; line-height:1; color:{C['yellow']}; margin-top:10px; }}
""")
sc.add('<div id="tp-big" class="big">TAPI...</div><div id="tp-sub"><span>ada pokok kekal dalam pasu 14 cm</span></div>')
sc.add(f'''<div id="jc-c" class="card"><div class="tag">Strawberry JC</div>
  <div id="jc-n">2+ TAHUN</div>
  <div id="jc-r" class="row"><div class="ico ok">{CHECK}</div>Masih dalam pasu 14 cm</div></div>''')
for s_ in ["#jc-c", "#jc-r", "#jc-n"]:
    sc.tw(f'tl.fromTo("{s_}",{{opacity:0}},{{opacity:0,duration:.01}},0);')
sc.pop("#tp-big", S("tapi") + 0.03, 1.6, 0.35, "expo.out")
sc.rise("#tp-sub", T("tapi", "gunakan"), 0.4, 30)
sc.out("#tp-big,#tp-sub", E("tapi") - 0.2)
sc.cardin("#jc-c", S("jc"))
t2 = T("jc", "2")
sc.pop("#jc-n", t2, 0.6)
sc.slidein("#jc-r", T("masih", "masih"))
sc.out("#jc-c", E("masih") - 0.2)
scenes.append(sc)
S_("impact-bass-1", S("tapi") + 0.03, 0.45); S_("click-soft", T("tapi", "gunakan"), 0.45)
whoosh(S("jc")); S_("pop", t2, 0.45); S_("click-soft", T("masih", "masih"), 0.5)

# =============================================================== 19. BROWN ROOTS
sc = Scene("coklat", S("coklat"), E("coklat"), css="""
#ck-a { position:absolute; left:0; right:0; top:830px; text-align:center; }
#ck-b { position:absolute; left:0; right:0; top:950px; text-align:center; }
.ckl { display:inline-block; font-weight:900; font-size:62px; padding:10px 30px 16px; border-radius:20px; box-shadow:0 18px 50px rgba(0,0,0,.45); }
""")
sc.add(f'<div id="ck-a"><span class="ckl" style="background:#8B5A2B">Akar penuh sampai coklat</span></div>')
sc.add(f'<div id="ck-b"><span class="ckl" style="background:{C["green"]}">Crown dah memanjang</span></div>')
sc.pop("#ck-a", T("coklat", "coklat"), 0.6)
sc.pop("#ck-b", T("coklat", "crown"), 0.6)
sc.out("#ck-a,#ck-b", E("coklat") - 0.22)
scenes.append(sc)
S_("pop", T("coklat", "coklat"), 0.45); S_("pop", T("coklat", "crown"), 0.45)

# =============================================================== 20. WATERING
sc = Scene("siram", S("siram"), E("siram"), css=f"""
#sr-ok {{ display:inline-block; margin-top:22px; font-weight:900; font-size:84px; color:{C['ink']}; background:{C['leaf']}; padding:6px 30px 12px; border-radius:20px; transform:rotate(-4deg); }}
#sr-c .row b {{ color:{C['yellow']}; }}
""")
sc.add(f'''<div id="sr-c" class="card"><div class="tag">Nak kekal pasu 14 cm?</div><br><div id="sr-ok">BOLEH!</div>
  <div id="sr-r0" class="row"><div class="ico drop">{DROP}</div><span>Tapi kena siram <b>lebih kerap</b></span></div>
  <div id="sr-r1" class="row"><div class="ico drop">{DROP}</div><span>Pokok besar: siram <b>hari-hari</b></span></div></div>''')
sc.cardin("#sr-c", S("siram"))
for s_ in ["#sr-ok", "#sr-r0", "#sr-r1"]:
    sc.tw(f'tl.fromTo("{s_}",{{opacity:0}},{{opacity:0,duration:.01}},0);')
tok = T("siram", "ok")
sc.tw(f'tl.fromTo("#sr-ok",{{opacity:0,scale:2.2,rotation:-4}},{{opacity:1,scale:1,rotation:-4,duration:.3,ease:"expo.out"}},{sc.L(tok)});')
sc.slidein("#sr-r0", T("siram", "kerap"))
sc.slidein("#sr-r1", T("siram", "pokok"))
sc.out("#sr-c", E("siram") - 0.25)
scenes.append(sc)
whoosh(S("siram")); S_("impact-bass-1", tok, 0.35)
S_("click-soft", T("siram", "kerap"), 0.5); S_("click-soft", T("siram", "pokok"), 0.5)

# =============================================================== 21. SUMMARY
END_SUM = S("tq") + 2.3
sc = Scene("rumusan", S("kesimpulan"), END_SUM, css=f"""
#rm-c {{ border:4px solid {C['leaf']}; }}
.rm-n {{ width:66px; height:66px; border-radius:50%; background:{C['yellow']}; color:{C['ink']}; font-weight:900; font-size:40px;
  display:flex; align-items:center; justify-content:center; flex:none; }}
#rm-g {{ margin-top:34px; background:rgba(255,255,255,.07); border-radius:28px; padding:8px 30px 26px; }}
#rm-g .row {{ font-size:36px; margin-top:18px; white-space:nowrap; }}
#rm-g b {{ color:{C['leaf']}; }}
""")
sc.add(f'''<div id="rm-c" class="card"><div class="tag">Kesimpulan</div><div class="h1">Pilih saiz pasu ikut:</div>
  <div id="rm-r0" class="row"><div class="rm-n">1</div>Peringkat pertumbuhan</div>
  <div id="rm-r1" class="row"><div class="rm-n">2</div>Umur pokok</div>
  <div id="rm-g">
    <div id="rm-g0" class="row">Anak benih → <b>pasu 14 cm</b></div>
    <div id="rm-g1" class="row">Akar penuh (9–10 bln) → <b>upsize 20 cm</b></div>
    <div id="rm-g2" class="row">Kekal pasu kecil → <b>siram hari-hari</b></div>
  </div></div>''')
sc.cardin("#rm-c", S("kesimpulan"))
for s_ in ["#rm-r0", "#rm-r1", "#rm-g", "#rm-g0", "#rm-g1", "#rm-g2"]:
    sc.tw(f'tl.fromTo("{s_}",{{opacity:0}},{{opacity:0,duration:.01}},0);')
sc.slidein("#rm-r0", T("kesimpulan", "peringkat"))
sc.slidein("#rm-r1", T("kesimpulan", "umur"))
tg = T("kesimpulan", "umur") + 0.3
sc.rise("#rm-g", tg, 0.4, 30)
for i in range(3):
    sc.slidein(f"#rm-g{i}", tg + 0.1 + i * 0.3)
sc.out("#rm-c", END_SUM - 0.2, 0.18)
scenes.append(sc)
whoosh(S("kesimpulan"))
S_("click-soft", T("kesimpulan", "peringkat"), 0.5); S_("click-soft", T("kesimpulan", "umur"), 0.5)
for i in range(3):
    S_("pop", tg + 0.1 + i * 0.3, 0.35)

# =============================================================== 22. OUTRO
sc = Scene("penutup", END_SUM, DUR, css=f"""
#pn-bg {{ position:absolute; inset:0; background:rgba(9,28,20,.72); }}
#pn-a {{ top:520px; font-size:128px; color:{C['yellow']}; }}
#pn-b {{ position:absolute; left:0; right:0; top:700px; text-align:center; font-weight:800; font-size:52px; line-height:1.25; }}
#pn-c {{ position:absolute; left:0; right:0; top:880px; text-align:center; }}
#pn-c span {{ display:inline-block; background:{C['berry']}; font-weight:900; font-size:56px; padding:14px 40px 18px; border-radius:999px; }}
""")
sc.add('<div id="pn-bg"></div><div id="pn-a" class="big">Terima kasih!</div>')
sc.add('<div id="pn-b">Semoga strawberry korang<br>berbuah lebat</div><div id="pn-c"><span>Follow untuk tips seterusnya</span></div>')
sc.tw('tl.fromTo("#pn-bg",{opacity:0},{opacity:1,duration:.4,ease:"power2.out"},0);')
sc.pop("#pn-a", END_SUM + 0.05, 0.7)
sc.rise("#pn-b", END_SUM + 0.2, 0.4, 30)
sc.pop("#pn-c", END_SUM + 0.3, 0.6)
scenes.append(sc)
S_("chime", END_SUM + 0.05, 0.4)

# =============================================================== CAPTIONS
NO_CAP = {"hook", "how", "ans", "tq"}
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
ZOOM = {"hook": (1.0, "50% 40%"), "q": (1.0, "50% 45%"), "pasu?": (1.12, "50% 45%"), "how": (1.1, "50% 45%"),
        "910": (1.06, "50% 40%"), "bawah": (1.16, "50% 25%"), "jangan": (1.08, "50% 45%"), "lemas": (1.14, "50% 45%"),
        "tapi": (1.1, "50% 45%"), "jc": (1.0, "50% 45%"), "masih": (1.1, "50% 45%"), "coklat": (1.14, "50% 30%"),
        "hasil": (1.05, "50% 45%"), "tq": (1.0, "50% 50%")}
cam_js = []
cam_js.append('tl.fromTo("#cam",{scale:1.22},{scale:1.0,duration:.32,ease:"expo.out"},0);')
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

# =============================================================== INDEX
hosts = []
for sc in scenes:
    hosts.append(f'      <div id="{sc.id}" data-composition-id="{sc.id}" data-composition-src="compositions/{sc.id}.html" '
                 f'data-start="{sc.start:.3f}" data-duration="{sc.end - sc.start:.3f}" data-track-index="1" '
                 f'data-track-kind="graphics" data-width="{W}" data-height="{H}" style="z-index:10"></div>')
index = f'''<!doctype html>
<html lang="ms" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <title>Pasu Strawberry</title>
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
