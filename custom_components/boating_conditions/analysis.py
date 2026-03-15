"""Forecast analysis for Brighton Marina boating comfort and challenge."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from statistics import mean
from typing import Any
from zoneinfo import ZoneInfo

from .const import (
    ATTRIBUTION,
    DAY_INDEX_TO_KEY,
    DISCLAIMER,
    ONSHORE_MAX_DEGREES,
    ONSHORE_MIN_DEGREES,
    RAG_GREEN,
    RAG_RED,
    RAG_UNKNOWN,
    RAG_YELLOW,
)

KMH_TO_KT = 0.539957

COMPASS_POINTS = (
    "N",
    "NNE",
    "NE",
    "ENE",
    "E",
    "ESE",
    "SE",
    "SSE",
    "S",
    "SSW",
    "SW",
    "WSW",
    "W",
    "WNW",
    "NW",
    "NNW",
)

FEEL_BY_RAG = {
    RAG_GREEN: "Easy and pleasant",
    RAG_YELLOW: "Safe but a bit lumpy",
    RAG_RED: "Challenging and uncomfortable",
    RAG_UNKNOWN: "Forecast unavailable",
}


class ForecastAnalysisError(Exception):
    """Raised when the forecast cannot be analysed."""


@dataclass(slots=True)
class HourSample:
    """Single merged weather and marine forecast sample."""

    time: datetime
    wind_speed_kt: float | None
    wind_gust_kt: float | None
    wind_direction: float | None
    wave_height: float | None
    wave_period: float | None
    wave_direction: float | None
    wind_wave_height: float | None
    wind_wave_period: float | None
    wind_wave_direction: float | None
    swell_wave_height: float | None
    swell_wave_period: float | None
    swell_wave_direction: float | None
    secondary_swell_wave_height: float | None
    secondary_swell_wave_period: float | None
    secondary_swell_wave_direction: float | None


@dataclass(slots=True)
class DayAssessment:
    """Daily outlook for one weekend day."""

    key: str
    label: str
    short_label: str
    date: str
    rag: str
    rag_label: str
    score: int
    feel: str
    summary: str
    daylight_start: str
    daylight_end: str
    daylight_hours: int
    wind_mean_kt: float | None
    wind_max_kt: float | None
    gust_max_kt: float | None
    dominant_wind_direction: str | None
    wave_mean_m: float | None
    wave_max_m: float | None
    wave_period_s: float | None
    wind_wave_max_m: float | None
    wind_wave_period_s: float | None
    swell_max_m: float | None
    swell_period_s: float | None
    secondary_swell_max_m: float | None
    dominant_swell_direction: str | None
    steepness_index: float | None
    onshore_wind_hours: int
    onshore_swell_hours: int
    drivers: list[str]


def analyse_forecasts(
    *,
    weather_payload: dict[str, Any],
    marine_payload: dict[str, Any],
    timezone_name: str,
    yacht_length_ft: int,
    location_name: str,
) -> dict[str, Any]:
    """Build the weekend assessment payload used by sensors and the card."""

    tzinfo = ZoneInfo(timezone_name)
    solar_windows = _extract_solar_windows(weather_payload, tzinfo)
    samples = _merge_samples(weather_payload, marine_payload, tzinfo)
    friday, saturday, sunday = _select_target_weekend(solar_windows, tzinfo)
    target_dates = [friday, saturday, sunday]

    days = [
        _analyse_day(
            day_date=day_date,
            solar_windows=solar_windows,
            samples=samples,
            yacht_length_ft=yacht_length_ft,
        )
        for day_date in target_dates
    ]

    weekend_rag = _worst_rag(days)
    best_day = min(days, key=lambda item: item.score)
    worst_day = max(days, key=lambda item: item.score)

    return {
        "state": weekend_rag,
        "state_label": FEEL_BY_RAG[weekend_rag],
        "summary": _build_weekend_summary(days, best_day, worst_day, yacht_length_ft),
        "weekend_label": f"Weekend of {days[0].label}",
        "weekend_start": friday.isoformat(),
        "weekend_end": sunday.isoformat(),
        "location_name": location_name,
        "boat_profile": f"{yacht_length_ft} ft motor yacht",
        "best_day": best_day.label,
        "worst_day": worst_day.label,
        "days": [asdict(day) for day in days],
        "by_key": {day.key: asdict(day) for day in days},
        "attribution": ATTRIBUTION,
        "disclaimer": DISCLAIMER.replace("55 ft", f"{yacht_length_ft} ft"),
        "generated_at": datetime.now(tzinfo).isoformat(),
    }


def _extract_solar_windows(
    weather_payload: dict[str, Any],
    tzinfo: ZoneInfo,
) -> dict[date, tuple[datetime, datetime]]:
    daily = weather_payload["daily"]
    windows: dict[date, tuple[datetime, datetime]] = {}

    for idx, day_text in enumerate(daily["time"]):
        day_value = date.fromisoformat(day_text)
        sunrise = _parse_datetime(daily["sunrise"][idx], tzinfo)
        sunset = _parse_datetime(daily["sunset"][idx], tzinfo)
        windows[day_value] = (sunrise, sunset)

    return windows


def _merge_samples(
    weather_payload: dict[str, Any],
    marine_payload: dict[str, Any],
    tzinfo: ZoneInfo,
) -> list[HourSample]:
    weather_hourly = weather_payload["hourly"]
    marine_hourly = marine_payload["hourly"]
    marine_index_by_time = {
        time_text: index for index, time_text in enumerate(marine_hourly["time"])
    }

    samples: list[HourSample] = []
    for weather_index, time_text in enumerate(weather_hourly["time"]):
        marine_index = marine_index_by_time.get(time_text)
        if marine_index is None:
            continue

        sample_time = _parse_datetime(time_text, tzinfo)
        samples.append(
            HourSample(
                time=sample_time,
                wind_speed_kt=_convert_kmh_to_knots(
                    _pick(weather_hourly, "wind_speed_10m", weather_index)
                ),
                wind_gust_kt=_convert_kmh_to_knots(
                    _pick(weather_hourly, "wind_gusts_10m", weather_index)
                ),
                wind_direction=_pick(weather_hourly, "wind_direction_10m", weather_index),
                wave_height=_pick(marine_hourly, "wave_height", marine_index),
                wave_period=_pick(marine_hourly, "wave_period", marine_index),
                wave_direction=_pick(marine_hourly, "wave_direction", marine_index),
                wind_wave_height=_pick(marine_hourly, "wind_wave_height", marine_index),
                wind_wave_period=_pick(marine_hourly, "wind_wave_period", marine_index),
                wind_wave_direction=_pick(
                    marine_hourly, "wind_wave_direction", marine_index
                ),
                swell_wave_height=_pick(
                    marine_hourly, "swell_wave_height", marine_index
                ),
                swell_wave_period=_pick(
                    marine_hourly, "swell_wave_period", marine_index
                ),
                swell_wave_direction=_pick(
                    marine_hourly, "swell_wave_direction", marine_index
                ),
                secondary_swell_wave_height=_pick(
                    marine_hourly, "secondary_swell_wave_height", marine_index
                ),
                secondary_swell_wave_period=_pick(
                    marine_hourly, "secondary_swell_wave_period", marine_index
                ),
                secondary_swell_wave_direction=_pick(
                    marine_hourly, "secondary_swell_wave_direction", marine_index
                ),
            )
        )

    if not samples:
        raise ForecastAnalysisError("No overlapping weather and marine forecast hours found")

    return samples


def _select_target_weekend(
    solar_windows: dict[date, tuple[datetime, datetime]],
    tzinfo: ZoneInfo,
) -> tuple[date, date, date]:
    now = datetime.now(tzinfo)
    candidates = sorted(day for day in solar_windows if day.weekday() == 4)

    for friday in candidates:
        saturday = friday + timedelta(days=1)
        sunday = friday + timedelta(days=2)
        if saturday not in solar_windows or sunday not in solar_windows:
            continue

        sunday_sunset = solar_windows[sunday][1]
        if now <= sunday_sunset:
            return friday, saturday, sunday

    for friday in candidates:
        saturday = friday + timedelta(days=1)
        sunday = friday + timedelta(days=2)
        if saturday in solar_windows and sunday in solar_windows:
            return friday, saturday, sunday

    raise ForecastAnalysisError("No complete Friday to Sunday weekend found in forecast")


def _analyse_day(
    *,
    day_date: date,
    solar_windows: dict[date, tuple[datetime, datetime]],
    samples: list[HourSample],
    yacht_length_ft: int,
) -> DayAssessment:
    sunrise, sunset = solar_windows[day_date]
    daylight_samples = [
        sample
        for sample in samples
        if sample.time.date() == day_date and sunrise <= sample.time <= sunset
    ]

    short_label = day_date.strftime("%a")
    label = day_date.strftime("%a %d %b")
    key = DAY_INDEX_TO_KEY[day_date.weekday()]

    if not daylight_samples:
        return DayAssessment(
            key=key,
            label=label,
            short_label=short_label,
            date=day_date.isoformat(),
            rag=RAG_UNKNOWN,
            rag_label=FEEL_BY_RAG[RAG_UNKNOWN],
            score=100,
            feel=FEEL_BY_RAG[RAG_UNKNOWN],
            summary="No daylight forecast samples were available for this day.",
            daylight_start=sunrise.strftime("%H:%M"),
            daylight_end=sunset.strftime("%H:%M"),
            daylight_hours=0,
            wind_mean_kt=None,
            wind_max_kt=None,
            gust_max_kt=None,
            dominant_wind_direction=None,
            wave_mean_m=None,
            wave_max_m=None,
            wave_period_s=None,
            wind_wave_max_m=None,
            wind_wave_period_s=None,
            swell_max_m=None,
            swell_period_s=None,
            secondary_swell_max_m=None,
            dominant_swell_direction=None,
            steepness_index=None,
            onshore_wind_hours=0,
            onshore_swell_hours=0,
            drivers=["missing daylight forecast samples"],
        )

    wind_values = _list_values(daylight_samples, "wind_speed_kt")
    gust_values = _list_values(daylight_samples, "wind_gust_kt")
    wave_values = _list_values(daylight_samples, "wave_height")
    wind_wave_values = _list_values(daylight_samples, "wind_wave_height")
    swell_values = _list_values(daylight_samples, "swell_wave_height")
    secondary_swell_values = _list_values(
        daylight_samples, "secondary_swell_wave_height"
    )

    wind_max = _safe_max(wind_values)
    wind_mean = _safe_mean(wind_values)
    gust_max = _safe_max(gust_values)
    wave_max = _safe_max(wave_values)
    wave_mean = _safe_mean(wave_values)
    wind_wave_max = _safe_max(wind_wave_values)
    primary_swell_max = _safe_max(swell_values)
    secondary_swell_max = _safe_max(secondary_swell_values)
    combined_swell_max = _safe_max(
        [value for value in (primary_swell_max, secondary_swell_max) if value is not None]
    )

    wave_peak_period = _period_at_peak(daylight_samples, "wave_height", "wave_period")
    wind_wave_peak_period = _period_at_peak(
        daylight_samples, "wind_wave_height", "wind_wave_period"
    )
    primary_swell_peak_period = _period_at_peak(
        daylight_samples, "swell_wave_height", "swell_wave_period"
    )
    secondary_swell_peak_period = _period_at_peak(
        daylight_samples,
        "secondary_swell_wave_height",
        "secondary_swell_wave_period",
    )

    primary_swell_direction = _direction_at_peak(
        daylight_samples,
        "swell_wave_height",
        "swell_wave_direction",
    )
    secondary_swell_direction = _direction_at_peak(
        daylight_samples,
        "secondary_swell_wave_height",
        "secondary_swell_wave_direction",
    )

    steepness_values = [
        sample.wave_height / max(sample.wave_period, 1.0)
        for sample in daylight_samples
        if sample.wave_height is not None and sample.wave_period is not None
    ]
    steepness_index = _safe_max(steepness_values)

    dominant_wind_direction = _mean_direction_text(
        _list_values(daylight_samples, "wind_direction")
    )
    if (secondary_swell_max or 0) > (primary_swell_max or 0):
        swell_peak_period = secondary_swell_peak_period
        dominant_swell_direction = secondary_swell_direction
    else:
        swell_peak_period = primary_swell_peak_period
        dominant_swell_direction = primary_swell_direction or _mean_direction_text(
            _list_values(daylight_samples, "swell_wave_direction")
        )

    onshore_wind_hours = sum(
        1
        for sample in daylight_samples
        if sample.wind_direction is not None
        and sample.wind_speed_kt is not None
        and sample.wind_speed_kt >= 14
        and _is_onshore(sample.wind_direction)
    )
    onshore_swell_hours = sum(
        1
        for sample in daylight_samples
        if (
            sample.swell_wave_direction is not None
            and sample.swell_wave_height is not None
            and sample.swell_wave_height >= 0.8
            and _is_onshore(sample.swell_wave_direction)
        )
        or (
            sample.secondary_swell_wave_direction is not None
            and sample.secondary_swell_wave_height is not None
            and sample.secondary_swell_wave_height >= 0.8
            and _is_onshore(sample.secondary_swell_wave_direction)
        )
    )

    severity_map = {
        "wind": _scaled_severity(wind_max, 10, 16, 24),
        "gusts": _scaled_severity(gust_max, 18, 24, 32),
        "sea_state": _scaled_severity(wave_max, 0.4, 0.8, 1.4),
        "wind_chop": _scaled_severity(wind_wave_max, 0.15, 0.45, 0.85),
        "swell": _scaled_severity(combined_swell_max, 0.35, 0.75, 1.3),
        "steepness": _scaled_severity(steepness_index, 0.07, 0.13, 0.2),
    }

    onshore_penalty = 0
    if onshore_wind_hours >= 3 and (wind_max or 0) >= 16:
        onshore_penalty += 8
    if onshore_swell_hours >= 2 and (combined_swell_max or 0) >= 0.9:
        onshore_penalty += 10

    score = round(
        (
            severity_map["wind"] * 0.30
            + severity_map["gusts"] * 0.15
            + severity_map["sea_state"] * 0.20
            + severity_map["wind_chop"] * 0.10
            + severity_map["swell"] * 0.15
            + severity_map["steepness"] * 0.10
        )
        + onshore_penalty
    )
    score = max(0, min(score, 100))

    caution_triggered = any(
        [
            (wind_max or 0) >= 16,
            (gust_max or 0) >= 24,
            (wave_max or 0) >= 0.8,
            (wind_wave_max or 0) >= 0.45,
            (combined_swell_max or 0) >= 0.75,
            (steepness_index or 0) >= 0.13,
            onshore_wind_hours >= 3,
            onshore_swell_hours >= 2,
        ]
    )

    hard_red = any(
        [
            (wind_max or 0) >= 24,
            (gust_max or 0) >= 32,
            (wave_max or 0) >= 1.4,
            (wind_wave_max or 0) >= 0.85,
            (combined_swell_max or 0) >= 1.3 and (swell_peak_period or 0) >= 8,
            (steepness_index or 0) >= 0.2 and (wave_max or 0) >= 0.8,
            onshore_wind_hours >= 5 and (wind_max or 0) >= 20,
        ]
    )

    if hard_red or score >= 65:
        rag = RAG_RED
    elif caution_triggered or score >= 35:
        rag = RAG_YELLOW
    else:
        rag = RAG_GREEN

    drivers = _build_drivers(
        wind_max=wind_max,
        gust_max=gust_max,
        wave_max=wave_max,
        wind_wave_max=wind_wave_max,
        combined_swell_max=combined_swell_max,
        steepness_index=steepness_index,
        dominant_wind_direction=dominant_wind_direction,
        dominant_swell_direction=dominant_swell_direction,
        onshore_wind_hours=onshore_wind_hours,
        onshore_swell_hours=onshore_swell_hours,
    )

    summary = _build_day_summary(
        rag=rag,
        wind_max=wind_max,
        wind_mean=wind_mean,
        gust_max=gust_max,
        dominant_wind_direction=dominant_wind_direction,
        wave_max=wave_max,
        wave_period=wave_peak_period,
        wind_wave_max=wind_wave_max,
        combined_swell_max=combined_swell_max,
        swell_peak_period=swell_peak_period,
        onshore_wind_hours=onshore_wind_hours,
        onshore_swell_hours=onshore_swell_hours,
        yacht_length_ft=yacht_length_ft,
    )

    return DayAssessment(
        key=key,
        label=label,
        short_label=short_label,
        date=day_date.isoformat(),
        rag=rag,
        rag_label=FEEL_BY_RAG[rag],
        score=score,
        feel=FEEL_BY_RAG[rag],
        summary=summary,
        daylight_start=sunrise.strftime("%H:%M"),
        daylight_end=sunset.strftime("%H:%M"),
        daylight_hours=len(daylight_samples),
        wind_mean_kt=_round_or_none(wind_mean, 1),
        wind_max_kt=_round_or_none(wind_max, 1),
        gust_max_kt=_round_or_none(gust_max, 1),
        dominant_wind_direction=dominant_wind_direction,
        wave_mean_m=_round_or_none(wave_mean, 2),
        wave_max_m=_round_or_none(wave_max, 2),
        wave_period_s=_round_or_none(wave_peak_period, 1),
        wind_wave_max_m=_round_or_none(wind_wave_max, 2),
        wind_wave_period_s=_round_or_none(wind_wave_peak_period, 1),
        swell_max_m=_round_or_none(combined_swell_max, 2),
        swell_period_s=_round_or_none(swell_peak_period, 1),
        secondary_swell_max_m=_round_or_none(secondary_swell_max, 2),
        dominant_swell_direction=dominant_swell_direction,
        steepness_index=_round_or_none(steepness_index, 3),
        onshore_wind_hours=onshore_wind_hours,
        onshore_swell_hours=onshore_swell_hours,
        drivers=drivers,
    )


def _build_weekend_summary(
    days: list[DayAssessment],
    best_day: DayAssessment,
    worst_day: DayAssessment,
    yacht_length_ft: int,
) -> str:
    if all(day.rag == RAG_GREEN for day in days):
        return (
            f"The daylight boating window looks broadly settled for a {yacht_length_ft} ft "
            f"motor yacht. {best_day.label} is the pick, but all three days currently look "
            "comfortable with only modest marina handling loads."
        )

    if worst_day.rag == RAG_RED:
        return (
            f"{best_day.label} is the easiest-looking boating day. {worst_day.label} is the "
            f"problem day, driven by {', '.join(worst_day.drivers[:2])}, so expect the sea "
            "outside the marina to feel lumpier and berthing to need more attention."
        )

    return (
        f"The weekend looks usable but mixed for a {yacht_length_ft} ft motor yacht. "
        f"{best_day.label} looks the most comfortable, while {worst_day.label} carries the "
        f"lumpier spell because of {', '.join(worst_day.drivers[:2])}."
    )


def _build_day_summary(
    *,
    rag: str,
    wind_max: float | None,
    wind_mean: float | None,
    gust_max: float | None,
    dominant_wind_direction: str | None,
    wave_max: float | None,
    wave_period: float | None,
    wind_wave_max: float | None,
    combined_swell_max: float | None,
    swell_peak_period: float | None,
    onshore_wind_hours: int,
    onshore_swell_hours: int,
    yacht_length_ft: int,
) -> str:
    wind_part = _describe_wind(
        wind_max=wind_max,
        wind_mean=wind_mean,
        gust_max=gust_max,
        dominant_wind_direction=dominant_wind_direction,
    )
    sea_part = _describe_sea(
        wave_max=wave_max,
        wave_period=wave_period,
        wind_wave_max=wind_wave_max,
        combined_swell_max=combined_swell_max,
        swell_peak_period=swell_peak_period,
        onshore_wind_hours=onshore_wind_hours,
        onshore_swell_hours=onshore_swell_hours,
    )
    handling_part = _describe_handling(rag, yacht_length_ft)

    return f"{wind_part}. {sea_part}. {handling_part}"


def _describe_wind(
    *,
    wind_max: float | None,
    wind_mean: float | None,
    gust_max: float | None,
    dominant_wind_direction: str | None,
) -> str:
    direction_text = f"{dominant_wind_direction} " if dominant_wind_direction else ""
    if wind_max is None:
        return "Wind data is limited"
    if wind_max < 12:
        return (
            f"Light {direction_text}winds, mostly around {wind_mean or wind_max:.0f} to "
            f"{wind_max:.0f} kt"
        )
    if wind_max < 18:
        return (
            f"Moderate {direction_text}breeze around {wind_mean or wind_max:.0f} to "
            f"{wind_max:.0f} kt, gusting {gust_max or wind_max:.0f} kt"
        )
    if wind_max < 24:
        return (
            f"Fresh {direction_text}winds up to {wind_max:.0f} kt with gusts around "
            f"{gust_max or wind_max:.0f} kt"
        )
    return (
        f"Strong {direction_text}winds up to {wind_max:.0f} kt with gusts around "
        f"{gust_max or wind_max:.0f} kt"
    )


def _describe_sea(
    *,
    wave_max: float | None,
    wave_period: float | None,
    wind_wave_max: float | None,
    combined_swell_max: float | None,
    swell_peak_period: float | None,
    onshore_wind_hours: int,
    onshore_swell_hours: int,
) -> str:
    wave_max = wave_max or 0
    wind_wave_max = wind_wave_max or 0
    combined_swell_max = combined_swell_max or 0

    if wave_max < 0.5 and combined_swell_max < 0.5:
        text = "Sea state looks low with only a small residual swell"
    elif wave_max < 0.9 and wind_wave_max < 0.5:
        text = "Expect a slight lump outside the breakwaters rather than a flat calm"
    elif wave_max < 1.4:
        text = "There is a noticeable sea running outside, with some lump and roll likely"
    else:
        text = "A proper lumpy sea is likely outside the marina entrance"

    if wave_period is not None and wave_period <= 5:
        text += "; the shorter periods point to a choppier feel"
    elif combined_swell_max >= 0.9 and (swell_peak_period or 0) >= 8:
        text += "; the longer swell could add some surge and rolling"

    if onshore_wind_hours >= 3 or onshore_swell_hours >= 2:
        text += " with a more direct onshore set into the Brighton frontage"

    return text


def _describe_handling(rag: str, yacht_length_ft: int) -> str:
    if rag == RAG_GREEN:
        return (
            f"For a {yacht_length_ft} ft motor yacht, close-quarters work and berthing should "
            "stay straightforward"
        )
    if rag == RAG_YELLOW:
        return (
            f"For a {yacht_length_ft} ft motor yacht, this still looks workable, but expect "
            "more movement outside and a bit more thought around berthing"
        )
    return (
        f"For a {yacht_length_ft} ft motor yacht, harbour entrance work and berthing are "
        "likely to feel harder work and less comfortable"
    )


def _build_drivers(
    *,
    wind_max: float | None,
    gust_max: float | None,
    wave_max: float | None,
    wind_wave_max: float | None,
    combined_swell_max: float | None,
    steepness_index: float | None,
    dominant_wind_direction: str | None,
    dominant_swell_direction: str | None,
    onshore_wind_hours: int,
    onshore_swell_hours: int,
) -> list[str]:
    drivers: list[str] = []

    if (wind_max or 0) >= 16:
        direction = f" {dominant_wind_direction}" if dominant_wind_direction else ""
        drivers.append(f"{wind_max:.0f} kt{direction} wind")
    if (gust_max or 0) >= 24:
        drivers.append(f"{gust_max:.0f} kt gusts")
    if (wave_max or 0) >= 0.8:
        drivers.append(f"{wave_max:.1f} m sea state")
    if (wind_wave_max or 0) >= 0.45:
        drivers.append(f"{wind_wave_max:.1f} m wind chop")
    if (combined_swell_max or 0) >= 0.75:
        direction = f" {dominant_swell_direction}" if dominant_swell_direction else ""
        drivers.append(f"{combined_swell_max:.1f} m{direction} swell")
    if (steepness_index or 0) >= 0.13:
        drivers.append("shorter wave periods")
    if onshore_wind_hours >= 3:
        drivers.append("persistent onshore wind")
    if onshore_swell_hours >= 2:
        drivers.append("onshore swell energy")

    return drivers or ["modest wind and sea state"]


def _worst_rag(days: list[DayAssessment]) -> str:
    if any(day.rag == RAG_RED for day in days):
        return RAG_RED
    if any(day.rag == RAG_YELLOW for day in days):
        return RAG_YELLOW
    if all(day.rag == RAG_GREEN for day in days):
        return RAG_GREEN
    return RAG_UNKNOWN


def _is_onshore(direction_degrees: float) -> bool:
    return ONSHORE_MIN_DEGREES <= direction_degrees <= ONSHORE_MAX_DEGREES


def _mean_direction_text(values: list[float]) -> str | None:
    if not values:
        return None

    radians = [math.radians(value) for value in values]
    sin_sum = sum(math.sin(value) for value in radians)
    cos_sum = sum(math.cos(value) for value in radians)

    if sin_sum == 0 and cos_sum == 0:
        return None

    angle = (math.degrees(math.atan2(sin_sum, cos_sum)) + 360) % 360
    return _direction_text(angle)


def _direction_text(direction_degrees: float) -> str:
    index = round(direction_degrees / 22.5) % 16
    return COMPASS_POINTS[index]


def _scaled_severity(
    value: float | None,
    green_threshold: float,
    yellow_threshold: float,
    red_threshold: float,
) -> float:
    if value is None:
        return 0
    if value <= green_threshold:
        return 0
    if value <= yellow_threshold:
        return 50 * ((value - green_threshold) / (yellow_threshold - green_threshold))
    if value <= red_threshold:
        return 50 + 50 * ((value - yellow_threshold) / (red_threshold - yellow_threshold))
    return 100


def _list_values(samples: list[HourSample], field_name: str) -> list[float]:
    values: list[float] = []
    for sample in samples:
        value = getattr(sample, field_name)
        if value is not None:
            values.append(float(value))
    return values


def _period_at_peak(
    samples: list[HourSample],
    height_field: str,
    period_field: str,
) -> float | None:
    pairs = [
        (getattr(sample, height_field), getattr(sample, period_field))
        for sample in samples
        if getattr(sample, height_field) is not None
        and getattr(sample, period_field) is not None
    ]
    if not pairs:
        return None

    _, period = max(pairs, key=lambda item: item[0])
    return float(period)


def _direction_at_peak(
    samples: list[HourSample],
    height_field: str,
    direction_field: str,
) -> str | None:
    pairs = [
        (getattr(sample, height_field), getattr(sample, direction_field))
        for sample in samples
        if getattr(sample, height_field) is not None
        and getattr(sample, direction_field) is not None
    ]
    if not pairs:
        return None

    _, direction = max(pairs, key=lambda item: item[0])
    return _direction_text(float(direction))


def _parse_datetime(value: str, tzinfo: ZoneInfo) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=tzinfo)
    return parsed.astimezone(tzinfo)


def _convert_kmh_to_knots(value: float | None) -> float | None:
    if value is None:
        return None
    return float(value) * KMH_TO_KT


def _pick(values: dict[str, list[Any]], key: str, index: int) -> float | None:
    if key not in values:
        return None
    value = values[key][index]
    return None if value is None else float(value)


def _safe_max(values: list[float]) -> float | None:
    return max(values) if values else None


def _safe_mean(values: list[float]) -> float | None:
    return mean(values) if values else None


def _round_or_none(value: float | None, digits: int) -> float | None:
    return round(value, digits) if value is not None else None
