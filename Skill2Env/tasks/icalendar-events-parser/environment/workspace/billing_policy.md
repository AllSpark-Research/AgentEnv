# Billing Policy — Estúdio Sofia Marques

*(Last reviewed: 5 January 2026)*

These are the rules I use to turn my teaching calendar into student invoices.
The teaching calendar (`lessons_calendar.ics`) is the source of truth for what
lessons were scheduled; `messages.md` and `roster.csv` document the changes and
special cases I already reflected in the calendar.

## Rates (valid for all of 2026)

| Student         | Instrument | Rate                  |
|-----------------|------------|-----------------------|
| Ana Costa       | Piano      | €30.00 per hour       |
| Anabela Sousa   | Violin     | €32.00 per hour       |
| Bruno Pereira   | Guitar     | €28.00 per hour       |
| Carla Ribeiro   | Voice      | €35.00 per hour       |
| Miguel Santos   | (trial)    | Flat fee €20.00       |
| Paulo Ferreira  | Drums      | €25.00 per hour       |

## Rules

1. **Billing window.** A lesson belongs to the month in which it *starts*,
   in Europe/Lisbon local time. Lessons that fall outside the billing month
   are never included, even if they belong to a series that runs longer.

2. **What is billable.** Only timed lessons on the teaching calendar are
   billable. All-day entries (recitals, studio closures, reminders) and
   everything on my personal calendar are never invoiced — they are not
   lessons, even when a title mentions a student or an instrument.

3. **Recurring series.** A weekly series is billed per occurrence that actually
   remained on the calendar. Occurrences I removed (e.g. the school-break week)
   are not billed. A lesson that was moved to a different day/time is billed
   **once**, at the day and time it actually took place.

4. **Cancellations.** A cancelled lesson is never billed — this covers a single
   cancelled occurrence as well as a whole series that was cancelled. Roster
   entries marked *stopped* have a cancelled series: no sessions of theirs are
   billable for the billing month, even if the series still appears when the
   calendar is expanded (their appointments never happened; the series was
   terminated before it began).

5. **Trial lessons.** Trials are billed at the flat fee listed in the table
   above, regardless of how long the trial session was scheduled.

6. **Amounts.** For hourly students, a session's billable time is its scheduled
   start-to-end length in minutes. Amount due per student =
   round(total_minutes ÷ 60 × hourly_rate, 2). All amounts in EUR.
