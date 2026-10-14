# Ashdod sports — results and statistics

Public static site at `/sports/ashdod/`, hosted through the same ISNET GitHub Pages publication as events and enrichment classes. All links and assets are relative. Published sports data is a verified snapshot refreshed through scheduled source scans. It is not a continuous live-score stream.

The site includes football adults, football youth, basketball, handball and round results. Logos and licensed Heebo fonts are bundled. The original development source is retained in the Sites source repository.

## MS Ashdod club hub

The public first-team page is `sports/ashdod/teams/ms-ashdod.html`. It reads current team tables, fixtures and player statistics from `../data.json` at page load. `teams/ms-ashdod.json` adds verified player names, portraits, nationality, birth month/year, shirt numbers from official match reports, and nine parsed league match reports. All 37 player photographs were obtained from the corresponding IFA player profile. Photo source URLs and the profile verification time are retained in the enrichment JSON.

League goals are shown separately from all-competition appearances, minutes and discipline. Schedule result strings are normalized from the IFA's visual RTL order and were checked against all nine named home/away match reports (8 wins, goals 22:8 at initial publication). The goal-timing chart uses only 20 events with verified minutes, and explicitly states its coverage versus the full league goal total. It must not silently imply complete event coverage.

Future dataset refreshes automatically appear in the club page. Profile enrichment has its own verification date; portraits and profile-specific breakdowns should only be refreshed from the exact official player URLs. Player-profile goal breakdowns are hidden when their total no longer matches the refreshed aggregate player statistics. Missing data remains unknown, not zero.


## Club match centre and scheduled source collector

`python scripts/refresh_ashdod_club.py` refreshes MS Ashdod from the exact saved IFA team, schedule, player-statistics and scorers URLs. It also reads named match reports for final results, published lineups and timeline events, and the next opponent schedule linked through the official league table. Every parsed report must agree with the schedule score and contain MS Ashdod. Failed records retain their previous values and verification times. No live feed, inferred injuries, assists, xG, tickets or parking claims are generated.

The existing sports automation runs the collector in its working environment at the six configured Jerusalem hours (07:00, 12:00, 14:00, 21:00, 22:00, 23:00), alongside the other clubs and branches. Direct requests from GitHub-hosted runners returned HTTP 403 on 15 October 2026, so `.github/workflows/ashdod-club.yml` is manual-only and has no schedule. The collector was successfully run from the working environment with all nine match reports and the opponent verified. The manual workflow commits only the two sports JSON files and refuses conflicting concurrent data changes. Pages can publish successful manual collector runs; scheduled automation commits are published normally. Photos and player biography enrichment retain their own verification date; this collector does not silently claim to refresh those fields.

The club page derives the pregame comparison, recent-form narrative and player comparison from the refreshed datasets. Comparisons use all-competition goals and minutes consistently; league totals are labeled separately. `teams/match.html?date=YYYY-MM-DD&opponent=...` resolves only games in the current official club schedule; stale match reports are not mixed with a newer score. Root `city-games.js` derives a rolling seven-day city schedule from existing football data plus other sports' saved upcoming fixtures. Unknown home/away values never enter the home-only filter. No youth player rankings are generated.
