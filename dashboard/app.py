from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import altair as alt
import pandas as pd
import streamlit as st
import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config" / "dashboard.yaml"

COLOR = {
    "ink": "#12243A",
    "muted": "#5B6B7C",
    "surface": "#F7F9FC",
    "line": "#D7E0EA",
    "blue": "#1976A3",
    "green": "#17835B",
    "amber": "#B66A0B",
    "red": "#B94343",
    "violet": "#6E5AA6",
}


@st.cache_data(ttl=5)
def load_config() -> dict[str, Any]:
    payload = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    return payload["dashboard"]


def load_logs(path: Path, *, time_range_minutes: int) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()

    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)

    frame = pd.json_normalize(records)
    if frame.empty or "ts" not in frame:
        return frame

    frame["ts"] = pd.to_datetime(frame["ts"], utc=True, errors="coerce")
    frame = frame.dropna(subset=["ts"])
    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=time_range_minutes)
    return frame.loc[frame["ts"] >= cutoff].sort_values("ts").copy()


def event_rows(frame: pd.DataFrame, event: str) -> pd.DataFrame:
    if frame.empty or "event" not in frame:
        return pd.DataFrame()
    return frame.loc[frame["event"] == event].copy()


def numeric(frame: pd.DataFrame, field: str) -> pd.Series:
    if frame.empty or field not in frame:
        return pd.Series(dtype="float64")
    return pd.to_numeric(frame[field], errors="coerce").dropna()


def percentile(series: pd.Series, quantile: float) -> float:
    return float(series.quantile(quantile)) if not series.empty else 0.0


def threshold_passes(value: float, *, threshold: float, operator: str) -> bool:
    return value <= threshold if operator == "lte" else value >= threshold


def status_badge(value: float, *, threshold: float, operator: str) -> None:
    passed = threshold_passes(value, threshold=threshold, operator=operator)
    css_class = "status-ok" if passed else "status-bad"
    label = "Within threshold" if passed else "Threshold breached"
    st.markdown(f'<span class="{css_class}">{label}</span>', unsafe_allow_html=True)


def threshold_rule(value: float, *, color: str = COLOR["red"]) -> alt.Chart:
    return (
        alt.Chart(pd.DataFrame({"threshold": [value]}))
        .mark_rule(color=color, strokeDash=[7, 5], strokeWidth=1.5)
        .encode(y="threshold:Q")
    )


def empty_chart_message(message: str) -> None:
    st.info(message, icon="ℹ️")


def render_latency(responses: pd.DataFrame, panel: dict[str, Any]) -> None:
    st.markdown(f"### {panel['title']}")
    latency = numeric(responses, "latency_ms")
    ttft = numeric(responses, "ttft_ms")
    values = {
        "P50": percentile(latency, 0.50),
        "P95": percentile(latency, 0.95),
        "P99": percentile(latency, 0.99),
        "TTFT P95": percentile(ttft, 0.95),
    }
    columns = st.columns(4)
    for column, (label, value) in zip(columns, values.items()):
        column.metric(label, f"{value:,.0f} ms")

    threshold = float(panel["threshold"]["value"])
    status_badge(
        values["P95"],
        threshold=threshold,
        operator=panel["threshold"]["operator"],
    )

    if responses.empty or "latency_ms" not in responses:
        empty_chart_message("No response latency is available in this window.")
        return

    chart_data = responses[["ts", "latency_ms", "correlation_id"]].copy()
    chart_data["latency_ms"] = pd.to_numeric(
        chart_data["latency_ms"], errors="coerce"
    )
    line = (
        alt.Chart(chart_data.dropna(subset=["latency_ms"]))
        .mark_line(point=alt.OverlayMarkDef(size=38), color=COLOR["blue"], strokeWidth=2)
        .encode(
            x=alt.X("ts:T", title="Time (UTC)"),
            y=alt.Y("latency_ms:Q", title="Latency (ms)"),
            tooltip=[
                alt.Tooltip("ts:T", title="Time"),
                alt.Tooltip("latency_ms:Q", title="Latency", format=",.0f"),
                alt.Tooltip("correlation_id:N", title="Correlation ID"),
            ],
        )
    )
    st.altair_chart(line + threshold_rule(threshold), width="stretch")
    st.caption(f"SLO line: latency P95 ≤ {threshold:,.0f} ms")


def render_traffic(requests: pd.DataFrame, panel: dict[str, Any]) -> None:
    st.markdown(f"### {panel['title']}")
    window_minutes = int(load_config()["time_range_minutes"])
    count = len(requests)
    average_rate = count / window_minutes
    left, right = st.columns(2)
    left.metric("Requests", f"{count:,}")
    right.metric("Average rate", f"{average_rate:.2f}/min")

    threshold = float(panel["threshold"]["value"])
    status_badge(
        average_rate,
        threshold=threshold,
        operator=panel["threshold"]["operator"],
    )
    if requests.empty:
        empty_chart_message("No requests are available in this window.")
        return

    traffic = (
        requests.set_index("ts")
        .resample("1min")
        .size()
        .rename("requests_per_minute")
        .reset_index()
    )
    bars = (
        alt.Chart(traffic)
        .mark_bar(color=COLOR["violet"], cornerRadiusTopLeft=2, cornerRadiusTopRight=2)
        .encode(
            x=alt.X("ts:T", title="Time (UTC)"),
            y=alt.Y("requests_per_minute:Q", title="Requests / minute"),
            tooltip=["ts:T", "requests_per_minute:Q"],
        )
    )
    st.altair_chart(
        bars + threshold_rule(threshold, color=COLOR["amber"]), width="stretch"
    )
    st.caption(f"Traffic guardrail: average ≥ {threshold:g} request/minute")


def render_errors(
    frame: pd.DataFrame,
    requests: pd.DataFrame,
    failures: pd.DataFrame,
    panel: dict[str, Any],
) -> None:
    st.markdown(f"### {panel['title']}")
    error_rate = len(failures) / len(requests) * 100 if len(requests) else 0.0

    if "tool_success" in frame:
        tool_records = frame.loc[frame["tool_success"].notna()].copy()
    else:
        tool_records = pd.DataFrame()
    if tool_records.empty:
        retrieval_success = 0.0
    else:
        succeeded = tool_records["tool_success"].map(
            lambda value: value is True or str(value).lower() == "true"
        )
        retrieval_success = float(succeeded.mean() * 100)

    left, right = st.columns(2)
    left.metric("Error rate", f"{error_rate:.2f}%")
    right.metric("Retrieval success", f"{retrieval_success:.2f}%")

    threshold = float(panel["threshold"]["value"])
    status_badge(
        error_rate,
        threshold=threshold,
        operator=panel["threshold"]["operator"],
    )
    if not failures.empty and "error_type" in failures:
        breakdown = (
            failures["error_type"]
            .fillna("unknown")
            .value_counts()
            .rename_axis("error_type")
            .reset_index(name="count")
        )
        chart = (
            alt.Chart(breakdown)
            .mark_bar(color=COLOR["red"])
            .encode(
                x=alt.X("count:Q", title="Failures"),
                y=alt.Y("error_type:N", title=None, sort="-x"),
                tooltip=["error_type:N", "count:Q"],
            )
        )
        st.altair_chart(chart, width="stretch")
    else:
        st.success("No request failures in the selected time window.")
    st.caption("Guardrails: error rate ≤ 2% · retrieval success ≥ 90%")


def render_cost(responses: pd.DataFrame, panel: dict[str, Any]) -> None:
    st.markdown(f"### {panel['title']}")
    cost = numeric(responses, "cost_usd")
    total_cost = float(cost.sum()) if not cost.empty else 0.0
    st.metric("Window cost", f"${total_cost:,.6f}")

    threshold = float(panel["threshold"]["value"])
    status_badge(
        total_cost,
        threshold=threshold,
        operator=panel["threshold"]["operator"],
    )
    if responses.empty or "cost_usd" not in responses:
        empty_chart_message("No cost data is available in this window.")
        return

    cost_by_minute = responses[["ts", "cost_usd"]].copy()
    cost_by_minute["cost_usd"] = pd.to_numeric(
        cost_by_minute["cost_usd"], errors="coerce"
    )
    cost_by_minute = (
        cost_by_minute.dropna(subset=["cost_usd"])
        .set_index("ts")["cost_usd"]
        .resample("1min")
        .sum()
        .reset_index()
    )
    area = (
        alt.Chart(cost_by_minute)
        .mark_area(color=COLOR["amber"], opacity=0.28, line={"color": COLOR["amber"]})
        .encode(
            x=alt.X("ts:T", title="Time (UTC)"),
            y=alt.Y("cost_usd:Q", title="USD / minute"),
            tooltip=[alt.Tooltip("ts:T"), alt.Tooltip("cost_usd:Q", format="$.6f")],
        )
    )
    st.altair_chart(area, width="stretch")
    st.caption(f"Window budget: total cost ≤ ${threshold:g}")


def render_tokens(responses: pd.DataFrame, panel: dict[str, Any]) -> None:
    st.markdown(f"### {panel['title']}")
    total_in = int(numeric(responses, "tokens_in").sum())
    total_out = int(numeric(responses, "tokens_out").sum())
    total = total_in + total_out
    cols = st.columns(3)
    cols[0].metric("Input", f"{total_in:,}")
    cols[1].metric("Output", f"{total_out:,}")
    cols[2].metric("Total", f"{total:,}")

    threshold = float(panel["threshold"]["value"])
    status_badge(
        total,
        threshold=threshold,
        operator=panel["threshold"]["operator"],
    )
    data = pd.DataFrame(
        {"direction": ["Input", "Output"], "tokens": [total_in, total_out]}
    )
    chart = (
        alt.Chart(data)
        .mark_bar(cornerRadiusEnd=3)
        .encode(
            x=alt.X("tokens:Q", title="Tokens"),
            y=alt.Y("direction:N", title=None, sort=["Input", "Output"]),
            color=alt.Color(
                "direction:N",
                scale=alt.Scale(
                    domain=["Input", "Output"],
                    range=[COLOR["blue"], COLOR["violet"]],
                ),
                legend=None,
            ),
            tooltip=["direction:N", "tokens:Q"],
        )
    )
    st.altair_chart(chart, width="stretch")
    st.caption(f"Window guardrail: total tokens ≤ {threshold:,.0f}")


def render_quality(responses: pd.DataFrame, panel: dict[str, Any]) -> None:
    st.markdown(f"### {panel['title']}")
    quality = numeric(responses, "quality_score")
    average = float(quality.mean()) if not quality.empty else 0.0
    st.metric("Average quality", f"{average:.2f} / 1.00")

    threshold = float(panel["threshold"]["value"])
    status_badge(
        average,
        threshold=threshold,
        operator=panel["threshold"]["operator"],
    )
    if responses.empty or "quality_score" not in responses:
        empty_chart_message("No quality scores are available in this window.")
        return

    quality_data = responses[["ts", "quality_score", "correlation_id"]].copy()
    quality_data["quality_score"] = pd.to_numeric(
        quality_data["quality_score"], errors="coerce"
    )
    line = (
        alt.Chart(quality_data.dropna(subset=["quality_score"]))
        .mark_line(point=True, color=COLOR["green"], strokeWidth=2)
        .encode(
            x=alt.X("ts:T", title="Time (UTC)"),
            y=alt.Y("quality_score:Q", title="Score", scale=alt.Scale(domain=[0, 1])),
            tooltip=["ts:T", "quality_score:Q", "correlation_id:N"],
        )
    )
    st.altair_chart(
        line + threshold_rule(threshold, color=COLOR["amber"]), width="stretch"
    )
    st.caption(f"Quality floor: average score ≥ {threshold:.2f}")


def inject_styles() -> None:
    st.markdown(
        f"""
        <style>
        :root {{
            --ops-ink: {COLOR['ink']};
            --ops-muted: {COLOR['muted']};
            --ops-surface: {COLOR['surface']};
            --ops-line: {COLOR['line']};
        }}
        .stApp {{
            background:
                linear-gradient(rgba(25,118,163,.035) 1px, transparent 1px),
                linear-gradient(90deg, rgba(25,118,163,.035) 1px, transparent 1px),
                var(--ops-surface);
            background-size: 28px 28px;
            color: var(--ops-ink);
            font-family: "Segoe UI", sans-serif;
        }}
        h1, h2, h3 {{
            color: var(--ops-ink) !important;
            font-family: Bahnschrift, "Arial Narrow", sans-serif !important;
            letter-spacing: -.02em;
        }}
        h1 {{ font-size: 2.25rem !important; }}
        h3 {{
            border-bottom: 1px solid var(--ops-line);
            padding-bottom: .55rem;
            font-size: 1.16rem !important;
        }}
        [data-testid="stMetric"] {{
            background: rgba(255,255,255,.78);
            border-left: 3px solid {COLOR['blue']};
            padding: .55rem .7rem;
        }}
        [data-testid="stMetricLabel"] {{ color: var(--ops-muted); }}
        [data-testid="stMetricValue"] {{ color: var(--ops-ink); }}
        .ops-ribbon {{
            display: flex;
            flex-wrap: wrap;
            gap: .55rem 1.4rem;
            margin: .25rem 0 1.1rem;
            padding: .75rem .9rem;
            background: #EAF1F7;
            border: 1px solid #CBD8E5;
            border-left: 5px solid {COLOR['blue']};
            color: #30465D;
            font-size: .91rem;
        }}
        .status-ok, .status-bad {{
            display: inline-block;
            margin: .55rem 0 .35rem;
            padding: .18rem .52rem;
            border-radius: 3px;
            font-size: .82rem;
            font-weight: 650;
        }}
        .status-ok {{ color: #0A5C3C; background: #DDF2E8; border: 1px solid #AFDAC8; }}
        .status-bad {{ color: #8A2525; background: #F8DFDF; border: 1px solid #EAB8B8; }}
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: rgba(255,255,255,.72);
            border-color: var(--ops-line) !important;
            border-radius: 7px !important;
        }}
        footer {{ visibility: hidden; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard() -> None:
    config = load_config()
    panel_by_id = {panel["id"]: panel for panel in config["panels"]}
    log_path = REPO_ROOT / panel_by_id["latency"]["source"]
    frame = load_logs(log_path, time_range_minutes=config["time_range_minutes"])

    st.title(config["title"])
    st.markdown(
        f"""
        <div class="ops-ribbon">
          <span><strong>Source</strong> {log_path.relative_to(REPO_ROOT)}</span>
          <span><strong>Window</strong> last {config['time_range_minutes']} minutes</span>
          <span><strong>Refresh</strong> {config['refresh_seconds']} seconds</span>
          <span><strong>Records</strong> {len(frame):,}</span>
          <span><strong>Timezone</strong> UTC</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if frame.empty:
        st.warning(
            "No logs were found in the active 60-minute window. Start the API, "
            "run `python scripts/load_test.py --concurrency 5`, then refresh this page.",
            icon="⚠️",
        )
        return

    requests = event_rows(frame, "request_received")
    responses = event_rows(frame, "response_sent")
    failures = event_rows(frame, "request_failed")

    row1_left, row1_right = st.columns([1.18, 0.82], gap="large")
    with row1_left.container(border=True):
        render_latency(responses, panel_by_id["latency"])
    with row1_right.container(border=True):
        render_traffic(requests, panel_by_id["traffic"])

    row2_left, row2_right = st.columns(2, gap="large")
    with row2_left.container(border=True):
        render_errors(frame, requests, failures, panel_by_id["errors"])
    with row2_right.container(border=True):
        render_cost(responses, panel_by_id["cost"])

    row3_left, row3_right = st.columns(2, gap="large")
    with row3_left.container(border=True):
        render_tokens(responses, panel_by_id["tokens"])
    with row3_right.container(border=True):
        render_quality(responses, panel_by_id["quality"])

    if "ts" in frame:
        st.caption(
            "Visible data: "
            f"{frame['ts'].min().strftime('%Y-%m-%d %H:%M:%S')} → "
            f"{frame['ts'].max().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )


st.set_page_config(
    page_title="K4-L3B Monitoring & LLMOps",
    page_icon="◫",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_styles()

dashboard_config = load_config()


@st.fragment(run_every=f"{dashboard_config['refresh_seconds']}s")
def dashboard_fragment() -> None:
    render_dashboard()


dashboard_fragment()
