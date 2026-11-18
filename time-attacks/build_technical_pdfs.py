"""Generate individual technical scenario PDFs and a complete collection from index.html."""
import html
import json
import re
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'output' / 'pdf'

def filename(index, name):
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    return f'technical-{index + 1:02d}-{slug}.pdf'

def build():
    source = (ROOT / 'index.html').read_text(encoding='utf-8')
    raw = re.search(r'const technicalScenarios = (\[.*?\]);', source, re.S).group(1)
    raw = re.sub(r'(?m)^(\s*)(\w+):', r'\1"\2":', raw)
    scenarios = json.loads(raw)
    OUT.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CaseTitle', fontName='Helvetica-Bold', fontSize=23, leading=27, textColor=colors.HexColor('#26384b'), spaceAfter=15))
    styles.add(ParagraphStyle(name='SectionTA', fontName='Helvetica-Bold', fontSize=12, leading=16, textColor=colors.HexColor('#0e6f68'), spaceBefore=12, spaceAfter=6, keepWithNext=True))
    styles.add(ParagraphStyle(name='TextTA', fontName='Helvetica', fontSize=10, leading=14, spaceAfter=7))
    def p(text, style='TextTA'):
        return Paragraph(html.escape(text), styles[style])
    def content(index, case):
        story = [p(f'TECHNICAL SCENARIO {index+1:02d} | {case["level"]} | 30 MINUTES', 'SectionTA'), p(case['name'], 'CaseTitle'), p('Synthetic tabletop assessment | Ranger Mastery Program'), p('Candidate brief', 'SectionTA'), p(case['brief']), p('Known facts', 'SectionTA')]
        story += [p('- '+fact) for fact in case['known']]
        story += [PageBreak(), p('Facilitator and evaluator only', 'CaseTitle'), p(case['name']), p('Keep this page private. Give the candidate only the candidate brief and known facts on the preceding page.'), p('Evidence to release when asked', 'SectionTA')]
        story += [p('- '+fact) for fact in case['hidden']]
        story += [p('Investigation targets', 'SectionTA')]
        story += [p('- '+fact) for fact in case['expected']]
        story += [p('Evaluation guidance', 'SectionTA'), p('Observe scoping, structured thinking under pressure, evidence-led decisions, customer communication, ownership and closure. Record observed evidence using the application\'s 1-5 scale; leave unobserved criteria unrated. Accept equivalent supported approaches rather than requiring a fixed script.')]
        return story
    def footer(canvas, doc):
        canvas.setStrokeColor(colors.HexColor('#0e6f68'))
        canvas.line(44, 39, 551, 39)
        canvas.setFont('Helvetica', 8)
        canvas.drawString(44, 26, 'RANGER MASTERY PROGRAM / TIME ATTACK / INSTRUCTOR MATERIAL')
        canvas.drawRightString(551, 26, str(doc.page))
    def save(name, story, title):
        SimpleDocTemplate(str(OUT / name), pagesize=(595.28, 841.89), leftMargin=44, rightMargin=44, topMargin=40, bottomMargin=55, title=title, author='Ranger Mastery Program').build(story, onFirstPage=footer, onLaterPages=footer)
    collection = []
    for index, case in enumerate(scenarios):
        save(filename(index, case['name']), content(index, case), case['name'])
        if index:
            collection.append(PageBreak())
        collection.extend(content(index, case))
    save('technical-scenarios-all.pdf', collection, 'Time Attack - All technical scenarios')
    print(f'Created {len(scenarios)} individual PDFs and the complete technical collection in {OUT}')

if __name__ == '__main__':
    build()
