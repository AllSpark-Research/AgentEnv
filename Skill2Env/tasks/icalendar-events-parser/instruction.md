You can use the skill documented at `_skill_ref/SKILL.md` (and its scripts under `_skill_ref/`) to help complete this task.

Focus on completing the user's request. Avoid additional work that goes beyond what the user asked for, unless it is necessary to ensure the correctness of the result.

Sofia Marques runs a one-person music studio in Lisbon, Portugal, and she has fallen behind on her invoicing. Prepare her March 2026 billing from her calendar exports.

Workspace files:
- lessons_calendar.ics — export of her teaching calendar containing March's scheduled lessons (several weekly recurring series plus one-off entries).
- personal_calendar.ics — her personal calendar export (context only).
- billing_policy.md — her billing rules and the per-student rate table.
- roster.csv — her current students and their status.
- messages.md — her notes about the schedule changes already reflected in the calendar export.

Apply the rules in billing_policy.md exactly. Treat lessons_calendar.ics as the source of truth for what was scheduled, remember that the billing month is March 2026 and the studio is in Europe/Lisbon, and produce three deliverables:

1. billing/sessions.csv — one row per billable lesson session, with exactly this header:
student,date,start,end,minutes
   - student: the student's full name exactly as in roster.csv
   - date: YYYY-MM-DD in Europe/Lisbon local time; start and end: local Lisbon wall-clock time as HH:MM; minutes: the scheduled length of the session in whole minutes.

2. billing/march_2026.json — valid JSON with exactly this structure:
{
  "billing_period": {"start": "2026-03-01", "end": "2026-03-31", "time_zone": "Europe/Lisbon"},
  "currency": "EUR",
  "students": [{"name": "...", "sessions": 0, "minutes": 0, "amount_eur": 0.00}],
  "total_sessions": 0,
  "total_amount_eur": 0.00
}
   - "students" must contain exactly the six names from roster.csv (a student with no billable sessions appears with zeros); sessions and minutes are whole numbers; amounts are in euro with two decimals.

3. billing/billing_notes.md — a short note Sofia can keep with the invoices explaining how each non-obvious case was handled (e.g. cancellations, rescheduled lessons, the trial lesson, anything excluded and why), so she can justify the amounts if a student questions them.