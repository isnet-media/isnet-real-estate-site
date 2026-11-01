# Herzliya health and emergency directory

This edition contains health services only. `index.html` leads to `health.html`; it does not advertise a Herzliya events, restaurant or other city application.

Reviewed data is in `data/health.json`. Source URLs and the review date are retained per directory snapshot. Opening status is not live and no source schedule is inferred to be pharmacist availability or today's duty roster. The Marina branch's address conflict is disclosed; the network's current branch address is used for navigation.

Rebuild with `python scripts/build_herzliya_health.py`; validate with `python scripts/test_herzliya_health.py`. The generator reuses the existing Holon health renderer with an explicit target directory; the default Holon output must remain unchanged. Styling and rich sharing reuse existing ISNET assets. Mobile and desktop checks run in `herzliya-health-tests.yml`.

Changes to phone numbers, locations or service availability require a fresh review of the linked official sources. Do not advance the review date merely by rebuilding.
