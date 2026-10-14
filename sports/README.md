# Ashdod sports — results and statistics

Public static site at `/sports/ashdod/`, hosted through the same ISNET GitHub Pages publication as events and enrichment classes. All links and assets are relative. Published sports data is a verified snapshot refreshed through scheduled source scans. It is not a continuous live-score stream.

The site includes football adults, football youth, basketball, handball and round results. Logos and licensed Heebo fonts are bundled. The original development source is retained in the Sites source repository.

## MS Ashdod club hub

The public first-team page is `sports/ashdod/teams/ms-ashdod.html`. It reads current team tables, fixtures and player statistics from `../data.json` at page load. `teams/ms-ashdod.json` adds verified player names, portraits, nationality, birth month/year, shirt numbers from official match reports, and nine parsed league match reports. All 37 player photographs were obtained from the corresponding IFA player profile. Photo source URLs and the profile verification time are retained in the enrichment JSON.

League goals are shown separately from all-competition appearances, minutes and discipline. Schedule result strings are normalized from the IFA's visual RTL order and were checked against all nine named home/away match reports (8 wins, goals 22:8 at initial publication). The goal-timing chart uses only 20 events with verified minutes, and explicitly states its coverage versus the full league goal total. It must not silently imply complete event coverage.

Future dataset refreshes automatically appear in the club page. Profile enrichment has its own verification date; portraits and profile-specific breakdowns should only be refreshed from the exact official player URLs. Player-profile goal breakdowns are hidden when their total no longer matches the refreshed aggregate player statistics. Missing data remains unknown, not zero.
