# Boating Conditions

HACS-ready custom Home Assistant integration and Lovelace card for a daylight-only Friday to Sunday boating outlook around Brighton Marina, using Open-Meteo weather and marine forecast data.

The scoring is tuned for a 55 ft motor yacht and blends:

- 10 m wind speed and gusts
- Wave height and wave period
- Wind-wave height and period
- Swell height and period, including secondary swell where available
- Onshore wind and swell exposure for the Brighton frontage

Green means easy and pleasant, yellow means safe but lumpier or a bit more demanding, and red means uncomfortable or challenging enough that berthing and marina-area handling are likely to take real concentration.

This is guidance only. It does not replace local forecasts, tide planning, Notices to Mariners, or skipper judgment.

## Repository layout

- `custom_components/boating_conditions/`: custom integration
- `custom_components/boating_conditions/static/boating-conditions-card.js`: bundled custom Lovelace card served by the integration
- `custom_components/boating_conditions/brand/`: Home Assistant 2026.3 local brand assets
- `examples/dashboard/boating_conditions_dashboard.yaml`: example dashboard snippet
- `examples/scripts/boating_conditions_scripts.yaml`: example script snippet
- `examples/automations/boating_conditions_notifications.yaml`: example automations
- `.github/workflows/`: HACS validation and Hassfest workflows
- `hacs.json`: HACS repository metadata

## HACS installation

1. Publish this repository to a public GitHub repository.
2. In HACS, add it as a custom repository of type `Integration`, then download it.
3. Restart Home Assistant.
4. Add the `Boating Conditions` integration from Settings > Devices & Services.
5. In Lovelace resources, add `/api/boating_conditions/static/boating-conditions-card.js` as a `module`.

For the best HACS upgrade experience, publish GitHub releases rather than only pushing tags or branch commits.

Default settings use approximate Brighton Marina coordinates and `Europe/London`.

## Manual installation

1. Copy `custom_components/boating_conditions` into your Home Assistant config directory.
2. Restart Home Assistant.
3. Add the `Boating Conditions` integration from Settings > Devices & Services.
4. In Lovelace resources, add `/api/boating_conditions/static/boating-conditions-card.js` as a `module`.

## GitHub metadata

The manifest and HACS metadata now point at:

- `https://github.com/diaego1/ha-boating-conditions`

## Example card

```yaml
type: custom:boating-conditions-card
entity: sensor.brighton_marina_weekend_rag
title: Boating Conditions
show_last_updated: true
```

## Entities created

- Main sensor: weekend worst-case RAG with summary and all three day payloads in attributes
- Friday, Saturday, and Sunday RAG sensors with per-day metrics and commentary

The integration also exposes the `boating_conditions.refresh_forecast` service for manual refreshes or automations, and exposes the bundled card resource URL as `/api/boating_conditions/static/boating-conditions-card.js`.

## How daylight filtering works

The card only analyses forecast hours between the forecast sunrise and sunset for each target day, so overnight conditions do not affect the Friday, Saturday, and Sunday RAG lamps.
