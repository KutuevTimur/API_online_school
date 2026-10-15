"""Deterministic artificial handwriting-like samples. Contains no student data."""
import argparse
from pathlib import Path
import json

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import pillow_heif

from src.modules.handlers_files.normalize_photo import normalize_photo


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--font', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(str(args.font), 58)
    small = ImageFont.truetype(str(args.font), 38)
    label_font = ImageFont.truetype(str(args.font), 22)
    pillow_heif.register_heif_opener()
    manifest = []
    panels = []
    for name, color, scale, rotated in [('notebook-12mp',(35,45,68),1,False),
                                        ('faint-pencil-48mp',(160,160,153),2,False),
                                        ('jpeg-rotated',(45,45,55),1,True),
                                        ('heic-phone',(45,45,55),1,False),
                                        ('png-screenshot',(15,15,15),1,False)]:
        image = Image.new('RGB',(4032,3024),(250,249,242))
        draw = ImageDraw.Draw(image)
        for x in range(0,4032,64):
            draw.line((x,0,x,3024),fill=(218,226,233),width=1)
        for y in range(0,3024,64):
            draw.line((0,y,4032,y),fill=(218,226,233),width=1)
        for y in range(160,2800,240):
            draw.text((180,y), 'x^2 + 2x + 1 = (x + 1)^2', font=font, fill=color)
            draw.text((1420,y-15), '3x',font=small,fill=color)
            draw.text((1470,y-30), '2',font=ImageFont.truetype(str(args.font),26),fill=color)
            draw.text((1495,y-15), ' - 7x + 2',font=small,fill=color)
            draw.line((1400,y+38,1720,y+38),fill=color,width=2)
            draw.text((1480,y+45), 'x - 2', font=small,fill=color)
            draw.text((2100,y), '0.125 x 10^(-3) = 1.25 x 10^(-4)',font=small,fill=color)
        # Local glare and faint pencil stress readability rather than optimize size.
        if scale == 2:
            image = image.filter(ImageFilter.GaussianBlur(.25)).resize((8064,6048),Image.Resampling.BICUBIC)
        source = args.output / (name + ('.heic' if name.startswith('heic') else '.png' if name.startswith('png') else '.jpg'))
        if rotated:
            image = image.rotate(90,expand=True)
            exif = Image.Exif(); exif[274] = 6
            image.save(source,format='JPEG',quality=96,exif=exif)
        elif name.startswith('heic'):
            image.save(source,format='HEIF',quality=95)
        elif name.startswith('png'):
            image.save(source,'PNG')
        else:
            image.save(source,'JPEG',quality=96)
        candidate = args.output/(name+'.webp')
        normalize_photo(source,candidate)
        with Image.open(source) as original, Image.open(candidate) as result:
            from PIL import ImageOps
            reference = ImageOps.exif_transpose(original).convert('RGB')
            reference.thumbnail((2560,2560),Image.Resampling.LANCZOS)
            manifest.append({'sample':name,'source_bytes':source.stat().st_size,
                             'webp_bytes':candidate.stat().st_size,'source_size':list(original.size),
                             'webp_size':list(result.size),'metadata_stripped':not bool(result.getexif())})
            # Corresponding crops at equal output scale; no additional shrinkage.
            box=(870,92,1570,482)
            panel=Image.new('RGB',(1440,440),'white'); pd=ImageDraw.Draw(panel)
            pd.text((10,8),name+' / source at matching scale',font=label_font,fill='black')
            pd.text((730,8),'WebP 2560 q85 / 100%',font=label_font,fill='black')
            panel.paste(reference.crop(box),(10,42));panel.paste(result.crop(box),(730,42))
            panels.append(panel)
    sheet=Image.new('RGB',(1440,len(panels)*440),'#eeeeee')
    for i,panel in enumerate(panels):sheet.paste(panel,(0,i*440))
    sheet.save(args.output/'comparison.png')
    (args.output/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps(manifest,indent=2))


if __name__=='__main__':
    main()
