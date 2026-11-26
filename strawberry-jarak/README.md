# Strawberry: Jarak Tanam Antara Pokok (video menegak 9:16)

Suntingan `VID_20261126_091106.mp4` (2:56 mentah) menjadi klip **1:42** (1080×1920, 30 fps),
dibina dengan [HyperFrames](https://hyperframes.heygen.com).

Hasil akhir: `renders/strawberry-jarak-final.mp4` · Caption berasingan: `data/captions.srt`

## Suntingan (disahkan oleh pemilik sebelum render)

**Hook (0–4.4 s):** "…pokok strawberry ni sebenarnya boleh je tanam rapat-rapat, takde masalah? Sebenarnya tidak."
dengan teks "TANAM STRAWBERRY RAPAT-RAPAT?" → "SEBENARNYA TIDAK!".

**Dibuang:**

| Masa asal | Ayat | Sebab |
| --- | --- | --- |
| 0:00 | "So," | pembuka kosong |
| 0:11–0:20 | "mungkin masih ramai yang di luar sana mempunyai pemahaman…" | sudah ada dalam hook |
| 1:09–1:16 | "sebab itu, jarak penanaman ni penting…" | diulang di penutup |
| 1:17–1:36 | "bila korang tanam guna pasu ni, senanglah nak kira… saiz dia memang just nice je… yang biasanya bila guna pasu lah" | ayat tergantung, boleh mengelirukan |
| 1:47–1:51 | "Cuma sekarang ni saya ambil contoh mudah. Kalau korang, cuma…" | tergagap / ulangan |
| 2:25–2:27 | "Jarak antara pokok ni." | ulang soalan |
| 2:54 | "Okay." | penutup kosong |
| semua | pause > 0.3 s | dipendekkan |

Caption disahkan: "14 cm", "pengudaraan", "Sebenarnya tidak!" (tanpa "eh"), ejaan "strawberry".

## Grafik

Hook · kad topik · mitos vs fakta · 3 sebab dengan ikon (cahaya, pengudaraan, serangga) ·
diagram dua pasu "14 → 14–20 cm, ruang kosong antara tepi pasu" · langkah ukur 1–4 semasa demo ·
"Kenapa jarak penting?" · kad akibat (pokok tinggi, buah tak jadi, serangga) · kesimpulan · penutup.

## Watermark

`assets/img/watermark.png` (dari `agro-guy/watermark/output/agro-guy-watermark-2000.png`, dipotong ke isi).
Muncul besar di tengah selepas hook (4.5 s), mengecil ke bucu **atas kiri** (di bawah status bar)
dalam 0.75 s, kekal hingga akhir pada **opacity 70%** dengan glow emas berdenyut (1.2 s) dan
bayang gelap halus supaya jelas di latar terang.

## Audio

Suara: high-pass 90 Hz, kurangkan bunyi bising rumah hijau, −16 LUFS. Muzik: trek HeyGen `2a2b3177`
(gitar akustik 120 bpm), 0.30 semasa hook dan penutup, 0.11 di bawah suara. 28 SFX.

## Bina semula

```bash
python3 tools/build_cut.py <scratch-dir> assets/aroll_raw.mp4   # potong (perlu video mentah + transkrip)
python3 tools/build.py                                          # jana komposisi + SRT
npx hyperframes check && npx hyperframes render -o renders/strawberry-jarak.mp4 --quality delivery
```
