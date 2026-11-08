# Strawberry: Pilih Saiz Pasu Yang Betul (video menegak 9:16)

Suntingan video `VID_20261103_112643.mp4` (6:48 mentah) menjadi klip menegak **2:28**
(1080×1920, 30 fps), dibina dengan [HyperFrames](https://hyperframes.heygen.com).

Hasil akhir: `renders/strawberry-pasu-final.mp4` · Caption berasingan: `data/captions.srt`

## Apa yang dibuat

| Langkah | Butiran |
| --- | --- |
| Transkrip | Whisper `large-v3-turbo`, Bahasa Melayu, timestamp setiap perkataan (`data/transcript-raw.json`) |
| Potong | 6:48 → 2:25 isi. Dibuang: intro panjang, ayat berulang (akar di permukaan ×3, rumusan ×3), bahagian tergagap, "sebenarnya sebenarnya", dan **semua pause > 0.3 s** (dipendekkan ke ~0.2 s). 77 potongan, tepat pada frame |
| Audio suara | High-pass 80 Hz, kurangkan bunyi bising, normalize ke −16 LUFS |
| Hook | 0–2 s: close-up akar menembusi lubang pasu + suara "siap-silap akar pokok boleh mati" + teks "SALAH PILIH PASU? AKAR STRAWBERRY BOLEH MATI!" (J-cut: suara dari 4:11, visual dari 6:04) |
| Caption | Gaya sosial, huruf besar, perkataan aktif kuning, 2–4 perkataan setiap kumpulan. Ejaan dibetulkan (serabut, sulur, repot, perkongsian, strawberry) |
| Grafik | 20 scene: gambar akar (B-roll), kad pasu terlalu besar/kecil (animasi paras air), jawapan "ikut peringkat pertumbuhan", diagram pasu ⌀14 × 11 cm, 9–10 bulan, upsize, amaran akar lemas, bukti 14→20 cm, pengecualian pokok JC 2 tahun, kesimpulan, penutup |
| Gerakan | Punch-in pada setiap potongan (sembunyikan jump cut), zoom ke bawah pasu & akar coklat |
| SFX | 66 bunyi (whoosh, pop, click, impact, sparkle, error, chime) diletak 1 frame selepas visual |

## Struktur cerita

1. **Hook** – akar boleh mati
2. Soalan: pasu besar atau kecil?
3. Akar strawberry serabut & cetek
4. Pasu terlalu besar → lambat kering, akar tak serap · Pasu terlalu kecil → cepat kering, pokok stres
5. **Jawapan: ikut peringkat pertumbuhan**
6. Peringkat 1: anak benih → pasu 14 cm (dalam 11 cm)
7. Peringkat 2: 9–10 bulan, akar penuh → upsize
8. Amaran: jangan terus pasu besar → akar lemas
9. Bukti: 14 → 20 cm, bunga baru, daun besar
10. Tapi… pokok JC 2+ tahun masih pasu 14 cm → kena siram hari-hari
11. Kesimpulan + penutup

## Bina semula

```bash
# 1. potong A-roll daripada video mentah (perlukan raw footage + transcript + silences)
python3 tools/build_cut.py <scratch-dir> assets/aroll.mp4
# 2. jana komposisi (index.html, compositions/*.html, data/captions.srt)
python3 tools/build.py
# 3. semak & render
npx hyperframes check
npx hyperframes render -o renders/strawberry-pasu.mp4 --quality delivery
```

Untuk ubah teks, masa atau gaya: edit `tools/build.py` dan jana semula, atau buka projek
dalam HyperFrames Studio (`npx hyperframes preview`).

## Muzik latar

Belum ada muzik latar (akaun HeyGen belum log masuk, jadi katalog muzik tak dapat diakses).
Untuk tambah: `npx hyperframes auth login`, kemudian
`npx hyperframes media-use resolve --type bgm --intent "lofi santai, akustik, 90 bpm" --project .`
dan letak sebagai `<audio>` pada volume ~0.12 di bawah suara.

SFX: lihat `assets/sfx/CREDITS.md`. Gambar akar: dibekalkan oleh pemilik dalam folder Drive.
