"""Combine all customer actor briefs into one bookmarked PDF. Requires pypdf."""
import json
import re
from pathlib import Path
from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parent

def build():
    source = (ROOT / 'index.html').read_text(encoding='utf-8')
    files = json.loads(re.search(r'const actorPdfFiles = (\[.*?\]);', source, re.S).group(1))
    output = ROOT / 'output' / 'pdf'
    writer = PdfWriter()
    total_pages = 0
    for filename in files:
        reader = PdfReader(output / filename)
        title = reader.pages[0].extract_text().splitlines()[1]
        writer.append(reader, outline_item=title)
        total_pages += len(reader.pages)
    writer.add_metadata({'/Title': 'Time Attack - All Customer Behaviour Roles', '/Author': 'Ranger Mastery Program'})
    target = output / 'customer-behaviours-all.pdf'
    with target.open('wb') as stream:
        writer.write(stream)
    combined = PdfReader(target)
    assert len(combined.pages) == total_pages
    assert len(combined.outline) == len(files)
    expected = [page.extract_text() for filename in files for page in PdfReader(output / filename).pages]
    assert [page.extract_text() for page in combined.pages] == expected
    print(f'Created {target}: {len(files)} roles, {total_pages} pages, all source content verified.')

if __name__ == '__main__':
    build()
