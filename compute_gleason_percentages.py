from PIL import Image
import numpy as np
import os, sys, csv, math, glob

def dist(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2)

# Renk merkezleri (senin extract çıktına göre)
COLORS = {
    "WHITE_BG": [(255,255,255), (254,254,254), (253,253,253), (251,251,251)],
    "BLACK_BG": [(0,0,0), (1,0,0), (2,0,0)],
    "GP5": [(251,184,157), (243,75,54)],         # pink + red
    "GP4": [(106,173,213), (183,212,234)],       # blue + light blue
    "GP3": [(164,218,158)],                      # green
}

TOL_BG = 12
TOL_CLASS = 18

def is_near_any(rgb, refs, tol):
    return any(dist(rgb, r) <= tol for r in refs)

def classify(rgb):
    if is_near_any(rgb, COLORS["WHITE_BG"], TOL_BG):
        return "WHITE_BG"
    if is_near_any(rgb, COLORS["BLACK_BG"], TOL_BG):
        return "BLACK_BG"
    for cls in ["GP5", "GP4", "GP3"]:
        if is_near_any(rgb, COLORS[cls], TOL_CLASS):
            return cls
    return "OTHER"

def crop_prediction_panel(arr):
    # layout: [Image | Prediction | Legend]
    h, w, _ = arr.shape
    x1 = int(w * 0.33)
    x2 = int(w * 0.66)
    y1 = int(h * 0.10)
    y2 = int(h * 0.95)
    mid = arr[y1:y2, x1:x2, :]

    flat = mid.reshape(-1, 3)
    mask_nonwhite = np.array([not is_near_any(tuple(px), COLORS["WHITE_BG"], TOL_BG) for px in flat])
    if mask_nonwhite.sum() < 1000:
        return mid

    ys, xs = np.where(mask_nonwhite.reshape(mid.shape[0], mid.shape[1]))
    top, bot = ys.min(), ys.max()
    left, right = xs.min(), xs.max()

    pad = 5
    top = max(0, top - pad); bot = min(mid.shape[0]-1, bot + pad)
    left = max(0, left - pad); right = min(mid.shape[1]-1, right + pad)

    return mid[top:bot+1, left:right+1, :]

def compute_for_file(path):
    img = Image.open(path).convert("RGB")
    arr = np.array(img)

    pred = crop_prediction_panel(arr)
    counts = {"GP3":0, "GP4":0, "GP5":0, "WHITE_BG":0, "BLACK_BG":0, "OTHER":0}
    flat = pred.reshape(-1, 3)
    for px in flat:
        cls = classify(tuple(px))
        counts[cls] += 1

    tissue_total = counts["GP3"] + counts["GP4"] + counts["GP5"] + counts["OTHER"]
    if tissue_total == 0:
        return None

    gp3 = counts["GP3"] / tissue_total * 100
    gp4 = counts["GP4"] / tissue_total * 100
    gp5 = counts["GP5"] / tissue_total * 100

    patterns = [("3", gp3), ("4", gp4), ("5", gp5)]
    patterns_sorted = sorted(patterns, key=lambda x: -x[1])
    dominant = patterns_sorted[0][0]
    secondary = patterns_sorted[1][0] if patterns_sorted[1][1] > 0 else ""
    suggestion = f"{dominant}+{secondary}" if secondary else dominant

    return {
        "file": os.path.basename(path),
        "GP3_pct": round(gp3, 2),
        "GP4_pct": round(gp4, 2),
        "GP5_pct": round(gp5, 2),
        "dominant": dominant,
        "secondary": secondary,
        "ai_suggestion": suggestion,
        "tissue_pixels": tissue_total,
        "other_pixels": counts["OTHER"],
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python compute_gleason_percentages.py <pred_png_or_folder>")
        sys.exit(1)

    target = sys.argv[1]
    if os.path.isdir(target):
        files = sorted(glob.glob(os.path.join(target, "pred_*.png")))
    else:
        files = [target]

    rows = []
    for f in files:
        r = compute_for_file(f)
        if r is None:
            print(f"⚠️ No tissue pixels detected: {f}")
            continue
        rows.append(r)
        print(f"✅ {r['file']}: GP3 {r['GP3_pct']}% | GP4 {r['GP4_pct']}% | GP5 {r['GP5_pct']}% | suggestion {r['ai_suggestion']}")

    if not rows:
        print("No valid outputs.")
        sys.exit(0)

    out_csv = os.path.join(os.getcwd(), "out", "gleason_percentages.csv")
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)

    with open(out_csv, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n📄 CSV saved to: {out_csv}")

if __name__ == "__main__":
    main()
