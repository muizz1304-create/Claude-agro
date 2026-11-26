import json, sys, subprocess, os, math
S=sys.argv[1]; OUT=sys.argv[2]
V=f"{S}/raw/src.mp4"
words=[w for seg in json.load(open(f"{S}/transcript.json")) for w in seg["words"]]
sil=[tuple(map(float,l.split())) for l in open(f"{S}/silences.txt") if l.strip()]
FPS=30
# segments: list of word-start ranges (a,b) inclusive; optional 'v' = video source start (J-cut hook)
SEGS=[
 dict(id="hook", r=[(20.1,23.7),(24.95,25.74,"raw")]),
 dict(id="intro", r=[(1.0,9.9)]),
 dict(id="ruang", r=[(26.5,31.7)]),
 dict(id="s1", r=[(33.7,47.7)]),
 dict(id="s2", r=[(48.1,58.0)]),
 dict(id="s3", r=[(58.6,67.7)]),
 dict(id="jarak", r=[(96.9,103.2),(103.25,106.6,"raw")]),
 dict(id="contoh", r=[(111.3,114.9),(114.85,116.5,"raw")]),
 dict(id="demo1", r=[(117.2,120.5),(122.8,127.2)]),
 dict(id="demo2", r=[(127.9,131.7),(132.1,135.5)]),
 dict(id="demo3", r=[(136.2,139.0)]),
 dict(id="kenapa", r=[(140.4,144.9)]),
 dict(id="akibat", r=[(147.8,149.8),(150.5,154.7),(155.9,159.45,"raw"),(160.35,162.5,"raw")]),
 dict(id="tutup", r=[(163.6,173.2)]),
]
def widx(t): return min(range(len(words)), key=lambda i: abs(words[i]["s"]-t))
def snap(t): return round(t*FPS)/FPS
pieces=[]  # (seg_id, a, b, vstart)
for sg in SEGS:
  for rr in sg["r"]:
    ta,tb=rr[0],rr[1]
    if len(rr)>2:  # exact seconds, checked by ear-proxy (fine re-transcription)
      a,b=ta,tb
    else:
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
