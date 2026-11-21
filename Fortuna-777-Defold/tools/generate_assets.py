"""Generate original 2.5D art and stop/win effects for Defold. Run before Bob."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math, wave, struct, subprocess
root=Path(__file__).resolve().parents[1]
out=root/"assets"
out.mkdir(exist_ok=True)
S=192
def icon(name,draw):
    im=Image.new("RGBA",(S,S))
    d=ImageDraw.Draw(im)
    def orb(cx,cy,r,c,ry=None):
        ry=ry or r
        d.ellipse((cx-r,cy-ry,cx+r,cy+ry),fill=tuple(int(v*.38) for v in c)+(255,))
        for k in range(34,0,-1):
            t=k/34
            shade=.45+.55*(1-t)**.45
            rgb=tuple(min(255,int(v*shade+20*(1-t))) for v in c)
            d.ellipse((cx-r*t-2,cy-ry*t-5,cx+r*t-2,cy+ry*t-5),fill=rgb+(255,))
        d.ellipse((cx-r*.48,cy-ry*.63,cx-r*.13,cy-ry*.38),fill=(255,255,235,170))
    draw(d,orb)
    im.save(out/(name+".png"))
def cherries(d,o):
    d.line([(66,91),(91,29),(133,92)],fill="#427b33",width=9,joint="curve")
    d.ellipse((89,25,144,48),fill="#54a246")
    o(61,120,42,(238,25,57));o(131,123,39,(200,10,45))
def lemon(d,o):
    o(95,105,69,(245,215,25),47)
    d.polygon([(21,105),(38,86),(40,124)],fill="#d9b526")
    d.polygon([(167,104),(153,86),(153,122)],fill="#d9b526")
    d.ellipse((99,25,160,58),fill="#479a43")
def orange(d,o):
    o(96,103,69,(255,117,16))
    d.line((96,38,98,21),fill="#556c32",width=8)
    d.ellipse((98,22,154,48),fill="#4ea044")
def grapes(d,o):
    d.line((96,52,104,18),fill="#527136",width=9)
    d.ellipse((102,18,153,43),fill="#52a044")
    for x,y in [(63,65),(120,65),(40,103),(92,104),(145,103),(65,142),(120,142),(93,166)]:
        o(x,y,27,(147,61,221))
def bell(d,o):
    d.rounded_rectangle((62,30,130,68),radius=22,fill="#9d6514")
    for i in range(36):
        t=i/35
        d.polygon([(37+i/2,141-i/3),(55+i/2,68),(80,41+i/2),(114,41+i/2),(138-i/2,68),(155-i/2,141-i/3)],fill=(int(155+95*t),int(91+112*t),int(15+55*t)))
    d.rounded_rectangle((28,133,164,151),radius=9,fill="#f5cb59",outline="#a86b19",width=3)
    o(96,155,15,(234,166,47))
def star(d,o):
    pts=[]
    for i in range(10):
        a=-math.pi/2+i*math.pi/5;r=80 if i%2==0 else 37
        pts.append((96+math.cos(a)*r,96+math.sin(a)*r))
    d.polygon(pts,fill="#ae761b",outline="#f4ca60",width=5)
    for i in range(0,10,2):
        d.polygon([(96,96),pts[i],pts[(i+1)%10]],fill="#ffe07b")
        d.polygon([(96,96),pts[(i-1)%10],pts[i]],fill="#df9d20")
def seven(d,o):
    p=[(43,39),(150,39),(150,65),(97,155),(59,155),(111,72),(43,72)]
    d.polygon([(x+5,y+6) for x,y in p],fill="#570e19")
    d.polygon(p,fill="#ed163d",outline="#ffe27c",width=7)
    d.line([(51,47),(140,47)],fill="#ff9a9c",width=5)
for name,fn in [("cherry",cherries),("lemon",lemon),("orange",orange),("grape",grapes),("bell",bell),("star",star),("seven",seven)]:
    icon(name,fn)
(out/"symbols.atlas").write_text("".join('images { image: "/assets/'+n+'.png" }\n' for n in ["cherry","lemon","orange","grape","bell","star","seven"])+"extrude_borders: 2\n")
def wav(name,length,kind):
    samples=[]
    for i in range(int(44100*length)):
        t=i/44100
        if kind=="stop":
            v=(math.sin(2*math.pi*(125*t-80*t*t))*.55+math.sin(2*math.pi*440*t)*.2)*math.exp(-t*26)
        else:
            v=sum(.21*math.sin(2*math.pi*f*t)*math.exp(-max(0,t-j*.09)*8) for j,f in enumerate([523,659,784]) if t>=j*.09)
        samples.append(struct.pack("<h",int(max(-1,min(1,v))*24000)))
    with wave.open(str(out/(name+".wav")),"wb") as f:
        f.setparams((1,2,44100,len(samples),"NONE","not compressed"));f.writeframes(b"".join(samples))
wav("stop",.20,"stop");wav("win",.65,"win")
music=root.parent/"Fortuna-777/audio/casino-jazz.mp3"
if not music.is_file(): raise FileNotFoundError(music)
subprocess.run(["ffmpeg","-v","error","-y","-i",str(music),"-c:a","libvorbis","-q:a","4",str(out/"music.ogg")],check=True)
for name,ext,loop in [("stop","wav",0),("win","wav",0),("music","ogg",1)]:
    (out/(name+".sound")).write_text('sound: "/assets/'+name+'.'+ext+'"\nlooping: '+str(loop)+'\ngain: 1.0\n')
