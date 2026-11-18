"""Render every final PDF page and make contact sheets for visual review."""
from pathlib import Path
import subprocess
from pypdf import PdfReader
from PIL import Image, ImageOps, ImageDraw
root = Path(__file__).resolve().parent
tmp = root/'tmp'/'pdfs'
tmp.mkdir(parents=True,exist_ok=True)
pages=[]
for pdf in sorted((root/'output'/'pdf').glob('*.pdf')):
    reader=PdfReader(pdf)
    print(pdf.name, len(reader.pages), 'pages')
    for n,page in enumerate(reader.pages):
        text=page.extract_text()
        assert text and len(text)>150, (pdf,n)
    subprocess.run(['pdftoppm','-scale-to','900','-png',str(pdf),str(tmp/pdf.stem)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    for path in sorted(tmp.glob(pdf.stem+'-*.png')): pages.append(path)
for start in range(0,len(pages),12):
    sheet=Image.new('RGB',(1200,4*450),'#ccd4dc')
    draw=ImageDraw.Draw(sheet)
    for k,path in enumerate(pages[start:start+12]):
        im=Image.open(path).convert('RGB'); im.thumbnail((386,417))
        x=(k%3)*400; y=(k//3)*450
        sheet.paste(im,(x,y+24));draw.text((x+4,y+4),path.stem[:53],fill='black')
    sheet.save(tmp/f'contact-{start//12+1}.png')
print('Rendered',len(pages),'pages')
