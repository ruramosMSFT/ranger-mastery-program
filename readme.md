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

## Local Preview

Run `start.cmd`, then open `http://127.0.0.1:4173/`. The preview server disables caching so changes appear after refresh.

## Editing Workflow

Use branches and pull requests for changes. The `main` branch represents the live production version deployed to Azure App Service.

