import json, sys, subprocess, os, math
S=sys.argv[1]; OUT=sys.argv[2]
V=f"{S}/raw/src/VID_20261103_112643.mp4"
words=[w for seg in json.load(open(f"{S}/transcript.json")) for w in seg["words"]]
sil=[tuple(map(float,l.split())) for l in open(f"{S}/silences.txt") if l.strip()]
FPS=30
# segments: list of word-start ranges (a,b) inclusive; optional 'v' = video source start (J-cut hook)
SEGS=[
 dict(id="hook", r=[(250.98,252.48)], v=363.6),
 dict(id="q", r=[(18.72,23.94)]),
 dict(id="akar", r=[(28.22,29.28),(33.60,34.96)]),
 dict(id="akar2", r=[(50.74,52.54),(58.96,60.68)]),
 dict(id="pasu?", r=[(62.12,64.76)]),
 dict(id="besar", r=[(73.84,75.44),(76.56,82.08)]),
 dict(id="besar2", r=[(84.92,88.68)]),
 dict(id="kecil", r=[(91.28,99.82)]),
 dict(id="how", r=[(100.32,102.20)]),
 dict(id="ans", r=[(104.42,105.70),(107.84,110.76)]),
 dict(id="start", r=[(123.94,127.76),(131.22,133.70)]),
 dict(id="dim", r=[(136.58,139.30)]),
 dict(id="why", r=[(144.20,147.42)]),
 dict(id="air", r=[(159.38,162.24)]),
 dict(id="lama", r=[(171.40,174.04)]),
 dict(id="910", r=[(188.42,200.14)]),
 dict(id="bawah", r=[(201.10,208.80)]),
 dict(id="upsize", r=[(217.52,222.44)]),
 dict(id="baru", r=[(228.82,234.30)]),
 dict(id="jangan", r=[(236.02,238.04),(238.40,243.64)]),
 dict(id="lemas", r=[(262.54,270.48)]),
 dict(id="20", r=[(286.14,291.06),(293.06,294.38)]),
 dict(id="hasil", r=[(302.68,314.10)]),
 dict(id="tapi", r=[(330.22,330.22),(333.46,336.92)]),
 dict(id="jc", r=[(350.08,354.28)]),
 dict(id="masih", r=[(357.72,358.92)]),
 dict(id="coklat", r=[(364.26,365.86),(368.56,370.66)]),
 dict(id="siram", r=[(377.54,383.04),(386.54,389.52)]),
 dict(id="kesimpulan", r=[(320.80,327.42)]),
 dict(id="tq", r=[(403.92,406.06)]),
]
def widx(t): return min(range(len(words)), key=lambda i: abs(words[i]["s"]-t))
def snap(t): return round(t*FPS)/FPS
pieces=[]  # (seg_id, a, b, vstart)
for sg in SEGS:
  for (ta,tb) in sg["r"]:
    i,j=widx(ta),widx(tb)
    a=words[i]["s"]-0.10; b=words[j]["e"]+0.14
    if i>0: a=max(a, words[i-1]["e"]+0.02)
    if j+1<len(words): b=min(b, words[j+1]["s"]-0.03)
    # cap overly long final-word ends (whisper stretch)
    b=min(b, words[j]["s"]+max(0.35, 0.09*len(words[j]["w"]))+0.25)
    # remove internal silences
    cur=a; sub=[]
    for (s,e) in sil:
      if s>a+0.05 and e<b-0.05 and e-s>0.32:
        sub.append((cur,s+0.10)); cur=e-0.10
    sub.append((cur,b))
    for (x,y) in sub:
      x,y=snap(x),snap(y)
      if y-x>=2/FPS: pieces.append(dict(seg=sg["id"],a=x,b=y,v=sg.get("v")))
# output timeline + word map
t=0; outwords=[]; segtimes={}
for p in pieces:
  p["o"]=t; d=p["b"]-p["a"]
  segtimes.setdefault(p["seg"],[t,t+d]); segtimes[p["seg"]][1]=t+d
  t+=d
for k,w in enumerate(words):
  best=None; bo=0
  for p in pieces:
    ov=min(p["b"],w["e"])-max(p["a"],w["s"])
    if ov>bo: bo,best=ov,p
  if best and bo>=0.06:
    d=best["b"]-best["a"]
    outwords.append(dict(k=k,text=w["w"].strip(),start=round(best["o"]+max(0,w["s"]-best["a"]),3),end=round(best["o"]+min(d,w["e"]-best["a"]),3),seg=best["seg"]))
outwords.sort(key=lambda w:w["start"])
print("pieces",len(pieces),"duration",round(t,2), file=sys.stderr)
json.dump(dict(duration=round(t,3),pieces=pieces,words=outwords,segs={k:[round(a,3),round(b,3)] for k,(a,b) in segtimes.items()}),open(f"{S}/cut_plan.json","w"),indent=1,ensure_ascii=False)
if "--plan" in sys.argv: sys.exit()
os.makedirs(f"{S}/pieces",exist_ok=True)
lst=open(f"{S}/pieces/list.txt","w")
for n,p in enumerate(pieces):
  d=p["b"]-p["a"]; f=f"{S}/pieces/p{n:03d}.mp4"; vs=p["v"]
  if vs is not None and p is pieces[0]: pass
  vin = ["-ss",f"{(vs if vs is not None else p['a']):.3f}","-i",V]
  ain = ["-ss",f"{p['a']:.3f}","-i",V]
  fo=min(0.02,d/4)
  cmd=["ffmpeg","-v","error","-y",*vin,*ain,"-frames:v",str(round(d*FPS)),"-map","0:v:0","-map","1:a:0",
   "-vf",f"scale=1080:1920,fps={FPS},setsar=1","-af",f"aresample=48000,afade=t=in:d={fo},afade=t=out:st={d-fo:.4f}:d={fo},apad,atrim=0:{d:.4f}",
   "-c:v","libx264","-preset","veryfast","-crf","19","-g","30","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-ar","48000","-ac","2",f]
  subprocess.run(cmd,check=True); lst.write(f"file '{f}'\n")
lst.close()
subprocess.run(["ffmpeg","-v","error","-y","-f","concat","-safe","0","-i",f"{S}/pieces/list.txt","-c","copy","-movflags","+faststart",OUT],check=True)
print("wrote",OUT,file=sys.stderr)
