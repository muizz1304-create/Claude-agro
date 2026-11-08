import sys, json
from faster_whisper import WhisperModel
audio, out = sys.argv[1], sys.argv[2]
import numpy as np, subprocess
audio = np.frombuffer(subprocess.run(["ffmpeg","-v","error","-i",audio,"-f","f32le","-ac","1","-ar","16000","-"],capture_output=True,check=True).stdout, np.float32)
m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8", cpu_threads=4)
segs, info = m.transcribe(audio, language="ms", word_timestamps=True, vad_filter=False, beam_size=5,
    initial_prompt="Video tentang penanaman strawberry, anak benih bare root, akar, polybag, baja, cocopeat.")
print(info.language, info.duration, file=sys.stderr)
res=[]
for s in segs:
    d={"start":s.start,"end":s.end,"text":s.text,"words":[{"w":w.word,"s":w.start,"e":w.end,"p":w.probability} for w in s.words]}
    res.append(d); print(f"[{s.start:7.2f}-{s.end:7.2f}] {s.text}", file=sys.stderr, flush=True)
json.dump(res, open(out,"w"), ensure_ascii=False, indent=1)
