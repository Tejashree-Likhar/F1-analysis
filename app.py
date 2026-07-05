"""
F1 Insights
===========
A Streamlit dashboard exploring 25 seasons (2000-2024) of real Formula 1
race data: win/podium leaders, grid-vs-finish patterns, circuit factors,
per-season driver timelines, and head-to-head driver comparisons.

Run with:  streamlit run app.py
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.theme import CUSTOM_CSS, TEAM_COLORS, team_color

DATA_DIR = Path(__file__).resolve().parent / "data"

st.set_page_config(
    page_title="F1 Insights",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

PLOTLY_TEMPLATE = "plotly_dark"


# ---------------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------------
@st.cache_data
def load_clean_data():
    df = pd.read_csv(DATA_DIR / "race_data_clean.csv")
    # per-race win flag, robust across eras with different points scales.
    # NOTE: uses race_points (points scored AT this Grand Prix), not the
    # raw `points` column, which is actually the cumulative season total.
    race_max = df.groupby("raceId")["race_points"].transform("max")
    df["is_win"] = (df["race_points"] == race_max) & (df["race_points"] > 0)
    df["is_podium"] = df["Top 3 Finish"] == 1
    return df


df = load_clean_data()


def metric_card(label, value, col):
    col.markdown(
        f"""<div class="metric-card"><div class="label">{label}</div>
        <div class="value">{value}</div></div>""",
        unsafe_allow_html=True,
    )


def order_by_round(frame, round_col="round", name_col="race_name"):
    """Return the race names in chronological (round) order, for use as a
    category order on an x-axis, so 'Round 3' reliably shows before 'Round 4'
    even though we're labeling the axis with the race name instead of a bare
    number."""
    return (
        frame[[round_col, name_col]]
        .drop_duplicates()
        .sort_values(round_col)[name_col]
        .tolist()
    )


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
st.sidebar.markdown(
    "<h2 style='font-family:Orbitron;color:#F4F4F4;'>🏁 F1 INSIGHTS</h2>",
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    "<p style='color:#9AA3AF;margin-top:-10px;'>Exploring 25 seasons of real F1 data</p>",
    unsafe_allow_html=True,
)
PAGE = st.sidebar.radio(
    "Navigate",
    [
        "🏠 Overview",
        "📊 Historical Explorer",
        "📈 Driver Timelines",
        "⚔️ Driver Comparison",
    ],
    label_visibility="collapsed",
)
st.sidebar.markdown("<div class='checkered'></div>", unsafe_allow_html=True)
st.sidebar.markdown(
    "<p style='color:#9AA3AF;font-size:0.8rem;'>Dataset: 9,839 real race entries, "
    "2000-2024.</p>",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# PAGE: Overview
# ---------------------------------------------------------------------------
if PAGE == "🏠 Overview":
    st.markdown(
        """<div class="f1-hero">
        <h1>🏎️ F1 Insights</h1>
        <p>25 seasons of real Formula 1 race results — explore win and podium
        leaders, grid-to-finish patterns, circuit factors, season-by-season
        driver timelines, and head-to-head driver comparisons.</p>
        </div>""",
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    metric_card("Race entries analyzed", f"{len(df):,}", c1)
    metric_card("Seasons covered", "2000 – 2024", c2)
    metric_card("Drivers", f"{df['driver_name'].nunique()}", c3)
    metric_card("Constructors", f"{df['constructor_name'].nunique()}", c4)

    st.write("")
    left, right = st.columns([1.3, 1])

    with left:
        st.subheader("Points scored by circuit type (rain vs dry)")
        agg = df.groupby("rainy")["race_points"].mean().reset_index()
        agg["Condition"] = agg["rainy"].map({0: "Dry", 1: "Wet"})
        fig = px.bar(
            agg, x="Condition", y="race_points", color="Condition",
            color_discrete_map={"Dry": "#3B82F6", "Wet": "#E10600"},
            template=PLOTLY_TEMPLATE, text_auto=".2f",
        )
        fig.update_layout(showlegend=False, yaxis_title="Avg. points scored", height=360)
        st.plotly_chart(fig, width="stretch")

    with right:
        st.subheader("Races per season")
        races_per_year = df.groupby("year")["raceId"].nunique().reset_index()
        fig2 = px.area(
            races_per_year, x="year", y="raceId", template=PLOTLY_TEMPLATE,
            color_discrete_sequence=["#E10600"],
        )
        fig2.update_layout(yaxis_title="Races", xaxis_title="Year", height=360)
        st.plotly_chart(fig2, width="stretch")

    st.info(
        "Use the sidebar to explore historical trends, see every driver's "
        "season timeline, or compare two drivers head-to-head.",
        icon="🏁",
    )


# ---------------------------------------------------------------------------
# PAGE: Historical Explorer
# ---------------------------------------------------------------------------
elif PAGE == "📊 Historical Explorer":
    st.markdown("## 📊 Historical Explorer")
    st.markdown("<div class='f1-stripe'></div>", unsafe_allow_html=True)

    years = sorted(df["year"].unique())
    yr_range = st.slider(
        "Season range", int(years[0]), int(years[-1]), (int(years[0]), int(years[-1]))
    )
    sub = df[(df["year"] >= yr_range[0]) & (df["year"] <= yr_range[1])]

    tab1, tab2, tab3 = st.tabs(["🏆 Win/podium leaders", "🎯 Grid vs finish", "🌧️ Circuit factors"])

    with tab1:
        # wins, races entered, and losses per driver in the selected range
        stats = (
            sub.groupby("driver_name")
            .agg(wins=("is_win", "sum"), races=("is_win", "count"))
            .reset_index()
        )
        stats["losses"] = stats["races"] - stats["wins"]
        stats = stats[stats["wins"] > 0].sort_values("wins", ascending=False)

        n_available = len(stats)
        top_n = st.slider(
            "Show top N drivers", 5, max(5, n_available),
            min(15, n_available) if n_available else 5,
        )
        st.caption(f"{n_available} drivers won at least one race in this range.")

        top_stats = stats.head(top_n).sort_values("wins")  # ascending for horizontal bar (top at top)

        fig = go.Figure(go.Bar(
            x=top_stats["wins"],
            y=top_stats["driver_name"],
            orientation="h",
            marker=dict(
                color=top_stats["wins"],
                colorscale="Reds",
            ),
            customdata=top_stats["losses"],
            hovertemplate="<b>%{y}</b><br>Wins: %{x}<br>Losses: %{customdata}<extra></extra>",
        ))
        fig.update_layout(
            template=PLOTLY_TEMPLATE, height=max(400, 24 * len(top_stats)),
            xaxis_title="Race wins", yaxis_title="",
        )
        st.plotly_chart(fig, width="stretch")

    with tab2:
        st.caption("Does starting further back still lead to a podium? Each dot is one race result.")
        sample = sub.sample(min(4000, len(sub)), random_state=1)
        fig = px.strip(
            sample, x="grid", y="race_points", color="is_podium",
            color_discrete_map={True: "#FFD400", False: "#3B82F6"},
            template=PLOTLY_TEMPLATE,
            labels={"grid": "Starting grid position", "race_points": "Points scored", "is_podium": "Podium"},
        )
        fig.update_layout(height=480)
        st.plotly_chart(fig, width="stretch")

    with tab3:
        c1, c2 = st.columns(2)
        with c1:
            st.caption(
                "What share of race results land in each points bracket — "
                "dry vs wet. 'No points' means finishing outside the top 10."
            )
            bins = [-0.1, 0, 5, 10, 15, 25.1]
            labels = ["No points (11th+)", "1–5", "6–10", "11–15", "16–25"]
            tmp = sub.copy()
            tmp["bracket"] = pd.cut(tmp["race_points"], bins=bins, labels=labels)
            dist = tmp.groupby(["rainy", "bracket"], observed=True).size().reset_index(name="count")
            dist["pct"] = 100 * dist["count"] / dist.groupby("rainy")["count"].transform("sum")
            dist["Condition"] = dist["rainy"].map({0: "Dry", 1: "Wet"})
            fig = px.bar(
                dist, x="bracket", y="pct", color="Condition", barmode="group",
                template=PLOTLY_TEMPLATE, category_orders={"bracket": labels},
                color_discrete_map={"Dry": "#3B82F6", "Wet": "#E10600"},
                labels={"bracket": "Points scored", "pct": "% of race results"},
            )
            fig.update_layout(height=440, title="Points scored: dry vs wet", legend_title="")
            st.plotly_chart(fig, width="stretch")
        with c2:
            st.caption(
                "How many *different* drivers have reached the podium at "
                "each circuit — a high count means the podium there is hard "
                "to predict; a low count means the same few drivers keep "
                "winning it. Limited to circuits that have hosted 5+ races."
            )
            races_held = sub.groupby("circuit_name")["raceId"].nunique()
            eligible = races_held[races_held >= 5].index
            podium_diversity = (
                sub[sub["is_podium"] & sub["circuit_name"].isin(eligible)]
                .groupby("circuit_name")["driver_name"].nunique()
                .sort_values(ascending=False).head(12)
            )
            fig2 = px.bar(
                podium_diversity[::-1], orientation="h", template=PLOTLY_TEMPLATE,
                color=podium_diversity[::-1].values, color_continuous_scale="Oranges",
                labels={"value": "Unique podium finishers", "circuit_name": ""},
            )
            fig2.update_layout(coloraxis_showscale=False, height=440, title="Most unpredictable podiums by circuit")
            st.plotly_chart(fig2, width="stretch")


# ---------------------------------------------------------------------------
# PAGE: Driver Timelines  (ups & downs per year / Grand Prix)
# ---------------------------------------------------------------------------
elif PAGE == "📈 Driver Timelines":
    st.markdown("## 📈 Driver Timelines — Ups & Downs")
    st.markdown("<div class='f1-stripe'></div>", unsafe_allow_html=True)
    st.caption(
        "Championship points progression across a season, Grand Prix by "
        "Grand Prix. Click a driver's name in the legend to isolate their "
        "line, or pick a driver below to see their race-by-race wins and "
        "losses."
    )

    year = st.selectbox("Season", sorted(df["year"].unique(), reverse=True), index=0)
    yr_df = df[df["year"] == year].sort_values(["driver_name", "round"])
    race_order = order_by_round(yr_df)

    fig = go.Figure()
    for drv, g in yr_df.groupby("driver_name"):
        g = g.sort_values("round")
        team = g["constructor_name"].iloc[-1]
        fig.add_trace(go.Scatter(
            x=g["race_name"], y=g["points_driver_champ"], mode="lines+markers", name=drv,
            line=dict(width=2, color=team_color(team) if team in TEAM_COLORS else None),
            marker=dict(size=5),
            hovertemplate=f"<b>{drv}</b><br>%{{x}}<br>Championship points: %{{y}}<extra></extra>",
        ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE, height=560,
        xaxis_title="Grand Prix", xaxis=dict(categoryorder="array", categoryarray=race_order, tickangle=-45),
        yaxis_title="Cumulative championship points",
        legend=dict(font=dict(size=10)),
        hovermode="closest",
    )
    st.plotly_chart(fig, width="stretch")

    st.markdown("### 🔍 Driver deep-dive")
    driver_list = sorted(yr_df["driver_name"].unique())
    sel_driver = st.selectbox("Pick a driver to see their wins & losses timeline", driver_list)

    dd = yr_df[yr_df["driver_name"] == sel_driver].sort_values("round").copy()
    dd_race_order = order_by_round(dd)

    def outcome(row):
        if row["is_win"]:
            return "Win"
        elif row["is_podium"]:
            return "Podium"
        elif row["race_points"] > 0:
            return "Points"
        else:
            return "No points (loss)"

    dd["outcome"] = dd.apply(outcome, axis=1)
    outcome_colors = {"Win": "#FFD400", "Podium": "#C0C0C0", "Points": "#3B82F6", "No points (loss)": "#3A3F4B"}

    n_wins = int(dd["is_win"].sum())
    n_races = len(dd)
    c1, c2, c3, c4 = st.columns(4)
    metric_card("Wins", n_wins, c1)
    metric_card("Losses", n_races - n_wins, c2)
    metric_card("Podiums", int(dd["is_podium"].sum()), c3)
    metric_card("Total points", f"{dd['race_points'].sum():.0f}", c4)

    fig2 = px.bar(
        dd, x="race_name", y="race_points", color="outcome",
        color_discrete_map=outcome_colors, template=PLOTLY_TEMPLATE,
        labels={"race_name": "Grand Prix", "race_points": "Points scored"},
        category_orders={"race_name": dd_race_order},
    )
    fig2.update_layout(height=420, legend_title="Result", xaxis_tickangle=-45)
    st.plotly_chart(fig2, width="stretch")


# ---------------------------------------------------------------------------
# PAGE: Driver Comparison
# ---------------------------------------------------------------------------
elif PAGE == "⚔️ Driver Comparison":
    st.markdown("## ⚔️ Driver Comparison")
    st.markdown("<div class='f1-stripe'></div>", unsafe_allow_html=True)

    all_drivers = sorted(df["driver_name"].unique())
    c1, c2 = st.columns(2)
    d1 = c1.selectbox("Driver A", all_drivers, index=all_drivers.index("Lewis Hamilton") if "Lewis Hamilton" in all_drivers else 0)
    d2 = c2.selectbox("Driver B", all_drivers, index=all_drivers.index("Max Verstappen") if "Max Verstappen" in all_drivers else 1)

    def driver_summary(name):
        g = df[df["driver_name"] == name]
        career_points = g.groupby("year")["points_driver_champ"].max().sum()
        return dict(
            races=len(g), wins=int(g["is_win"].sum()), podiums=int(g["is_podium"].sum()),
            points=career_points, avg_grid=g["grid"].mean(),
            win_rate=g["is_win"].mean() * 100, podium_rate=g["is_podium"].mean() * 100,
        )

    s1, s2 = driver_summary(d1), driver_summary(d2)

    cols = st.columns(2)
    for col, name, s in zip(cols, [d1, d2], [s1, s2]):
        with col:
            st.markdown(f"### {name}")
            mc1, mc2 = st.columns(2)
            metric_card("Races", s["races"], mc1)
            metric_card("Wins", s["wins"], mc2)
            mc3, mc4 = st.columns(2)
            metric_card("Podiums", s["podiums"], mc3)
            metric_card("Total points", f"{s['points']:.0f}", mc4)

    categories = ["Win rate %", "Podium rate %", "Avg. grid (inverted)", "Points/race"]
    def radar_vals(s):
        return [s["win_rate"], s["podium_rate"], max(0, 21 - s["avg_grid"]) * 5, s["points"] / max(s["races"], 1) * 4]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=radar_vals(s1), theta=categories, fill="toself", name=d1, line_color="#E10600"))
    fig.add_trace(go.Scatterpolar(r=radar_vals(s2), theta=categories, fill="toself", name=d2, line_color="#3B82F6"))
    fig.update_layout(template=PLOTLY_TEMPLATE, height=480, polar=dict(radialaxis=dict(visible=True)))
    st.plotly_chart(fig, width="stretch")

    st.markdown("### Points per season")
    comp = df[df["driver_name"].isin([d1, d2])].groupby(["year", "driver_name"])["points_driver_champ"].max().reset_index()
    fig2 = px.line(
        comp, x="year", y="points_driver_champ", color="driver_name", markers=True,
        template=PLOTLY_TEMPLATE, color_discrete_map={d1: "#E10600", d2: "#3B82F6"},
    )
    fig2.update_layout(height=420, yaxis_title="Points that season", xaxis_title="Year")
    st.plotly_chart(fig2, width="stretch")


st.markdown(
    "<div class='footer-note'>Historical data: 2000-2024 race results "
    "(Ergast-schema). Built with Streamlit &amp; Plotly.</div>",
    unsafe_allow_html=True,
)
