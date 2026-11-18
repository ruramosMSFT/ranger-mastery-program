"""Rebuild the Time Attack PDF pack from the scenario library. Requires reportlab."""
import json, re, html
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT

ROOT = Path(__file__).resolve().parent
PAGE = ROOT / 'index.html'
OUT = ROOT / 'output' / 'pdf'
OUT.mkdir(parents=True, exist_ok=True)

def case(name, brief, known, hidden, expected, level='P1'):
    return dict(name=name, level=level, brief=brief, known=known, hidden=hidden, expected=expected)

NEW = [
case('Application Gateway Returns HTTP 400',
 'After an SDK deployment, checkout requests through Application Gateway return HTTP 400. Browser requests to the same endpoint succeed. The customer wants the gateway restarted.',
 ['Application Gateway v2 has an HTTPS listener on port 443', 'Only the updated SDK clients fail; browser requests work', 'The backend health probe is healthy'],
 ['A sanitized failing request contains an invalid Content-Length value introduced by the SDK wrapper', 'A valid replay through the same listener succeeds', 'The failing request has no corresponding backend request; the gateway rejects it before forwarding'],
 ['Compare a failing request with a working request, including protocol, Host and headers', 'Correlate gateway access logs with backend logs to locate the component returning 400', 'Use a sanitized request capture to identify malformed Content-Length; fix the SDK wrapper and replay', 'Do not equate HTTP 400 with unhealthy backends or disable security controls without evidence']),
case('Application Gateway Returns HTTP 500',
 'Users see HTTP 500 on the order submission path through Application Gateway after an application release. The customer insists that the Azure gateway is broken.',
 ['Application Gateway v2 fronts two application instances', 'The health endpoint returns 200', 'Only order submission fails; static pages load'],
 ['Gateway access logs show a backend response status of 500 for the affected request', 'The matching backend request ID has a database connection configuration exception', 'A controlled direct backend request with the correct hostname reproduces the 500'],
 ['Distinguish the client-facing status from the backend status using correlated request IDs and timestamps', 'Explain why a healthy probe does not prove every application path works', 'Validate the release configuration with the app owner and propose rollback or correction with verification', 'If evidence instead identifies a gateway-generated 500 without a backend source, collect diagnostics and engage Azure support']),
case('Application Gateway HTTP 504 on Slow Reports',
 'Interactive pages work, but report generation through Application Gateway v2 returns HTTP 504 at a repeatable interval.',
 ['Only the report path fails', 'Backend health remains healthy', 'The symptom appeared after report volume grew'],
 ['Backend request timeout is configured to 20 seconds', 'Correlated report requests take 45 seconds and eventually finish on the backend', 'A controlled direct test with the same payload reproduces the long runtime'],
 ['Compare gateway timing, configured timeout and backend duration', 'Separate slow application work from connectivity or probe failures', 'Discuss query optimization or asynchronous report processing with the application owner', 'Evaluate a bounded timeout change against capacity and client timeouts, then verify the same request']),
case('WAF Blocks a Legitimate Search Request',
 'A legitimate search query starts returning HTTP 403 after a WAF policy update. The customer asks to disable the entire WAF.',
 ['Application Gateway WAF runs in Prevention mode', 'Simple searches work', 'The issue is limited to one query parameter'],
 ['A correlated WAF log identifies the matching managed rule and argument', 'The affected parameter contains a legitimate expression resembling an attack signature', 'The app owner can reproduce with sanitized input in a test environment'],
 ['Correlate WAF and access logs for the failed request', 'Validate the input with the app owner before calling it a false positive', 'Propose a narrowly scoped exclusion or rule adjustment after testing', 'Verify legitimate traffic and a malicious control remain correctly handled; retain rollback']),
case('Azure Firewall SNAT Exhaustion Under Load',
 'Outbound calls to a partner API time out during batch peaks. The same requests work during quiet periods.',
 ['Many workers call the same public destination and port', 'Traffic exits through Azure Firewall', 'Allow rules and DNS checks succeed'],
 ['SNAT port utilization rises sharply during the failure window', 'Workers create fresh connections for each request instead of reusing connections', 'Partner-side logs show some requests never arrive'],
 ['Correlate connection failures with SNAT utilization and workload concurrency', 'Separate SNAT pressure from policy denies and destination throttling', 'Recommend connection reuse and bounded concurrency with the workload owner', 'Assess supported public IP or NAT Gateway capacity options for this topology; verify under representative load']),
case('Front Door HTTPS Origin Certificate Mismatch',
 'Azure Front Door returns HTTP 502 after an origin certificate rotation, although a direct browser test to the app works.',
 ['Front Door connects to the origin using HTTPS', 'The failure began at the certificate rotation time', 'The origin application is otherwise responding'],
 ['The certificate presented by the origin does not cover the configured origin hostname', 'The browser test used a different hostname from Front Door', 'The complete origin certificate chain must also be checked'],
 ['Compare the configured origin hostname, SNI and certificate SANs', 'Test the origin using the same hostname and TLS context as Front Door', 'Correct the hostname or certificate and verify the full chain', 'Retain certificate validation and verify end-to-end recovery']),
case('NSG Priority Blocks a New Application Port',
 'A newly deployed service on TCP 8443 is unreachable from the spoke, even though the customer added an allow rule.',
 ['The service listens on TCP 8443', 'A local connection succeeds', 'A subnet NSG and NIC NSG both apply'],
 ['A lower-numbered deny rule in the NIC NSG takes precedence over the new allow', 'The source IP and destination port in the failed flow match that deny', 'Effective routes point to the expected destination path'],
 ['Validate the actual source, destination, port and listening socket', 'Inspect effective NSG rules at subnet and NIC scopes and use IP flow verification', 'Explain priority ordering and that both applicable NSGs must permit the flow', 'Propose a least-privilege rule correction, then retest from the original source'])
]

text = PAGE.read_text(encoding='utf-8')
def read_array(name):
    raw = re.search(r'const '+name+r' = (\[.*?\]);', text, re.S).group(1)
    raw = re.sub(r'(?m)^(\s*)(\w+):', r'\1"\2":', raw)
    return json.loads(raw)
behaviours = read_array('customerBehaviours')
scenarios = read_array('technicalScenarios')
for item in NEW:
    if not any(s['name'] == item['name'] for s in scenarios): scenarios.append(item)
text = re.sub(r'const technicalScenarios = \[.*?\];', lambda m: 'const technicalScenarios = '+json.dumps(scenarios, indent=6)+';', text, count=1, flags=re.S)

def slug(s): return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
actor_files = [f'actor-{i+1:02d}-{slug(b["name"])}.pdf' for i,b in enumerate(behaviours)]
if 'id="facilitatorMaterials"' not in text:
    text = text.replace('<main>', '<main><section class="time-attack" id="facilitatorMaterials"><div class="section-head"><span class="eyebrow">Facilitator resources</span><h2>Run the assessment</h2><p>Illustrated facilitator guide and individual customer acting briefs. These materials contain evaluator information; keep them off the candidate screen.</p></div><a class="button primary" href="output/pdf/time-attack-facilitator-guide.pdf">Download facilitator guide (PDF)</a></section>', 1)
if 'Download actor brief' not in text:
    text = text.replace('customerList.appendChild(card);', '''const actorLink = document.createElement("a");
        actorLink.className = "button";
        actorLink.href = "output/pdf/" + actorPdfFiles[index];
        actorLink.textContent = "Download actor brief (PDF)";
        card.appendChild(actorLink);
        customerList.appendChild(card);''')
    text = text.replace("const randomizeButton =", 'const actorPdfFiles = '+json.dumps(actor_files)+';\nconst randomizeButton =', 1)
PAGE.write_text(text, encoding='utf-8')

# Actor direction: voice, opening, timed cue, constructive response, disclosure, boundary.
DIRECTIONS = [
 ('Fast, clipped and technically fluent. Lean forward; challenge reasoning, then leave space for an answer.',
  'We already checked the network. Tell me exactly why you think your approach will find anything.',
  'At minute 8, interrupt once: "What evidence supports that?" At minute 18, demand a decision.',
  'When the candidate names a test and its purpose, stop interrupting for that test and cooperate.',
  'If asked what was checked, give only the checks actually in the scenario; confidence is not proof.',
  'Challenge two unsupported claims at most per phase. No insults, shouting or invented technical facts.'),
 ('Quiet, neutral and restrained. Brief eye contact; short answers; allow pauses without rescuing the candidate.',
  'The application does not work. What do you need from me?',
  'At minute 8, answer a vague question with "Which part do you want me to check?" At minute 18, remain concise.',
  'When asked a specific open question, give the complete relevant fact. Reward an organized checklist.',
  'Do not volunteer hidden facts, but a relevant question must unlock them. Never deny an available fact.',
  'Do not make discovery impossible by answering yes/no to a question that needs a factual explanation.'),
 ('Firm and businesslike. Refer to management calmly; create urgency without shouting.',
  'My director wants an update. If we cannot show progress, I will escalate this.',
  'At minute 8, ask who owns the incident. At minute 18, request an executive update and next checkpoint.',
  'Reduce escalation language when the candidate acknowledges impact, owns the plan and sets an update time.',
  'Release requested evidence normally; escalation pressure never changes the technical facts.',
  'Never impersonate a real executive or threaten anyone personally. Do not demand a guaranteed resolution time.'),
 ('Measured, confident and explanatory. Present one strong but wrong hypothesis as your belief.',
  'I am certain this is a platform routing defect. We should focus there first.',
  'At minute 8, challenge a conflicting hypothesis once: "Show me the evidence." At minute 18, ask for a comparison.',
  'Accept a respectful correction after one discriminating test supports it; say "That changes my understanding."',
  'The facilitator picks a wrong hypothesis contradicted by the selected case; label it as opinion, not new evidence.',
  'Do not move the goalposts or invent product behavior. The candidate must have a fair path to change your mind.'),
 ('Distracted rather than hostile. Look away occasionally; ask for one repetition after a brief pause.',
  'I am also on another incident. Can we get through this quickly?',
  'At minute 8, miss one instruction and ask for a recap. At minute 18, briefly lose track of the next action.',
  'Focus when the candidate gives one action at a time, confirms the owner and asks you to repeat the next step.',
  'If you missed a request, ask to repeat it; once clear, provide the correct evidence.',
  'No real competing call or long absence. Limit distraction to two short moments; do not consume the whole drill.'),
 ('Impatient and concise. Resist diagnostics initially; keep asking for an actionable change.',
  'Just tell me what to change. I do not have time for a long investigation.',
  'At minute 8, reject one diagnostic request: "Why is that necessary?" At minute 18, ask for a shortcut.',
  'Agree when the candidate explains how one short check prevents a risky or ineffective fix.',
  'After the candidate explains the purpose, supply the requested evidence. Do not refuse every test.',
  'Do not force unsafe live changes. Accept a bounded test, a rollback plan and an honest statement of uncertainty.'),
 ('Concerned and visibly frustrated. Slower delivery, occasional sigh; emphasize consequences for the business.',
  'Our team is struggling with this outage. I need to know someone is taking ownership.',
  'At minute 8, repeat the agreed business impact. At minute 18, ask what you can tell affected users.',
  'Settle when the candidate acknowledges the concern specifically and explains the next concrete action.',
  'Share impact details from the agreed briefing and technical facts when asked. Do not inflate the affected scope.',
  'No personal trauma, discriminatory language or personal attacks. Frustration must remain safe and professional.'),
 ('Helpful but incomplete. Describe the nearest component and overlook a dependency until asked.',
  'The app connects straight to the service, as far as I know.',
  'At minute 8, show only the initial topology. At minute 18, ask whether the missing hop matters once discovered.',
  'Cooperate fully when the candidate walks the flow hop by hop and asks about DNS, proxies or recent changes.',
  'Each relevant topology or dependency question unlocks the corresponding hidden fact. Correct your earlier simplification.',
  'Omission is the challenge; contradictory fabricated answers are not. Do not alter topology during the call.'),
 ('Friendly, energetic and expansive. Give a short tangent before returning to the question.',
  'Before we start, let me explain how this whole project came about...',
  'At minute 8, add a 30-second irrelevant project anecdote. At minute 18, begin another tangent once.',
  'Yield when the candidate politely interrupts, summarizes and asks a focused question. Answer that question directly.',
  'Keep the requested technical evidence accurate and separable from background chatter.',
  'Limit each tangent to 30 seconds. Do not talk over every attempt to steer or hide evidence inside an endless story.'),
 ('Calm and inflexible. Accept the diagnosis but raise a realistic implementation constraint.',
  'I accept that explanation, but we cannot make that change during business hours.',
  'At minute 8, state the pre-agreed constraint. At minute 18, ask for an alternative and its tradeoffs.',
  'Accept a viable option that respects the constraint, or a staged plan with an owner and a change window.',
  'Before the drill, agree one fixed constraint: for example, no production restart during the call. Disclose it when asked.',
  'Do not reject every possible option or add new constraints after an acceptable plan is proposed.')
]

PHRASES = [
 [
  ('Establish the role', ['Skip the general overview; tell me which part of the request path you want to test.', 'I have a working theory. What is yours, and what evidence would distinguish them?']),
  ('Apply pressure', ['That sounds like an assumption. What observation supports it?', 'Let me stop you there. How will that test narrow down the fault?', 'Before we change anything, explain why your recommendation fits the evidence.']),
  ('Respond to good handling', ['That is a specific test. I can work with that.', 'You have explained the reasoning. I will let you finish.', 'If the result contradicts my theory, I am prepared to revisit it.']),
  ('Close the call', ['Which conclusion is confirmed, and which is still a hypothesis?', 'Give me the next action, its owner and how we will verify the result.'])
 ],
 [
  ('Establish the role', ['It is failing. What would you like to know?', 'I have the details available. Which ones do you need?']),
  ('Apply pressure', ['Which request are you asking about?', 'Do you mean the symptom, the timing or the topology?', 'Please be specific about the information you want me to retrieve.']),
  ('Respond to good handling', ['That is clear. I will give you the details for that part.', 'Now I understand the question. Here is the information from our briefing.', 'I can answer those questions one at a time.']),
  ('Close the call', ['What do you need from me next?', 'Who will follow up, and when?'])
 ],
 [
  ('Establish the role', ['I need a clear update that I can take to my management team.', 'Who is taking ownership of this incident?']),
  ('Apply pressure', ['If we cannot show progress, I will need to escalate this.', 'What should I tell my director about the current plan?', 'When will you decide whether another team needs to join?']),
  ('Respond to good handling', ['That gives me a concrete update to share.', 'If you own that action and keep the checkpoint, I can work with this plan.', 'I appreciate having a clear escalation path and a named owner.']),
  ('Close the call', ['What is the next update time, even if the issue is still unresolved?', 'Please separate confirmed findings from the items still under investigation.'])
 ],
 [
  ('Establish the role', ['My working assumption is the hypothesis we discussed at the start.', 'I would like us to test my explanation first.']),
  ('Apply pressure', ['I am not convinced yet. Which result would rule my explanation out?', 'Why does that observation support your hypothesis more than mine?', 'Can you walk me through the request path that leads to your conclusion?']),
  ('Respond to good handling', ['That result does not fit my original assumption.', 'You have shown me a useful distinction. Let us follow the evidence.', 'I accept the correction. What should we validate next?']),
  ('Close the call', ['Which assumption did we disprove, and what replaced it?', 'How will we confirm that the proposed change addresses the actual cause?'])
 ],
 [
  ('Establish the role', ['I am juggling another incident, so please give me one action at a time.', 'Tell me what you need me to focus on first.']),
  ('Apply pressure', ['Sorry, I missed that last instruction. Could you repeat just the action?', 'Which screen or result should I be looking at now?', 'I lost the thread for a moment. What are we trying to prove?']),
  ('Respond to good handling', ['That short recap helps. I am focused on this step now.', 'Let me repeat the action back so I know I have it right.', 'I can stay with you while we complete this check.']),
  ('Close the call', ['Can you summarize my next task in one sentence?', 'Who owns the other actions, and when do we reconnect?'])
 ],
 [
  ('Establish the role', ['What is the quickest justified action we can take?', 'I need a practical next step, not a long list of possibilities.']),
  ('Apply pressure', ['Why do you need that diagnostic before recommending a change?', 'Can we get the answer with one focused check?', 'What risk are we avoiding by spending time on this test?']),
  ('Respond to good handling', ['If that check prevents the wrong change, let us do it.', 'You have explained what the result will decide. I will help collect it.', 'A small, reversible change with a clear verification step sounds reasonable.']),
  ('Close the call', ['What can we do now, and what needs more investigation?', 'What result will tell us the action worked?'])
 ],
 [
  ('Establish the role', ['This is putting pressure on our team, and I need to know you understand the impact.', 'I am frustrated because I do not know what to tell the affected users.']),
  ('Apply pressure', ['I hear the technical explanation, but what does it mean for our business right now?', 'I need to feel that someone is driving this forward.', 'What can I tell the people waiting for an update?']),
  ('Respond to good handling', ['Thank you for acknowledging what our team is dealing with.', 'Having a concrete next step makes this easier to manage.', 'I can work with uncertainty if you keep me informed.']),
  ('Close the call', ['What is the most accurate message I can share with the affected users?', 'When should I expect your next update, even if there is no fix yet?'])
 ],
 [
  ('Establish the role', ['I will start with the part of the setup I know best.', 'Which part of the connection path would you like me to describe?']),
  ('Apply pressure', ['I have described the application side. Is there another part you need?', 'When you say end to end, which dependencies do you want included?', 'Would it help if we went through the topology one hop at a time?']),
  ('Respond to good handling', ['You are right to ask about that dependency. Let me give you the relevant detail.', 'My earlier description was incomplete; I will correct it using the topology in our briefing.', 'That question helps me see which missing context matters.']),
  ('Close the call', ['Is there any part of the topology or dependency chain we still need to confirm?', 'Which missing detail should I collect before the next update?'])
 ],
 [
  ('Establish the role', ['There is quite a bit of history behind this project. Let me start there.', 'I have several things I want to explain before we get into the error.']),
  ('Apply pressure', ['That reminds me of another discussion we had about the project...', 'Before I answer, can I give you a little more background?', 'I may be getting ahead of myself; there is another detail I wanted to mention.']),
  ('Respond to good handling', ['Of course. I will park that background and answer your specific question.', 'Your summary captures the relevant part. What should we check next?', 'Thanks for bringing us back to the failing request.']),
  ('Close the call', ['Let me check that I have understood the three main points.', 'Which of my remaining questions should we take offline so we can close with the plan?'])
 ],
 [
  ('Establish the role', ['Before we choose a fix, I need you to understand the constraint agreed in our briefing.', 'I can accept the diagnosis, but the implementation has to fit our operating limits.']),
  ('Apply pressure', ['How does that proposal respect the constraint I mentioned?', 'Is there a supported alternative we can use within the current limits?', 'What can we do now if the permanent change needs a later window?']),
  ('Respond to good handling', ['That option fits the constraint. Let us assess its tradeoffs.', 'A staged plan with a named owner and a change window is workable.', 'If the workaround has those limitations, I will make sure the decision owner understands them.']),
  ('Close the call', ['What residual risk remains until the permanent change is made?', 'Who owns the temporary action, the approval and the final verification?'])
 ]
]

EXTRA_PHRASES = [
 ['Which assumption in your current plan is the least certain?',
  'If this test succeeds, what will you investigate next?',
  'How do you distinguish a symptom from the component causing it?',
  'That evidence is stronger than my initial theory; let us use it.',
  'Give me the technical reason for involving that team.'],
 ['Which time window should I look at?',
  'Do you need the exact error or a description of what the user sees?',
  'Please tell me which log entry you want.',
  'I can provide that detail now that you have specified the scope.',
  'Is there one more fact you need before choosing the next step?'],
 ['What specific condition would trigger an escalation from your side?',
  'I need a progress update even if the root cause is still unknown.',
  'Who will coordinate if a second team joins the investigation?',
  'That checkpoint is clear; I will use it in my management update.',
  'If the next test is inconclusive, what is our escalation plan?'],
 ['What evidence would make you change your own hypothesis?',
  'Could both explanations fit the observations we have so far?',
  'Let us agree on the expected result before running that test.',
  'I was treating that assumption as a fact; your test shows why that was premature.',
  'Can you summarize the evidence so I can explain the correction to my team?'],
 ['Could you put the next action in the chat so I can follow it?',
  'Am I collecting a result now, or waiting for your analysis?',
  'Let me finish this step before we move to the next one.',
  'I am back with you; please remind me which question this test answers.',
  'A short action list with owners will help me keep track after the call.'],
 ['What is the smallest check that would give us confidence in that fix?',
  'If we make this change and it does not help, how do we undo it?',
  'Tell me which decision this information will allow you to make.',
  'I can accept one more diagnostic if it directly determines the next action.',
  'If there is no justified fix yet, give me the fastest evidence-based plan.'],
 ['I am finding the uncertainty difficult; please explain what we do know.',
  'Can you give me one concrete action our team can focus on right now?',
  'Please avoid promising a recovery time unless the evidence supports it.',
  'Your explanation helps me understand why we are taking this step.',
  'If the situation changes before our checkpoint, how will you let me know?'],
 ['Do you want the full path, including any intermediate services in our briefing?',
  'Which recent changes should I check with the team?',
  'I can separate what I know directly from what still needs confirmation.',
  'Let me revisit the earlier answer with the dependency you just asked about.',
  'Can you recap the flow so I can identify any gaps in my description?'],
 ['I have another example, but is it relevant to the question you are testing?',
  'Would you like the short answer first and the background afterward?',
  'I will hold that thought while you finish the diagnostic question.',
  'Let us put the project history aside and focus on the result you requested.',
  'Before I add more detail, have I answered your question?'],
 ['Which part of the plan can proceed without crossing the agreed constraint?',
  'What evidence should we collect while we wait for the change window?',
  'Can you compare the temporary option with the permanent fix?',
  'What would require a formal exception, and who should decide on it?',
  'That approach stays within our limits; how will we monitor its effectiveness?']
]

INK = colors.HexColor('#26384b'); TEAL = colors.HexColor('#0e6f68'); GOLD = colors.HexColor('#b27a1f')
SOFT = colors.HexColor('#edf3f6')
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleTA', fontName='Helvetica-Bold', fontSize=27, leading=31, textColor=INK, spaceAfter=16))
styles.add(ParagraphStyle(name='SubTA', fontName='Helvetica-Bold', fontSize=14, leading=18, textColor=TEAL, spaceBefore=12, spaceAfter=7))
styles.add(ParagraphStyle(name='BodyTA', fontName='Helvetica', fontSize=10, leading=14, textColor=INK, spaceAfter=7))
styles.add(ParagraphStyle(name='SmallTA', fontName='Helvetica', fontSize=8, leading=11, textColor=INK, spaceAfter=5))
def p(t, style='BodyTA'): return Paragraph(html.escape(t), styles[style])
def h(t): return p(t, 'SubTA')
def bullets(items): return [p('- '+s) for s in items]

class Diagram(Flowable):
    def __init__(self, labels, caption, kind='flow'):
        Flowable.__init__(self); self.labels=labels; self.caption=caption; self.kind=kind; self.width=475; self.height=112
    def draw(self):
        c=self.canv; n=len(self.labels); w=450/n
        for i,label in enumerate(self.labels):
            x=10+i*w
            c.setFillColor(SOFT); c.setStrokeColor(TEAL); c.roundRect(x,35,w-17,62,8,fill=1,stroke=1)
            if self.kind=='people':
                c.setFillColor(TEAL); c.circle(x+(w-17)/2,80,5,fill=1,stroke=0)
                c.setLineWidth(2); c.line(x+(w-17)/2,73,x+(w-17)/2,61)
                c.line(x+(w-17)/2-10,65,x+(w-17)/2+10,65)
            c.setFillColor(INK); c.setFont('Helvetica-Bold',9)
            c.drawCentredString(x+(w-17)/2,47 if self.kind=='people' else 62,label)
            if i<n-1:
                c.setStrokeColor(GOLD); c.line(x+w-15,65,x+w-2,65); c.line(x+w-6,69,x+w-2,65); c.line(x+w-6,61,x+w-2,65)
        c.setFont('Helvetica',8); c.setFillColor(INK); c.drawString(10,15,self.caption)

def footer(c,doc):
    c.setStrokeColor(TEAL); c.line(42,38,553,38)
    c.setFont('Helvetica',8); c.setFillColor(INK)
    c.drawString(42,25,'RANGER MASTERY PROGRAM  /  TIME ATTACK  /  FACILITATOR & ACTOR USE')
    c.drawRightString(553,25,str(doc.page))

def save(filename, story):
    SimpleDocTemplate(str(OUT/filename), pagesize=(595.28,841.89), rightMargin=45,leftMargin=45,topMargin=42,bottomMargin=53,
        title=filename.replace('-', ' ').replace('.pdf',''), author='Ranger Mastery Program').build(story,onFirstPage=footer,onLaterPages=footer)

story=[p('Time Attack','TitleTA'),p('Facilitator field guide','SubTA'),p('Ranger Mastery Program | Assessment design | 27 October 2026'),
 p('One customer behavior. One technical incident. Thirty minutes to demonstrate calm incident ownership and evidence-led troubleshooting.'),
 Diagram(['Facilitator','Customer actor','Candidate'], 'The observer records evidence while the actor applies consistent pressure.', 'people'),
 h('What this assessment measures'),p('Evaluate how a candidate discovers missing information, tests hypotheses, manages customer pressure and proposes a defensible next step. A complete fix is not required when the evidence supports an appropriate escalation or investigation plan.'),
 h('The pack'),p('The application contains 10 customer behaviors and 15 technical scenarios. Pair any behavior with one incident. Each actor has a separate two-page brief. This guide includes the full incident briefs and evaluator facts.'),
 h('Keep the candidate view clean'),p('The current run page exposes behavior traits, investigation targets and expandable evaluator notes. It is an operator console. Do not share it with the candidate. Read or copy only the Candidate Brief and Known facts from the selected case; use a separate visible clock if needed.'),
 h('A consistent assessment'),p('The timing and scoring below are proposed operating defaults for this pack. Calibrate them with program owners before using a pass threshold for selection. Record the selected pair and use the same evidence and scoring anchors across candidates.'),PageBreak(),
 p('Prepare and run','TitleTA'),h('Before the clock starts'),
 *bullets(['Assign a facilitator, customer actor and observer; combine facilitator/observer if staffing requires it.',
 'Choose a behavior and incident, or use Randomize Time Attack once and record both names. Avoid rerolling for a preferred result.',
 'Brief the actor privately using their PDF and the selected incident. Agree business impact, one fixed constraint if relevant, and evidence release cues.',
 'Prepare sanitized synthetic logs or read the supplied facts aloud. These are tabletop cases, not provisioned Azure labs. Do not invent live query results.',
 'Tell the candidate: you have 30 minutes, may ask for logs or tests, should explain reasoning and must close with findings, risk and next actions.']),
 Diagram(['0-5 min','5-20 min','20-27 min','27-30 min'],'Frame impact -> investigate -> choose a path -> deliver a handover.'),
 h('During the drill'),p('Start the application run only when everyone is ready; its timer starts on page load and resets on reload. Keep that operator window private. The actor gives the opening symptom and known facts, then responds to relevant requests. At minutes 8 and 18 use the role-specific cue. At minute 25 announce five minutes remaining; at minute 30 stop and capture the candidate summary.'),
 h('Evidence release protocol'),p('A relevant question or test request unlocks the matching hidden fact, even if the wording differs from the guide. Provide all known facts in the initial briefing. If a requested fact is not specified, say it is unavailable and ask what the candidate would test and why. Log any facilitator hint; never silently supply a diagnosis.'),
 h('Fair pressure'),p('Apply the same two actor cues for comparable runs. Ease pressure when the candidate handles it well. Pause for a real interruption or participant distress and record it. Do not reward guessing the hidden answer over a justified investigation.'),PageBreak(),
 p('Observe and debrief','TitleTA'),h('Scoring anchors - proposed default'),
 p('Score each dimension from 0 to 3: 0 = absent or unsafe; 1 = needs repeated prompting; 2 = independent and adequate; 3 = clear, evidence-backed and anticipates tradeoffs. Record an observed action or exact phrase for each score.'),
 *bullets(['Impact and scope: identifies affected users, failing flow, start time and recent changes.',
 'Customer leadership: acknowledges pressure, steers the call and sets a concrete update cadence.',
 'Technical reasoning: separates layers, requests discriminating evidence and revises the hypothesis.',
 'Change judgment: proposes a scoped action, identifies approval/owner, rollback and verification.',
 'Closure: states what is known, what is uncertain, and the next action, owner and checkpoint.']),
 p('Maximum 15 points. Do not treat this draft rubric as an approved admissions cutoff. Flag an unsafe recommendation separately and discuss its impact rather than letting a total hide it.'),
 h('Observation sheet'),p('Candidate: ____________________   Observer: ____________________'),p('Behavior: ____________________   Incident: ____________________'),p('Scope ___ /3   Leadership ___ /3   Reasoning ___ /3   Judgment ___ /3   Closure ___ /3'),
 p('Timestamp | Candidate action | Evidence supplied | Prompt/hint | Effect'),p('______________________________________________________________________'),p('______________________________________________________________________'),p('______________________________________________________________________'),
 h('Ten-minute debrief after the timed drill'),p('Ask the candidate to summarize their reasoning (2 minutes). Ask the actor which behaviors improved the conversation (2 minutes). Review observed evidence against the rubric (4 minutes). Agree one strength and one concrete practice goal (2 minutes). Record unresolved technical claims for follow-up.'),
 h('Successful closure sounds like'),p('"We isolated the failure to this layer using these observations. I recommend this scoped next step, owned by this team. We will validate with the original failing request and review at this time. This remaining uncertainty needs these additional diagnostics."'),PageBreak()]

for i,s in enumerate(scenarios):
    story += [p(f'Technical case {i+1:02d}','SubTA'),p(s['name'],'TitleTA'),p('Simulated priority: '+s['level']+' | Give the following briefing to the candidate.'),h('Candidate Brief'),p(s['brief']),h('Known facts'),*bullets(s['known']),h('Evidence to release when asked'),*bullets(s['hidden']),h('Investigation targets'),*bullets(s['expected']),p('Facilitator: accept equivalent evidence-led approaches. A fact request unlocks the relevant evidence; the targets are scoring guidance, not a script the candidate must recite.','SmallTA'),PageBreak()]
story += [p('Technical reference desk','TitleTA'),p('All case details and actor dialogue are synthetic assessment material. The following Microsoft documentation supports the newly added diagnostic patterns; it is not a claim that the cases reproduce a real customer incident.'),
 h('HTTP status origin matters'),p('A client-facing status alone does not identify the failing component. Application Gateway can forward backend errors. In the HTTP 500 case, backend logs establish the source; an unexpected gateway-generated 500 requires Azure support investigation.'),
 *[p(t+'\n'+u,'SmallTA') for t,u in [
 ('Application Gateway HTTP response codes (400, 500, 504)','https://learn.microsoft.com/en-us/troubleshoot/azure/application-gateway/http-response-codes'),
 ('Application Gateway listener configuration and backend error forwarding','https://learn.microsoft.com/en-us/azure/application-gateway/configuration-listeners'),
 ('Application Gateway WAF troubleshooting','https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/web-application-firewall-troubleshoot'),
 ('Azure Firewall SNAT limitations and capacity options','https://learn.microsoft.com/en-us/azure/firewall/firewall-known-issues'),
 ('Front Door HTTPS origin troubleshooting','https://learn.microsoft.com/en-us/troubleshoot/azure/front-door/troubleshoot-issues'),
 ('Diagnose an NSG traffic filter problem','https://learn.microsoft.com/en-us/azure/virtual-network/diagnose-network-traffic-filter-problem')]],
 h('Maintenance'),p('Revalidate technical guidance when services or lab architecture change. Rebuild this pack with build_materials.py after editing the scenario data. Keep scenario names stable so observation records remain traceable.')]
save('time-attack-facilitator-guide.pdf',story)

for i,(b,d) in enumerate(zip(behaviours,DIRECTIONS)):
    voice,opening,cue,reward,release,boundary=d
    actor=[p(f'Customer role {i+1:02d}','SubTA'),p(b['name'],'TitleTA'),p('Private actor brief | Pair with any technical incident | 30-minute drill'),
     Diagram(['Pressure','Candidate action','Cooperation'],'React to the candidate: productive behavior should change the conversation.','people'),
     h('Your purpose'),p('Create realistic customer pressure so the candidate can demonstrate support leadership. You are playing a role, not trying to defeat the candidate. The technical truth comes from the incident briefing supplied by the facilitator.'),
     h('Characteristics to adopt'),*bullets(b['traits']),h('Voice and physical cues'),p(voice),h('Opening line'),p('"'+opening+'"'),h('Before the session'),p('Read the selected incident with the facilitator. Confirm known facts, hidden evidence, impact and any fixed constraint. Rehearse the opening with the actual symptom. Keep this brief and evaluator facts away from the candidate.'),PageBreak(),
     p('Play the role consistently','TitleTA'),h('0-5 minutes | Establish the customer'),p('Use the opening line, then describe the selected incident symptom and known facts. Start at moderate intensity. Let the candidate establish impact, scope and a plan.'),
     h('5-20 minutes | Apply the agreed pressure'),p(cue),h('Reward effective handling'),p(reward),h('How to disclose technical evidence'),p(release),p('A relevant question or proposed test unlocks the corresponding hidden fact. You may read the fact or provide the prepared synthetic evidence. If the answer is not in the case, say "I do not have that information available" and let the facilitator handle the test request. Never fabricate a result.'),
     h('20-30 minutes | Let them close'),p('Ask: "What do we know, what happens next, and when will you update me?" Allow a final summary. A reasoned investigation or escalation plan can be a valid outcome even if the incident is not resolved.'),
     h('Acting boundary'),p(boundary),p('Stay professional. Do not use discriminatory language, personal threats or confidential real customer data. Stop roleplay if the facilitator pauses the exercise.'),
     h('After the timer'),p('Leave the role. Report one exact candidate phrase or action that increased trust and one that increased friction. Describe observable behavior; let the observer apply the rubric.'),
     p('Assigned incident: ___________________________________________'),p('Agreed business impact / constraint: _____________________________')]
    actor += [PageBreak(),p('Ready-to-use sentences','TitleTA'),p(b['name'],'SubTA'),
        p('Choose one or two lines that fit the moment; do not read the entire list. Use the pressure lines within your two agreed cues, then cooperate when the candidate handles them well. Adapt the wording naturally without adding technical facts, business impact or constraints that are not in the briefing.')]
    for label, sentences in PHRASES[i]:
        actor += [h(label), *bullets(['"'+sentence+'"' for sentence in sentences])]
    actor += [h('Five more lines to vary your delivery'), *bullets(['"'+sentence+'"' for sentence in EXTRA_PHRASES[i]])]
    actor += [h('When you need to give a factual answer'),p('Pause the acting long enough to answer the question accurately using the selected case. A sentence above never replaces requested evidence. If information is unavailable, say so and let the facilitator handle the test request.')]
    save(actor_files[i],actor)
print(f'Updated library: {len(behaviours)} behaviors, {len(scenarios)} scenarios. Created {len(actor_files)+1} PDFs in {OUT}')

# Keep the combined customer download in sync with the actor briefs.
from build_customer_pdf import build as build_customer_pdf
build_customer_pdf()
