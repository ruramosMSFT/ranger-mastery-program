from pathlib import Path
from pypdf import PdfReader
import json,re
from PIL import Image,ImageOps,ImageDraw
import subprocess
root=Path('time-attacks');s=(root/'index.html').read_text(encoding='utf-8');cases=json.loads(re.search(r'const technicalScenarios = (\[.*?\]);',s,re.S).group(1));files=sorted((root/'output/pdf').glob('technical-[0-9]*.pdf'));assert len(files)==len(cases)==15
thumbs=[]
for i,f in enumerate(files):
    pdf=PdfReader(f);text='\n'.join(p.extract_text() for p in pdf.pages)
    assert cases[i]['name'] in text
    assert all(x in text for x in ['Candidate brief','Known facts','Investigation targets','Facilitator and evaluator only'])
    assert len(pdf.pages)==2,(f,len(pdf.pages))
    prefix=root/'tmp/pdfs'/f.stem
    subprocess.run(['pdftoppm','-scale-to','650','-png',str(f),str(prefix)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    for image in sorted(prefix.parent.glob(prefix.name+'-*.png')):
        im=Image.open(image).convert('RGB');im.thumbnail((290,410));thumb=Image.new('RGB',(310,440),'#d8e0ea');thumb.paste(im,((310-im.width)//2,10));ImageDraw.Draw(thumb).text((10,420),image.stem[:46],fill='black');thumbs.append(thumb)
assert len(PdfReader(root/'output/pdf/technical-scenarios-all.pdf').pages)==30
sheet=Image.new('RGB',(310*6,440*5),'white')
for i,t in enumerate(thumbs):sheet.paste(t,((i%6)*310,(i//6)*440))
sheet.save(root/'tmp/pdfs/technical-contact-sheet.png');print('PASS: all 15 PDF contents, two-page layout, combined 30-page collection; rendered all pages')
