# Ranger Mastery Program

Static website for the Ranger Mastery Program.

## Main Pages

- `index.html` - Home page and program flow
- `program_materials.html` - Program materials and weekly activities
- `program_model.html` - Program model
- `program_playbook.html` - Program playbook
- `Program_Assessment.html` - Engineer and Manager assessments
- `rangers_success_measurement_review.html` - Success measurement
- `rangers_week0_overview.html` - Week 0 overview
- `rangers_cohort_size_rationale.html` - Cohort size rationale
- `faq.html` - Frequently asked questions

## Program Material Visibility

Edit `weekoftheprogram.txt` to control material availability:

- `0` - Lock all weeks.
- `1` through `7` - Make all materials available through that week.
- `<week>.<day>` - Make earlier weeks available and reveal materials through that day in the current week. For example, `1.1` reveals only Day 1 of Week 1.

Preview all materials at `program_materials.html#admin`. This URL fragment is a convenience preview only; it is not authentication or an access-control boundary.

## Instructor Guides

Open [Program Materials in instructor mode](program_materials.html#instructor) to reveal the Instructor Desk and unlock all weeks. The desk groups PDF guides by week and day, with matching instructor links on participant material cards. Use **Return to participant view** to hide the desk and restore the release schedule. The existing `#admin` preview does not show instructor guides.

To add a guide:

1. Place the PDF in the website root alongside the existing instructor PDFs.
2. Add an entry to the `instructorGuides` array in [program_materials.html](program_materials.html) with `week`, `day` (the program-wide day number), `title`, and `file` (the exact PDF filename).
3. The desk automatically sorts entries, creates week groups, and updates its guide count. A matching `.resource-day-N` card in that week also receives an instructor link when present.

This is hidden-only mode, not restricted access. Instructor PDFs remain publicly accessible by direct URL, and the catalog is visible in the page source. Do not publish confidential documents using this mechanism.

## Local Preview

Run `start.cmd`, then open `http://127.0.0.1:4173/`. The preview server disables caching so changes appear after refresh.

## Editing Workflow

Use branches and pull requests for changes. The `main` branch represents the live production version deployed to Azure App Service.
