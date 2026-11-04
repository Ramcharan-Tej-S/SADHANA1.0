# utils/charts.py — ExamFlow AI Plotly Visualizations
import plotly.graph_objects as go
import plotly.express as px

# ─── Shared Layout ────────────────────────────────────────────────────
DARK_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#E8EAED", size=12),
    margin=dict(l=20, r=20, t=40, b=20),
    xaxis=dict(gridcolor="rgba(45,49,67,0.5)", zerolinecolor="#2D3143"),
    yaxis=dict(gridcolor="rgba(45,49,67,0.5)", zerolinecolor="#2D3143"),
)

DEFAULT_LEGEND = dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#9AA0A6"))

COLORS_PALETTE = ["#6C63FF", "#00D9FF", "#00E676", "#FFB740", "#FF5252", "#BB86FC", "#64FFDA", "#FF80AB"]


def render_readiness_gauge(score: float, title: str = "Readiness Score"):
    """Circular gauge for readiness score (0-100)."""
    color = "#00E676" if score >= 70 else "#FFB740" if score >= 40 else "#FF5252"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number=dict(suffix="%", font=dict(size=36, color=color)),
        title=dict(text=title, font=dict(size=14, color="#9AA0A6")),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor="#2D3143", tickwidth=1),
            bar=dict(color=color, thickness=0.3),
            bgcolor="#1C2035",
            borderwidth=0,
            steps=[
                dict(range=[0, 40], color="rgba(255,82,82,0.1)"),
                dict(range=[40, 70], color="rgba(255,183,64,0.1)"),
                dict(range=[70, 100], color="rgba(0,230,118,0.1)"),
            ],
            threshold=dict(
                line=dict(color=color, width=3),
                thickness=0.8,
                value=score,
            ),
        ),
    ))
    fig.update_layout(**DARK_LAYOUT, height=250, showlegend=False)
    return fig


def render_difficulty_radar(subjects: list, scores: list):
    """Radar chart for topic difficulty spread across subjects."""
    fig = go.Figure(go.Scatterpolar(
        r=scores + [scores[0]],
        theta=subjects + [subjects[0]],
        fill="toself",
        fillcolor="rgba(108,99,255,0.15)",
        line=dict(color="#6C63FF", width=2),
        marker=dict(size=6, color="#00D9FF"),
    ))
    fig.update_layout(
        **DARK_LAYOUT,
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 10], gridcolor="rgba(45,49,67,0.5)", tickfont=dict(color="#9AA0A6")),
            angularaxis=dict(gridcolor="rgba(45,49,67,0.3)", tickfont=dict(color="#E8EAED")),
        ),
        height=350,
        showlegend=False,
    )
    return fig


def render_schedule_timeline(sessions: list):
    """Gantt-like horizontal bar chart for study schedule.
    sessions: list of dicts with {subject, topic, date, start, duration_min}
    """
    if not sessions:
        return _empty_chart("No study sessions yet")

    import pandas as pd
    from datetime import datetime, timedelta

    data = []
    for s in sessions:
        try:
            start_dt = datetime.strptime(f"{s['session_date']} {s['start_time']}", "%Y-%m-%d %H:%M")
        except (ValueError, KeyError):
            continue
        end_dt = start_dt + timedelta(minutes=s.get("duration_min", 60))
        data.append(dict(
            Subject=s.get("subject_name", "Unknown"),
            Topic=s.get("topic_name", ""),
            Start=start_dt,
            End=end_dt,
            Priority=s.get("priority", "medium"),
        ))

    if not data:
        return _empty_chart("No valid sessions to display")

    df = pd.DataFrame(data)
    fig = px.timeline(df, x_start="Start", x_end="End", y="Subject", color="Priority",
                      hover_data=["Topic"],
                      color_discrete_map={"high": "#FF5252", "medium": "#FFB740", "low": "#00E676"})

    fig.update_layout(**DARK_LAYOUT, height=max(200, len(df["Subject"].unique()) * 60 + 80),
                      xaxis_title="", yaxis_title="",
                      legend=dict(**DEFAULT_LEGEND))
    return fig


def render_performance_bars(subjects: list, expected: list, actual: list):
    """Grouped bar chart: expected vs actual scores."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Expected", x=subjects, y=expected,
        marker_color="#6C63FF", marker_line=dict(width=0),
        opacity=0.8,
    ))
    fig.add_trace(go.Bar(
        name="Actual", x=subjects, y=actual,
        marker_color="#00D9FF", marker_line=dict(width=0),
        opacity=0.8,
    ))
    fig.update_layout(
        **DARK_LAYOUT, barmode="group", height=350,
        xaxis_title="", yaxis_title="Score",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def render_coverage_pie(covered: float, remaining: float):
    """Donut chart for syllabus coverage."""
    fig = go.Figure(go.Pie(
        labels=["Covered", "Remaining"],
        values=[covered, remaining],
        hole=0.65,
        marker=dict(colors=["#00E676", "#2D3143"], line=dict(width=0)),
        textinfo="percent",
        textfont=dict(color="#E8EAED", size=13),
        hovertemplate="<b>%{label}</b><br>%{value} topics<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(**DARK_LAYOUT, height=280, showlegend=True,
                      legend=dict(**DEFAULT_LEGEND),
                      annotations=[dict(text=f"{covered/(covered+remaining)*100:.0f}%" if (covered+remaining) > 0 else "0%",
                                       x=0.5, y=0.5, font=dict(size=24, color="#00E676"), showarrow=False)])
    return fig


def render_trend_line(dates: list, scores: list, title: str = "Readiness Trend"):
    """Line chart for readiness score over time."""
    fig = go.Figure(go.Scatter(
        x=dates, y=scores,
        mode="lines+markers",
        line=dict(color="#6C63FF", width=3, shape="spline"),
        marker=dict(size=8, color="#00D9FF", line=dict(width=2, color="#6C63FF")),
        fill="tozeroy",
        fillcolor="rgba(108,99,255,0.1)",
    ))
    fig.update_layout(
        **DARK_LAYOUT, height=300,
        title=dict(text=title, font=dict(size=14, color="#9AA0A6")),
        xaxis_title="", yaxis_title="Score",
        yaxis=dict(range=[0, 105], gridcolor="rgba(45,49,67,0.5)"),
    )
    return fig


def render_difficulty_distribution(easy: int, medium: int, hard: int):
    """Horizontal stacked bar for difficulty distribution."""
    total = easy + medium + hard
    if total == 0:
        return _empty_chart("No topics assessed yet")

    fig = go.Figure()
    fig.add_trace(go.Bar(y=["Topics"], x=[easy], name="Easy",
                         orientation="h", marker_color="#00E676", opacity=0.85))
    fig.add_trace(go.Bar(y=["Topics"], x=[medium], name="Medium",
                         orientation="h", marker_color="#FFB740", opacity=0.85))
    fig.add_trace(go.Bar(y=["Topics"], x=[hard], name="Hard",
                         orientation="h", marker_color="#FF5252", opacity=0.85))

    fig.update_layout(**DARK_LAYOUT, barmode="stack", height=120,
                      xaxis_title="", yaxis_title="", showlegend=True,
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    return fig


def render_subject_radar(subjects: list, readiness: list):
    """Radar chart for overall subject readiness."""
    fig = go.Figure(go.Scatterpolar(
        r=readiness + [readiness[0]],
        theta=subjects + [subjects[0]],
        fill="toself",
        fillcolor="rgba(0,230,118,0.12)",
        line=dict(color="#00E676", width=2),
        marker=dict(size=6, color="#64FFDA"),
    ))
    fig.update_layout(
        **DARK_LAYOUT,
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(45,49,67,0.5)", tickfont=dict(color="#9AA0A6")),
            angularaxis=dict(gridcolor="rgba(45,49,67,0.3)", tickfont=dict(color="#E8EAED")),
        ),
        height=350,
        showlegend=False,
    )
    return fig


def _empty_chart(message: str = "No data available"):
    """Return an empty chart with a message."""
    fig = go.Figure()
    fig.update_layout(
        **DARK_LAYOUT, height=200,
        annotations=[dict(text=message, x=0.5, y=0.5,
                         xref="paper", yref="paper",
                         font=dict(size=14, color="#9AA0A6"),
                         showarrow=False)],
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig
