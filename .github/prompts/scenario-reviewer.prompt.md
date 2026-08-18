---
mode: ask
tools: ['codebase']
description: Review a scenario.json file for consistency and safe generation.
---

# Scenario Reviewer

Review the `scenario.json` file used by this repository.

## Goal

Validate the scenario before video generation and prevent invalid or misleading outputs.

## What to check

- Required fields in `text`, `data`, and `video`
- Date consistency: `start_date < end_date`
- Presence of exactly one investment rhythm: `weekly_investment` or `monthly_investment`
- Positive numeric values for investment amount, duration, and fps
- Sensible output filename ending with `.mp4`
- Currency and ticker presence
- Headline length and readability for a vertical mobile layout
- Consistency between `reinvest_dividends` and the expected graph behavior

## Constraints

- Keep the scope limited to scenario validation
- Never silently ignore invalid values
- Prefer minimal fixes
- Do not redesign the repository

## Expected output

Provide:

1. A short validation summary
2. A list of issues ordered by severity
3. A minimal corrected version of `scenario.json` if needed
