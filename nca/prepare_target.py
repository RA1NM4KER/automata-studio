"""Prepare a local 64px RGBA target. It is deliberately separate from playback."""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageOps

def synthetic(size):
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(image)
    d.ellipse((14, 5, 50, 53), fill=(91, 50, 31, 255))
    d.ellipse((18, 13, 46, 42), fill=(116, 72, 47, 255))
    d.ellipse((22, 24, 26, 28), fill=(16, 16, 20, 255)); d.ellipse((38, 24, 42, 28), fill=(16, 16, 20, 255))
    d.arc((25, 27, 41, 38), 10, 170, fill=(38, 18, 16, 255), width=2)
    d.polygon([(17, 43), (47, 43), (57, 63), (7, 63)], fill=(25, 84, 108, 255))
    return image

def main():
    p=argparse.ArgumentParser(); p.add_argument('--input'); p.add_argument('--name', default='synthetic-smoke'); p.add_argument('--size', type=int, default=64); p.add_argument('--margin',type=int,default=0); p.add_argument('--circle-mask', action='store_true'); p.add_argument('--zoom',type=float,default=1.0); p.add_argument('--center-x',type=float,default=.5); p.add_argument('--center-y',type=float,default=.5); p.add_argument('--posterize-bits',type=int,choices=range(1,9),default=8); p.add_argument('--contrast',type=float,default=1); p.add_argument('--sharpness',type=float,default=1); a=p.parse_args()
    out=Path('nca-inputs'); out.mkdir(exist_ok=True); dest=out/f'{a.name}.png'
    if a.input:
        content=a.size-2*a.margin
        if content<1: raise ValueError('margin leaves no target pixels')
        image=Image.open(a.input).convert('RGBA'); w,h=image.size; side=max(1,round(min(w,h)/a.zoom)); left=max(0,min(w-side,round(w*a.center_x-side/2))); top=max(0,min(h-side,round(h*a.center_y-side/2))); image=image.crop((left,top,left+side,top+side)).resize((content,content),Image.Resampling.LANCZOS)
        alpha=image.getchannel('A'); rgb=ImageEnhance.Contrast(image.convert('RGB')).enhance(a.contrast); rgb=ImageEnhance.Sharpness(rgb).enhance(a.sharpness); rgb=ImageOps.posterize(rgb,a.posterize_bits); image=rgb.convert('RGBA'); image.putalpha(alpha)
        if a.circle_mask:
            mask=Image.new('L',(content,content)); ImageDraw.Draw(mask).ellipse((1,1,content-2,content-2),fill=255); image.putalpha(mask)
        if a.margin:
            canvas=Image.new('RGBA',(a.size,a.size)); canvas.paste(image,(a.margin,a.margin),image); image=canvas
    else: image=synthetic(a.size)
    image.save(dest); print(dest)
if __name__=='__main__': main()
