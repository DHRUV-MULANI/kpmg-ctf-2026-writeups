from PIL import Image, ImageOps
import sys
img = Image.open("/home/boss/Works/ctf/KPMG/OSINT/a_clean_tail/Challenge.png").convert("L")
w = 170
h = int(img.height / img.width * w * 0.5)
img2 = img.resize((w, h))
ramp = "@%#*+=-:. "
px = img2.load()
for y in range(h):
    line = ""
    for x in range(w):
        v = px[x, y]
        line += ramp[min(len(ramp)-1, v * len(ramp) // 256)]
    print(line)
