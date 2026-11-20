import plotly.graph_objects as go
from typing import List, Dict, Any


DARK_LAYOUT = dict(
    paper_bgcolor="#161b22",
    plot_bgcolor="#161b22",
    font=dict(color="#c9d1d9", family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto"),
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(
        gridcolor="#21262d",
        zerolinecolor="#30363d",
        showgrid=True,
    ),
    yaxis=dict(
        gridcolor="#21262d",
        zerolinecolor="#30363d",
        showgrid=True,
    )
)


def create_weekly_activity_chart(weekly_data: List[Dict[str, Any]]) -> go.Figure:
    """Creates a dark-mode bar chart of completed workouts and minutes for the past 7 days."""
    days = [item["day"] for item in weekly_data]
    workouts = [item["workouts_completed"] for item in weekly_data]
    durations = [item["total_duration_minutes"] for item in weekly_data]

    fig = go.Figure()

    # Bar for duration
    fig.add_trace(
        go.Bar(
            x=days,
            y=durations,
            name="Duration (mins)",
            marker=dict(
                color="#a3e635",
                line=dict(color="#bef264", width=1.5),
                cornerradius=6
            ),
            hovertemplate="<b>%{x}</b><br>Duration: %{y} mins<extra></extra>"
        )
    )

    # Line overlay for workout count
    fig.add_trace(
        go.Scatter(
            x=days,
            y=[w * 30 for w in workouts], # Scaled for secondary visual cue
            mode="lines+markers",
            name="Session Completed",
            line=dict(color="#38bdf8", width=3, dash="dot"),
            marker=dict(size=8, color="#38bdf8"),
            hovertext=[f"{w} workout(s)" for w in workouts],
            hoverinfo="text+x"
        )
    )

    layout = DARK_LAYOUT.copy()
    layout.update(
        title=dict(text="Weekly Workout Activity (Minutes)", font=dict(color="#ffffff", size=14)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=280
    )
    fig.update_layout(layout)
    return fig


def create_macro_donut_chart(protein_g: float, carbs_g: float, fat_g: float) -> go.Figure:
    """Creates a donut chart for consumed macronutrients."""
    # Convert grams to kcal
    p_cals = protein_g * 4
    c_cals = carbs_g * 4
    f_cals = fat_g * 9
    total_cals = p_cals + c_cals + f_cals

    if total_cals == 0:
        labels = ["No Data Yet"]
        values = [1]
        colors = ["#30363d"]
    else:
        labels = ["Protein", "Carbohydrates", "Fats"]
        values = [p_cals, c_cals, f_cals]
        colors = ["#a3e635", "#38bdf8", "#fbbf24"]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.65,
        marker=dict(colors=colors, line=dict(color="#161b22", width=3)),
        textinfo="percent" if total_cals > 0 else "none",
        hovertemplate="<b>%{label}</b>: %{value:.1f} kcal (%{percent})<extra></extra>" if total_cals > 0 else "No meals logged today"
    )])

    layout = DARK_LAYOUT.copy()
    layout.update(
        title=dict(text="Macro Ratio (% Calories)", font=dict(color="#ffffff", size=14)),
        height=260,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        annotations=[
            dict(
                text=f"<b>{int(total_cals)}</b><br><span style='font-size:11px;color:#8b949e;'>kcal</span>",
                x=0.5, y=0.5,
                font_size=16,
                font_color="#ffffff",
                showarrow=False
            )
        ]
    )
    fig.update_layout(layout)
    return fig


def create_weight_trend_chart(records: List[Dict[str, Any]], target_weight: float) -> go.Figure:
    """Creates a weight progress trend line chart with target reference."""
    dates = [r["date"] for r in records]
    weights = [r["weight_kg"] for r in records]

    fig = go.Figure()

    # User Weight Line
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=weights,
            mode="lines+markers",
            name="Weight (kg)",
            line=dict(color="#a3e635", width=3),
            marker=dict(size=8, color="#a3e635", line=dict(color="#ffffff", width=1.5)),
            hovertemplate="<b>%{x}</b><br>Weight: %{y} kg<extra></extra>"
        )
    )

    # Target line if available
    if target_weight and target_weight > 0 and len(dates) > 0:
        fig.add_trace(
            go.Scatter(
                x=[dates[0], dates[-1]],
                y=[target_weight, target_weight],
                mode="lines",
                name=f"Target ({target_weight} kg)",
                line=dict(color="#f43f5e", width=2, dash="dash")
            )
        )

    layout = DARK_LAYOUT.copy()
    layout.update(
        title=dict(text="Body Weight Trajectory (kg)", font=dict(color="#ffffff", size=14)),
        height=320,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_layout(layout)
    return fig


def create_measurements_chart(records: List[Dict[str, Any]]) -> go.Figure:
    """Creates a multi-line chart for body circumferences (chest, waist, arm, thigh)."""
    dates = [r["date"] for r in records]
    chests = [r.get("chest_cm") for r in records]
    waists = [r.get("waist_cm") for r in records]
    arms = [r.get("arm_cm") for r in records]
    thighs = [r.get("thigh_cm") for r in records]

    fig = go.Figure()

    if any(c is not None for c in chests):
        fig.add_trace(go.Scatter(x=dates, y=chests, mode="lines+markers", name="Chest (cm)", line=dict(color="#38bdf8", width=2)))
    if any(w is not None for w in waists):
        fig.add_trace(go.Scatter(x=dates, y=waists, mode="lines+markers", name="Waist (cm)", line=dict(color="#f97316", width=2)))
    if any(a is not None for a in arms):
        fig.add_trace(go.Scatter(x=dates, y=arms, mode="lines+markers", name="Arm (cm)", line=dict(color="#a3e635", width=2)))
    if any(t is not None for t in thighs):
        fig.add_trace(go.Scatter(x=dates, y=thighs, mode="lines+markers", name="Thigh (cm)", line=dict(color="#ec4899", width=2)))

    layout = DARK_LAYOUT.copy()
    layout.update(
        title=dict(text="Body Circumferences (cm)", font=dict(color="#ffffff", size=14)),
        height=320,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_layout(layout)
    return fig
