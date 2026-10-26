from PIL import Image
img = Image.open("/home/boss/Works/ctf/KPMG/OSINT/a_clean_tail/Challenge.png").convert("RGB")
W=96
H=int(img.height/img.width*W*0.45)
img2=img.resize((W,H))
px=img2.load()
def classify(r,g,b):
    mx=max(r,g,b); mn=min(r,g,b)
    if mx<45: return "K"        # black
    if mn>200: return "W"       # white
    if mx-mn<28:
        v=(r+g+b)//3
        return "." if v>150 else ":" if v>90 else "k"
    # hue
    import colorsys
    h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
    hd=h*360
    if hd<20 or hd>=330: return "R"
    if hd<45: return "O"
    if hd<70: return "Y"
    if hd<160: return "G"
    if hd<200: return "C"
    if hd<260: return "B"
    return "M"
for y in range(H):
    print("".join(classify(*px[x,y]) for x in range(W)))
