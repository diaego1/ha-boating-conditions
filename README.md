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
5. Add the dashboard card file to Home Assistant:
   1. In Home Assistant, open the left sidebar and go to `Settings` > `Dashboards`.
   2. If you do not see `Settings` or the `Resources` option, click your user/profile icon at the very bottom of the sidebar and turn on `Advanced Mode`, then come back to `Settings` > `Dashboards`.
   3. On the `Dashboards` page, click the three-dot menu in the top-right corner and choose `Resources`.
   4. Click `Add Resource`.
   5. In `URL`, enter `/api/boating_conditions/static/boating-conditions-card.js`
   6. In `Resource type`, choose `JavaScript Module`.
   7. Click `Create`.
   8. Refresh your browser tab once, then add the card to a dashboard using `type: custom:boating-conditions-card`.
   9. When you add the card, Home Assistant should usually suggest the correct weekend sensor automatically. If it does not, open the card settings and choose the sensor whose entity id ends with `weekend_rag`.
   10. If Home Assistant still seems to be using an older version of the card after an update, edit the resource and temporarily change the URL to `/api/boating_conditions/static/boating-conditions-card.js?v=2`, then refresh the browser again.

For the best HACS upgrade experience, publish GitHub releases rather than only pushing tags or branch commits.

Default settings use approximate Brighton Marina coordinates and `Europe/London`.

## Manual installation

1. Copy `custom_components/boating_conditions` into your Home Assistant config directory.
2. Restart Home Assistant.
3. Add the `Boating Conditions` integration from Settings > Devices & Services.
4. Add the dashboard card file to Home Assistant:
   1. Go to `Settings` > `Dashboards`.
   2. If the `Resources` option is missing, open your user/profile page from the bottom-left of the sidebar, enable `Advanced Mode`, and return to `Settings` > `Dashboards`.
   3. Click the three-dot menu in the top-right corner and select `Resources`.
   4. Click `Add Resource`.
   5. Set `URL` to `/api/boating_conditions/static/boating-conditions-card.js`
   6. Set `Resource type` to `JavaScript Module`
   7. Click `Create`
   8. Refresh the browser tab, then add the card to a dashboard using `type: custom:boating-conditions-card`.
   9. If the card is added without a sensor selected, edit the card and choose the weekend sensor whose entity id ends with `weekend_rag`.
   10. If Home Assistant still shows old card behavior after an update, change the resource URL to `/api/boating_conditions/static/boating-conditions-card.js?v=2` to force the browser to fetch the latest file, then refresh again.

## GitHub metadata

The manifest and HACS metadata now point at:

- `https://github.com/diaego1/ha-boating-conditions`

## Example card

```yaml
type: custom:boating-conditions-card
entity: sensor.brighton_marina_weekend_rag
title: Boating Conditions
layout: portrait
show_last_updated: true
```

Set `layout: landscape` if you want the wider, shorter version of the card.

## Entities created

- Main sensor: weekend worst-case RAG with summary and all three day payloads in attributes
- Friday, Saturday, and Sunday RAG sensors with per-day metrics and commentary

The integration also exposes the `boating_conditions.refresh_forecast` service for manual refreshes or automations, and exposes the bundled card resource URL as `/api/boating_conditions/static/boating-conditions-card.js`.

## How daylight filtering works

The card only analyses forecast hours between the forecast sunrise and sunset for each target day, so overnight conditions do not affect the Friday, Saturday, and Sunday RAG lamps.
