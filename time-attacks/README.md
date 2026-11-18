# Time Attack



The library contains 10 customer profiles and 15 technical scenarios, including Application Gateway HTTP 400 and 500, gateway timeouts, WAF false positives, SNAT exhaustion, Front Door certificate mismatch, and NSG priority conflicts.



Facilitator resources: `output/pdf/time-attack-facilitator-guide.pdf` and ten individual `actor-*.pdf` briefs. Download links are available in the application. The guide contains illustrations, operating instructions, the proposed scoring rubric and all incident evidence. Each actor brief explains delivery, scripted pressure cues and when to cooperate.



Use the run page as a private operator console: it exposes investigation targets and evaluator facts. Give candidates only the selected case's Candidate Brief and Known facts. Enter the candidate and instructor names, choose the customer behavior, technical scenario and soft skills, then explicitly start the 30-minute timer. Running assessments and observations recover on reload in the same browser.



To regenerate the PDFs after scenario edits, run `python build_materials.py` with ReportLab installed. Technical cases are synthetic tabletop assessments, not deployed Azure labs.



Independent static application with customer behaviour profiles, technical scenarios, and 30-minute drills.



Requires Node.js for HTTP preview. Run start.cmd or node preview.cjs from this folder, then open http://127.0.0.1:4174/. Stop with Ctrl+C.



You can also open index.html directly. No Ranger Mastery Program files or server are required. All scenario data, styles, and application logic are included in index.html. Drills open directly without a password.







## Instructor assignments and assessment reports



Open **Instructor assignments** in the navigation (the separate `index.html?timeAttack=assignments` view). Enter one instructor per line and click **Assign scenarios and roles**. Each instructor receives a randomly assigned technical scenario and customer role, plus a private assessment link and acting brief. Roles and scenarios are distributed without repeats until each pool is exhausted. Copy the private links to share assignments in advance; recipients must be able to access the application at the same URL/path.



On the run page, select the behavior, scenario and soft skills before starting. Record 1–5 ratings and observed evidence during the call. Questions map to the local Ranger Mastery Program playbook, Missions 1–4 and its evaluation framework; only the selected behavioral and soft-skill questions are scored. Technical scenarios provide role-play context, with no technical-understanding questions in the assessment or new reports. This is a proposed practice rubric, not a program certification threshold. Unobserved items are excluded from averages and reported explicitly.



At zero, inputs lock, the completed HTML report is stored in this browser and an HTML download is attempted. Browser download settings determine the destination; use **Download HTML report** if automatic downloading is blocked. Saved reports can also be downloaded from the home page. Reports contain candidate information and evaluator evidence. Local storage is specific to the browser/origin (file URLs may vary by browser), has capacity limits and is not shared or backed up: retain the downloaded files. Storage failures are shown in the console UI. A completed session can be reused with **New assessment**, while its previous report remains in saved reports.


During a running assessment, use **Save results as HTML** to download a snapshot at any time. Enter the filename when prompted; .html is added automatically. The snapshot includes current ratings, evidence and feedback, is marked in progress, and leaves the timer running. Canceling the prompt leaves the assessment unchanged.


The Technical Scenarios tab provides an individual PDF download on every card and a combined PDF download for all 15 cases. Each case separates the candidate briefing from private evaluator evidence and investigation targets. Regenerate these files after scenario edits with Python and ReportLab: python build_technical_pdfs.py.


The Customer Behaviour tab includes **Download all customer behaviours (PDF)**: a bookmarked collection of all 10 complete actor briefs. Rebuild with python build_customer_pdf.py after updating actor PDFs; build_materials.py also rebuilds the collection automatically.

