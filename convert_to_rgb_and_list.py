import os, glob
from PIL import Image

repo = os.path.abspath(os.path.dirname(__file__))
img_dir = os.path.join(repo, "images")
out_dir = os.path.join(repo, "out")
conv_dir = os.path.join(out_dir, "converted_rgb")

os.makedirs(img_dir, exist_ok=True)
os.makedirs(out_dir, exist_ok=True)
os.makedirs(conv_dir, exist_ok=True)

exts = ("*.jpg","*.jpeg","*.png","*.tif","*.tiff","*.bmp")
files = []
for e in exts:
    files.extend(glob.glob(os.path.join(img_dir, e)))

# pred_* gibi yanlışlıkla atılmış çıktı dosyalarını input diye alma
files = [f for f in files if not os.path.basename(f).lower().startswith("pred_")]

if not files:
    print(f"[INFO] No images found in: {img_dir}")
    print("       Copy images there and run again.")
    raise SystemExit(0)

print(f"[INFO] Found {len(files)} image(s). Converting to RGB PNG...")

converted = []
for f in files:
    base = os.path.splitext(os.path.basename(f))[0]
    rgb_path = os.path.join(conv_dir, base + ".png")
    try:
        img = Image.open(f).convert("RGB")   # RGBA/CMYK -> RGB fix
        img.save(rgb_path)
        converted.append(rgb_path)
        print("  OK ->", rgb_path)
    except Exception as e:
        print("  FAIL:", f, "->", e)

list_path = os.path.join(conv_dir, "_converted_list.txt")
with open(list_path, "w", encoding="utf-8") as fp:
    for p in converted:
        fp.write(p + "\n")

print("[INFO] Converted list saved:", list_path)
