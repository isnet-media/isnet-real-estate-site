# Family recipes

Canonical public section: https://isnet.co.il/SUPER.ASHDOD/recipes/

Twelve original full-meal recipes serve 4–5. Data is in SUPER.ASHDOD/recipes/recipes.json. Costs are planning estimates for ingredient usage, including pantry ingredients, not live branch quotations or whole-package checkout totals. No nutrition quantities are claimed.

Regenerate HTML with `python scripts/build_super_recipes.py`. Check using `python scripts/test_super_recipes.py` and `node --check SUPER.ASHDOD/recipes/recipes.js`. Images are distinct AI-generated illustrations, disclosed in the footer. Prompts are recorded in recipe-image-prompts.json.

The old one-time bootstrap importer is now manual-only and refuses to overwrite a site containing recipes. Edit this repository for the canonical external site. Do not run the old import to update prices: it would discard subsequent site edits.
