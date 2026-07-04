ICP
->
Company Discovery
->
Website Discovery
->
Founder Discovery
->
Contact Discovery
->
Verification
->
Confidence Scoring
->
SQLite Database
->
REST API / Dashboard

Phase 1 implementation notes:

1. Company discovery imports startup/company rows from public Inc42 content.
2. Website discovery finds official company sites using DuckDuckGo and filters noisy domains.
3. Founder discovery currently uses parsed public source data, then creates one lead per company founder or decision-maker.
4. Contact discovery scrapes public About, Team, Leadership, and Contact pages for emails and phone numbers, searches public LinkedIn profile results, and infers email patterns only when direct emails are not found.
5. Verification marks every email and phone as missing, invalid, format verified, domain verified, or inferred/unverified. Outreach readiness is driven by the confidence score, not by raw presence of a field.
6. CSV and JSON exports plus `/stats` read from SQLite for the dashboard/demo.

Phase 2 upgrade plan:

1. Replace public search scraping with official or paid enrichment APIs such as Hunter, Apollo, People Data Labs, or Clearbit.
2. Add real deliverability APIs such as ZeroBounce or NeverBounce instead of free format/domain checks.
3. Add phone lookup APIs such as Twilio Lookup or NumVerify for active line type checks.
4. Move schema changes to Alembic migrations.
5. Add a scheduler/queue for rate-limited scraping jobs.
