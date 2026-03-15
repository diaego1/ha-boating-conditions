# Boating Conditions

> [!WARNING]
> This project and much of its code/documentation have been largely AI-generated and only lightly reviewed by a human. The repository owner has limited coding knowledge. It may contain bugs, incorrect assumptions, incomplete validation, or unsafe logic. Use at your own risk. Always independently verify forecasts, tides, traffic, Notices to Mariners, and actual local conditions. Do not rely on this project as the sole basis for go/no-go boating decisions.

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

## How the RAG status is calculated

This integration does not use Home Assistant AI, Assist, or an LLM to generate the boating narrative. The logic is deterministic and rule-based:

1. Fetch weather and marine forecast data from Open-Meteo.
2. Keep only daylight hours between the forecast sunrise and sunset.
3. Build a per-day view for Friday, Saturday, and Sunday.
4. Score each day using wind, gusts, sea state, wind chop, swell, wave steepness, and onshore exposure.
5. Convert that score into `green`, `yellow`, or `red`.
6. Generate the narrative text from code-based templates using the resulting conditions.

The code currently uses two layers:

- A weighted score built from the forecast inputs.
- Direct caution and hard-red trigger thresholds that can override the score.

### Main thresholds

These are the practical skipper-facing breakpoints used by the logic today:

| Factor | Green feel | Yellow feel | Red feel |
|---|---|---|---|
| Wind max | Under 16 kt | 16-23 kt | 24+ kt |
| Gusts | Under 24 kt | 24-31 kt | 32+ kt |
| Sea state / wave max | Under 0.8 m | 0.8-1.39 m | 1.4+ m |
| Wind chop max | Under 0.45 m | 0.45-0.84 m | 0.85+ m |
| Combined swell max | Under 0.75 m | 0.75-1.29 m | 1.3+ m |
| Wave steepness index | Under 0.13 | 0.13-0.19 | 0.20+ with at least 0.8 m waves |

### Direct yellow triggers

Any one of these is enough to make a day at least `yellow`:

- Wind max `>= 16 kt`
- Gust max `>= 24 kt`
- Wave max `>= 0.8 m`
- Wind chop `>= 0.45 m`
- Combined swell `>= 0.75 m`
- Steepness index `>= 0.13`
- Onshore wind for `3+` daylight hours
- Onshore swell for `2+` daylight hours

### Direct red triggers

Any one of these is enough to make a day `red`:

- Wind max `>= 24 kt`
- Gust max `>= 32 kt`
- Wave max `>= 1.4 m`
- Wind chop `>= 0.85 m`
- Combined swell `>= 1.3 m` and swell period `>= 8 s`
- Steepness index `>= 0.20` and waves `>= 0.8 m`
- Onshore wind for `5+` daylight hours and wind max `>= 20 kt`

### Weighted score

When a direct trigger does not already decide the result, the score is built from:

- Wind max: `30%`
- Gust max: `15%`
- Sea state / wave max: `20%`
- Wind chop max: `10%`
- Swell max: `15%`
- Wave steepness: `10%`
- Extra onshore penalty: `+8` for persistent stronger onshore wind, `+10` for persistent onshore swell

The final RAG decision is:

- `Red` if any hard-red trigger fires, or score `>= 65`
- `Yellow` if not red, but any caution trigger fires, or score `>= 35`
- `Green` otherwise

### Brighton-specific onshore logic

The code treats directions between `120` and `240` degrees as onshore for the Brighton frontage. That means persistent SE through SW wind or swell can push a day toward yellow or red more quickly than the raw height/wind numbers alone might suggest.

### Yacht length setting

The setup flow asks for motor yacht length in feet, and the default is `55 ft`.

Important caveat: at the moment, that value does **not** numerically rescale the thresholds above.

Today, yacht length is used for:

- The displayed boat profile text
- The narrative wording
- The disclaimer text

Today, yacht length is **not** used for:

- Changing wind thresholds
- Changing wave/swell thresholds
- Changing the weighted score
- Changing green/yellow/red trigger points

So the current implementation should still be understood as a ruleset tuned around a `55 ft motor yacht`, even if a user enters a different boat length during setup.

## How daylight filtering works

The card only analyses forecast hours between the forecast sunrise and sunset for each target day, so overnight conditions do not affect the Friday, Saturday, and Sunday RAG lamps.
