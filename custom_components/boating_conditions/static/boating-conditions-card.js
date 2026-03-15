class BoatingConditionsCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = null;
    this._hass = null;
  }

  setConfig(config) {
    this._config = {
      title: "Boating Conditions",
      layout: "portrait",
      show_last_updated: true,
      ...(config || {}),
    };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return this._config?.layout === "landscape" ? 5 : 7;
  }

  getGridOptions() {
    return {
      columns: 12,
      min_rows: this._config?.layout === "landscape" ? 5 : 7,
    };
  }

  static getStubConfig(hass) {
    const entity = findCandidateEntity(hass);
    return {
      type: "custom:boating-conditions-card",
      title: "Boating Conditions",
      layout: "portrait",
      show_last_updated: true,
      ...(entity ? { entity } : {}),
    };
  }

  static getConfigForm() {
    return {
      schema: [
        {
          name: "entity",
          required: true,
          selector: {
            entity: {},
          },
        },
        {
          name: "title",
          selector: {
            text: {},
          },
        },
        {
          name: "layout",
          selector: {
            select: {
              mode: "dropdown",
              options: [
                {
                  label: "Portrait",
                  value: "portrait",
                },
                {
                  label: "Landscape",
                  value: "landscape",
                },
              ],
            },
          },
        },
        {
          name: "show_last_updated",
          selector: {
            boolean: {},
          },
        },
      ],
      computeLabel: (schema) => {
        if (schema.name === "entity") {
          return "Weekend sensor";
        }
        if (schema.name === "title") {
          return "Card title";
        }
        if (schema.name === "layout") {
          return "Layout";
        }
        if (schema.name === "show_last_updated") {
          return "Show last updated time";
        }
        return undefined;
      },
      computeHelper: (schema) => {
        if (schema.name === "entity") {
          return "Choose the main Boating Conditions sensor, usually the one ending in weekend_rag.";
        }
        if (schema.name === "layout") {
          return "Portrait is taller; landscape is wider and shorter.";
        }
        return undefined;
      },
    };
  }

  _render() {
    if (!this.shadowRoot || !this._config) {
      return;
    }

    const layout = normalizeLayout(this._config.layout);
    const candidateEntity = findCandidateEntity(this._hass);
    if (!this._config.entity) {
      this.shadowRoot.innerHTML = `
        <style>${styles}</style>
        <ha-card class="card layout-${layout}">
          <div class="shell layout-${layout}">
            <div class="header">
              <div>
                <h2>${escapeHtml(this._config.title || "Boating Conditions")}</h2>
              </div>
            </div>
            <div class="empty">
              <p>This card needs the main weekend Boating Conditions sensor.</p>
              ${
                candidateEntity
                  ? `<p>Suggested entity: <code>${escapeHtml(candidateEntity)}</code></p>`
                  : "<p>No matching weekend sensor was found yet. Make sure the Boating Conditions integration is installed and configured first.</p>"
              }
              <p>Open the card settings and choose the sensor that ends with <code>weekend_rag</code>.</p>
            </div>
          </div>
        </ha-card>
      `;
      return;
    }

    const stateObj = this._hass?.states?.[this._config.entity];
    if (!stateObj) {
      this.shadowRoot.innerHTML = `
        <style>${styles}</style>
        <ha-card class="card layout-${layout}">
          <div class="shell layout-${layout}">
            <div class="header">
              <div>
                <h2>${escapeHtml(this._config.title)}</h2>
              </div>
            </div>
            <div class="empty">Entity ${escapeHtml(this._config.entity)} is unavailable.</div>
          </div>
        </ha-card>
      `;
      return;
    }

    const attrs = stateObj.attributes || {};
    const days = Array.isArray(attrs.days) ? attrs.days : [];
    const overallRag = String(stateObj.state || "unknown");
    const weekendLabel = attrs.weekend_label || "Upcoming weekend";
    const summary = attrs.summary || "No weekend summary is available yet.";
    const locationName = attrs.location_name || "Brighton Marina";
    const updated = attrs.generated_at ? formatDateTime(attrs.generated_at) : "";
    const stateLabel = attrs.state_label || titleCase(overallRag);
    const subheadItems = [locationName, weekendLabel];

    this.shadowRoot.innerHTML = `
      <style>${styles}</style>
      <ha-card class="card layout-${layout}">
        <div class="shell layout-${layout}">
          <div class="glow glow-a"></div>
          <div class="glow glow-b"></div>

          <div class="header">
            <div>
              <h2>${escapeHtml(this._config.title)}</h2>
              <div class="subhead">
                ${subheadItems.map((item) => `<span>${escapeHtml(item)}</span>`).join("")}
              </div>
            </div>
            <div class="header-side">
              <div class="badges">
                <span class="status-badge rag-${escapeHtml(overallRag)}">${escapeHtml(stateLabel)}</span>
              </div>
              ${
                this._config.show_last_updated && updated
                  ? `<div class="updated-meta">Updated ${escapeHtml(updated)}</div>`
                  : ""
              }
            </div>
          </div>

          <div class="body layout-${layout}">
            <div class="primary-column">
              <div class="lamps">
                ${days.map((day) => renderLamp(day)).join("")}
              </div>

              <div class="summary-panel">
                <div class="summary-label">Weekend feel</div>
                <div class="summary-text">${escapeHtml(summary)}</div>
              </div>
            </div>

            <div class="secondary-column">
              <div class="detail-list">
                ${days.map((day) => renderDetail(day)).join("")}
              </div>
            </div>
          </div>
        </div>
      </ha-card>
    `;
  }
}

const styles = `
  :host {
    display: block;
    --boating-card-divider: rgba(var(--rgb-primary-text-color, 255, 255, 255), 0.12);
    --boating-card-panel: rgba(var(--rgb-primary-text-color, 255, 255, 255), 0.08);
    --boating-card-panel-strong: rgba(var(--rgb-primary-text-color, 255, 255, 255), 0.12);
    --boating-card-text-soft: var(--secondary-text-color);
    --boating-card-text-bright: var(--primary-text-color);
    --boating-card-sheen:
      radial-gradient(circle at top left, rgba(77, 213, 232, 0.16), transparent 36%),
      radial-gradient(circle at right 15%, rgba(255, 215, 123, 0.09), transparent 28%),
      linear-gradient(155deg, rgba(8, 37, 59, 0.24) 0%, rgba(11, 70, 98, 0.16) 50%, rgba(19, 79, 104, 0.12) 100%);
  }

  ha-card {
    overflow: hidden;
    border: 1px solid var(--boating-card-divider);
    border-radius: var(--ha-card-border-radius, 28px);
    background: var(--ha-card-background, var(--card-background-color, rgba(0, 0, 0, 0.18)));
    box-shadow: var(--ha-card-box-shadow, var(--shadow-elevation-2dp_-_box-shadow, none));
    color: var(--boating-card-text-bright);
    backdrop-filter: blur(18px) saturate(130%);
    -webkit-backdrop-filter: blur(18px) saturate(130%);
  }

  .shell {
    position: relative;
    padding: 22px;
    font-family: "Avenir Next", "Segoe UI", "Trebuchet MS", sans-serif;
    isolation: isolate;
  }

  .shell.layout-landscape {
    padding: 20px 22px 18px;
  }

  .shell::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: inherit;
    background: var(--boating-card-sheen);
    pointer-events: none;
    z-index: 0;
  }

  .glow {
    position: absolute;
    border-radius: 999px;
    pointer-events: none;
    filter: blur(28px);
    opacity: 0.42;
    z-index: 0;
  }

  .glow-a {
    width: 140px;
    height: 140px;
    right: -30px;
    top: -20px;
    background: rgba(117, 233, 255, 0.18);
  }

  .glow-b {
    width: 200px;
    height: 200px;
    left: -70px;
    bottom: -70px;
    background: rgba(255, 204, 102, 0.08);
  }

  .header {
    position: relative;
    z-index: 1;
    display: flex;
    gap: 16px;
    justify-content: space-between;
    align-items: flex-start;
    flex-wrap: wrap;
    margin-bottom: 18px;
  }

  h2 {
    margin: 0 0 8px;
    font-size: 1.6rem;
    line-height: 1.05;
    letter-spacing: 0.01em;
  }

  .subhead,
  .badges {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    align-items: center;
  }

  .header-side {
    display: grid;
    gap: 8px;
    justify-items: end;
    text-align: right;
  }

  .subhead span,
  .updated-meta {
    color: var(--boating-card-text-soft);
    font-size: 0.88rem;
  }

  .status-badge {
    padding: 7px 12px;
    border-radius: 999px;
    backdrop-filter: blur(14px);
    font-weight: 700;
  }

  .status-badge {
    color: #04141f;
  }

  .body {
    position: relative;
    z-index: 1;
    display: grid;
    gap: 14px;
  }

  .body.layout-landscape {
    grid-template-columns: minmax(0, 1.08fr) minmax(0, 0.92fr);
    align-items: start;
  }

  .primary-column,
  .secondary-column {
    display: grid;
    gap: 14px;
    min-width: 0;
  }

  .rag-green {
    background: #85e89a;
  }

  .rag-yellow {
    background: #ffd970;
  }

  .rag-red {
    background: #ff897d;
  }

  .rag-unknown {
    background: #d2dde5;
  }

  .lamps {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    margin-bottom: 18px;
  }

  .layout-landscape .lamps {
    margin-bottom: 0;
  }

  .lamp {
    padding: 14px 12px 12px;
    border-radius: 22px;
    background: var(--boating-card-panel);
    border: 1px solid var(--boating-card-divider);
    min-height: 164px;
  }

  .layout-landscape .lamp {
    min-height: 136px;
  }

  .lamp-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 12px;
  }

  .lamp-day {
    font-weight: 800;
    font-size: 1rem;
  }

  .lamp-date {
    color: var(--boating-card-text-soft);
    font-size: 0.8rem;
    margin-top: 3px;
  }

  .lamp-feel {
    color: var(--boating-card-text-bright);
    font-size: 0.84rem;
    margin-top: 8px;
  }

  .signal {
    width: 44px;
    height: 44px;
    border-radius: 999px;
    border: 3px solid rgba(var(--rgb-primary-text-color, 255, 255, 255), 0.18);
    box-shadow: inset 0 0 0 2px rgba(6, 18, 28, 0.18);
  }

  .signal.rag-green {
    box-shadow:
      0 0 24px rgba(133, 232, 154, 0.6),
      inset 0 0 0 2px rgba(6, 18, 28, 0.12);
  }

  .signal.rag-yellow {
    box-shadow:
      0 0 24px rgba(255, 217, 112, 0.55),
      inset 0 0 0 2px rgba(6, 18, 28, 0.12);
  }

  .signal.rag-red {
    box-shadow:
      0 0 24px rgba(255, 137, 125, 0.55),
      inset 0 0 0 2px rgba(6, 18, 28, 0.12);
  }

  .lamp-metrics {
    display: grid;
    gap: 6px;
    font-size: 0.82rem;
    color: var(--boating-card-text-bright);
  }

  .metric-chip {
    display: inline-flex;
    width: fit-content;
    padding: 5px 10px;
    border-radius: 999px;
    background: var(--boating-card-panel);
    border: 1px solid var(--boating-card-divider);
  }

  .summary-panel {
    margin-bottom: 14px;
    padding: 16px 18px;
    border-radius: 24px;
    background:
      linear-gradient(
        135deg,
        rgba(var(--rgb-primary-text-color, 255, 255, 255), 0.12),
        rgba(var(--rgb-primary-text-color, 255, 255, 255), 0.05)
      );
    border: 1px solid var(--boating-card-divider);
  }

  .layout-landscape .summary-panel {
    margin-bottom: 0;
  }

  .summary-label {
    color: var(--boating-card-text-soft);
    font-size: 0.78rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 8px;
  }

  .summary-text {
    font-size: 1rem;
    line-height: 1.55;
  }

  .detail-list {
    display: grid;
    gap: 10px;
  }

  .detail-row {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 12px;
    align-items: start;
    padding: 12px 14px;
    border-radius: 18px;
    background: rgba(var(--rgb-primary-text-color, 255, 255, 255), 0.05);
    border: 1px solid var(--boating-card-divider);
  }

  .detail-pill {
    min-width: 48px;
    text-align: center;
    padding: 6px 10px;
    border-radius: 999px;
    color: #061119;
    font-weight: 800;
    font-size: 0.78rem;
  }

  .detail-summary {
    font-size: 0.92rem;
    line-height: 1.45;
    color: var(--boating-card-text-bright);
  }

  .empty {
    padding: 18px 0 4px;
    color: var(--boating-card-text-bright);
  }

  @media (max-width: 640px) {
    .shell {
      padding: 18px;
    }

    .header-side {
      justify-items: start;
      text-align: left;
    }

    .lamps {
      gap: 10px;
    }

    .lamp {
      min-height: 0;
      padding: 12px 10px;
    }

    .lamp-day {
      font-size: 0.92rem;
    }

    .lamp-metrics {
      font-size: 0.76rem;
    }

    .summary-text,
    .detail-summary {
      font-size: 0.9rem;
    }
  }

  @media (max-width: 900px) {
    .body.layout-landscape {
      grid-template-columns: 1fr;
    }
  }
`;

function renderLamp(day) {
  const rag = String(day.rag || "unknown");
  const wind = formatNumber(day.wind_max_kt, "kt");
  const wave = formatNumber(day.wave_max_m, "m");
  const swell = formatNumber(day.swell_max_m, "m");
  const swellPeriod = formatNumber(day.swell_period_s, "s", false);
  const daylight = [day.daylight_start, day.daylight_end].filter(Boolean).join(" - ");

  return `
    <div class="lamp">
      <div class="lamp-head">
        <div>
          <div class="lamp-day">${escapeHtml(day.short_label || "")}</div>
          <div class="lamp-date">${escapeHtml(day.label || "")}</div>
        </div>
        <div class="signal rag-${escapeHtml(rag)}"></div>
      </div>
      <div class="lamp-feel">${escapeHtml(day.feel || titleCase(rag))}</div>
      <div class="lamp-metrics">
        <span class="metric-chip">Wind ${escapeHtml(wind)}</span>
        <span class="metric-chip">Sea ${escapeHtml(wave)} | Swell ${escapeHtml(swell)}</span>
        <span class="metric-chip">Period ${escapeHtml(swellPeriod)} | ${escapeHtml(daylight)}</span>
      </div>
    </div>
  `;
}

function renderDetail(day) {
  const rag = String(day.rag || "unknown");
  return `
    <div class="detail-row">
      <div class="detail-pill rag-${escapeHtml(rag)}">${escapeHtml((day.short_label || "").toUpperCase())}</div>
      <div class="detail-summary">${escapeHtml(day.summary || "No narrative available.")}</div>
    </div>
  `;
}

function formatDateTime(value) {
  try {
    return new Intl.DateTimeFormat(undefined, {
      weekday: "short",
      day: "numeric",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(value));
  } catch (_error) {
    return String(value);
  }
}

function formatNumber(value, suffix, includeSpace = true) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "n/a";
  }

  const formatted = Number(value).toFixed(Number(value) >= 10 ? 0 : 1).replace(/\.0$/, "");
  return includeSpace ? `${formatted} ${suffix}` : `${formatted}${suffix}`;
}

function titleCase(value) {
  return String(value)
    .replace(/_/g, " ")
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

function normalizeLayout(value) {
  return value === "landscape" ? "landscape" : "portrait";
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function getCandidateEntities(hass) {
  if (!hass?.states) {
    return [];
  }

  return Object.entries(hass.states)
    .filter(([entityId, stateObj]) => {
      if (!entityId.startsWith("sensor.")) {
        return false;
      }

      const attrs = stateObj?.attributes || {};
      return Array.isArray(attrs.days) && typeof attrs.summary === "string";
    })
    .map(([entityId]) => entityId)
    .sort();
}

function findCandidateEntity(hass) {
  return getCandidateEntities(hass)[0] || "";
}

if (!customElements.get("boating-conditions-card")) {
  customElements.define("boating-conditions-card", BoatingConditionsCard);
}

window.customCards = window.customCards || [];
window.customCards.push({
  type: "boating-conditions-card",
  name: "Boating Conditions",
  description: "Three-lamp weekend boating outlook for Brighton Marina",
  documentationURL:
    "https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card",
  preview: true,
});
