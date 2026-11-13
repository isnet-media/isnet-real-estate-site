# Workflow failure inbox

Immutable event metadata belongs here as `<run_id>-<attempt>.json`. The existing controller reconciles these with direct GitHub Actions reads because event chains can be missed. Preserve entries and mark processing in ../state.json; do not copy logs, secrets or email bodies. Empty at bootstrap; historical occurrences are linked in ../incidents.json rather than fabricated as captured events.
