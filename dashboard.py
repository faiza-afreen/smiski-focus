
import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import random
import time

from pathlib import Path
from datetime import datetime, timedelta
from database import init_db


# ==========================================
# PAGE SETTINGS
# ==========================================

st.set_page_config(
    page_title="Smiski Focus Analytics",
    page_icon="🌱",
    layout="wide"
)

BASE_DIR = Path(__file__).parent
DB_FILE = BASE_DIR / "smiski.db"

init_db()

GREEN = "#83A96F"
DARK_GREEN = "#47663D"
LIGHT_GREEN = "#CDE1B9"


# ==========================================
# CUSTOM DESIGN
# ==========================================

st.markdown("""
<style>

.stApp {
    background-color: #F1F5EB;
    color: #34482B;
}

[data-testid="stSidebar"] {
    background-color: #DFEBD4;
}

[data-testid="stMetric"] {
    background-color: #FFFFFF;
    border: 1px solid #D4E3C8;
    padding: 20px;
    border-radius: 18px;
}

[data-testid="stMetricValue"] {
    color: #47663D;
}

[data-testid="stMetricLabel"] {
    color: #34482B !important;
}

h1, h2, h3 {
    color: #34482B !important;
}

.stButton > button {
    background-color: #83A96F;
    color: white;
    border-radius: 12px;
    border: none;
}

</style>
""", unsafe_allow_html=True)


# ==========================================
# DATA CLEANING AND FEATURE ENGINEERING
# ==========================================

def prepare_data(distractions, sessions):

    distractions["timestamp"] = pd.to_datetime(
        distractions["timestamp"],
        errors="coerce"
    )

    sessions["start_time"] = pd.to_datetime(
        sessions["start_time"],
        errors="coerce"
    )

    sessions["end_time"] = pd.to_datetime(
        sessions["end_time"],
        errors="coerce"
    )

    # Remove invalid records
    distractions = distractions.dropna(
        subset=["timestamp"]
    ).copy()

    sessions = sessions.dropna(
        subset=["start_time", "end_time"]
    ).copy()

    # Create additional analysis columns
    distractions["date"] = (
        distractions["timestamp"].dt.date
    )

    distractions["hour"] = (
        distractions["timestamp"].dt.hour
    )

    distractions["weekday"] = (
        distractions["timestamp"].dt.day_name()
    )

    sessions["date"] = (
        sessions["start_time"].dt.date
    )

    sessions["hour"] = (
        sessions["start_time"].dt.hour
    )

    sessions["hours"] = (
        sessions["duration_minutes"] / 60
    )

    sessions["status"] = sessions["completed"].map({
        1: "Completed",
        0: "Unfinished"
    })

    return distractions, sessions


# ==========================================
# LOAD REAL DATA FROM SQLITE
# ==========================================

def load_data():

    with sqlite3.connect(DB_FILE, timeout=10) as conn:

        distractions = pd.read_sql_query(
            "SELECT * FROM distractions",
            conn
        )

        sessions = pd.read_sql_query(
            "SELECT * FROM study_sessions",
            conn
        )

    return prepare_data(distractions, sessions)


# ==========================================
# GENERATE SYNTHETIC DEMO DATA
# ==========================================

def generate_demo_data():

    rng = random.Random(42)

    demo_distractions = []
    demo_sessions = []

    today = datetime.now().date()

    session_id = 1
    distraction_id = 1

    # Generate 30 complete days of sample data
    for days_ago in range(30, 0, -1):

        day = today - timedelta(days=days_ago)

        number_of_sessions = rng.randint(1, 5)

        daily_sessions = []

        for i in range(number_of_sessions):

            start = datetime.combine(
                day,
                datetime.min.time()
            ) + timedelta(
                hours=9 + i * 3,
                minutes=rng.randint(0, 30)
            )

            completed = rng.random() < 0.85

            if completed:

                duration = rng.choice(
                    [25, 30, 45, 50, 60]
                )

            else:

                duration = rng.randint(5, 24)

            end = start + timedelta(minutes=duration)

            blocks = rng.choices(
                [0, 1, 2, 3],
                weights=[50, 30, 15, 5]
            )[0]

            demo_sessions.append({
                "id": session_id,
                "start_time": start,
                "end_time": end,
                "duration_minutes": duration,
                "completed": int(completed),
                "distractions": blocks
            })

            daily_sessions.append((start, end))

            session_id += 1

            # Generate blocking events during focus
            for j in range(blocks):

                timestamp = start + timedelta(
                    minutes=rng.randint(0, duration - 1)
                )

                demo_distractions.append({
                    "id": distraction_id,
                    "website": "Instagram",
                    "timestamp": timestamp
                })

                distraction_id += 1

        # Generate additional blocks outside focus sessions

        for j in range(rng.randint(0, 3)):

            while True:

                timestamp = datetime.combine(
                    day,
                    datetime.min.time()
                ) + timedelta(
                    hours=rng.randint(10, 22),
                    minutes=rng.randint(0, 59)
                )

                inside_session = any(
                    start <= timestamp < end
                    for start, end in daily_sessions
                )

                if not inside_session:
                    break

            demo_distractions.append({
                "id": distraction_id,
                "website": "Instagram",
                "timestamp": timestamp
            })

            distraction_id += 1

    distractions = pd.DataFrame(demo_distractions)
    sessions = pd.DataFrame(demo_sessions)

    return prepare_data(distractions, sessions)


# ==========================================
# DASHBOARD HEADER
# ==========================================

left, right = st.columns([5, 1])

with left:

    st.title("🌱 Smiski Focus Analytics")

    st.write(
        "Your little companion for better study habits."
    )

with right:

    image_path = BASE_DIR / "work.png"

    if image_path.exists():

        st.image(
            str(image_path),
            width=110
        )


# ==========================================
# SIDEBAR SETTINGS
# ==========================================

st.sidebar.title("🌿 Dashboard Settings")

demo_mode = st.sidebar.toggle(
    "Demo Mode",
    value=False,
    help=(
        "Display synthetic sample data instead "
        "of your personal study records."
    )
)

if demo_mode:

    distractions, sessions = generate_demo_data()

    st.sidebar.success("Demo Mode Active")

    st.sidebar.caption(
        "Viewing 30 days of synthetic sample data."
    )

    st.info(
        "🌱 DEMO MODE — All statistics and charts "
        "display synthetic sample data. "
        "Your personal study records are unchanged."
    )

else:

    distractions, sessions = load_data()

today = datetime.now().date()

if demo_mode:
    today -= timedelta(days=1)


# ==========================================
# DATE RANGE FILTER
# ==========================================

all_dates = (
    distractions["date"].tolist()
    + sessions["date"].tolist()
)

earliest = min(all_dates) if all_dates else today

period = st.sidebar.selectbox(
    "Select time period",
    [
        "Today",
        "Last 7 Days",
        "Last 30 Days",
        "All Time",
        "Custom Range"
    ],
    index=2 if demo_mode else 1,
    key="demo_period" if demo_mode else "real_period"
)

if period == "Today":

    start_date = today
    end_date = today

elif period == "Last 7 Days":

    start_date = today - timedelta(days=6)
    end_date = today

elif period == "Last 30 Days":

    start_date = today - timedelta(days=29)
    end_date = today

elif period == "All Time":

    start_date = min(earliest, today)
    end_date = today

else:

    selected_dates = st.sidebar.date_input(
        "Choose date range",
        value=(today - timedelta(days=6), today),
        key="demo_dates" if demo_mode else "real_dates"
    )

    if len(selected_dates) != 2:

        st.info("Please select a start and end date.")
        st.stop()

    start_date, end_date = selected_dates


# ==========================================
# AUTOMATIC REFRESH
# ==========================================

auto_refresh = st.sidebar.checkbox(
    "Auto-refresh every 10 seconds",
    value=False,
    disabled=demo_mode
)

if st.sidebar.button("🔄 Refresh Data"):

    st.rerun()

if demo_mode:

    st.sidebar.caption(
        "Auto-refresh is disabled in Demo Mode."
    )


# ==========================================
# FILTER DATA
# ==========================================

filtered_distractions = distractions[
    (distractions["date"] >= start_date)
    &
    (distractions["date"] <= end_date)
].copy()

filtered_sessions = sessions[
    (sessions["date"] >= start_date)
    &
    (sessions["date"] <= end_date)
].copy()


# ==========================================
# CALCULATE STATISTICS
# ==========================================

total_minutes = filtered_sessions[
    "duration_minutes"
].sum()

total_hours = total_minutes / 60

total_blocks = len(filtered_distractions)

total_sessions = len(filtered_sessions)

completed_sessions = int(
    filtered_sessions["completed"].sum()
)

unfinished_sessions = (
    total_sessions - completed_sessions
)

completion_rate = (
    completed_sessions / total_sessions * 100
    if total_sessions > 0 else 0
)

average_session = (
    total_minutes / total_sessions
    if total_sessions > 0 else 0
)

session_distractions = int(
    filtered_sessions["distractions"].sum()
)


# ==========================================
# DISPLAY SELECTED TIME PERIOD
# ==========================================

st.caption(
    f"Showing records from {start_date} to {end_date}"
)


# ==========================================
# MAIN STATISTICS
# ==========================================

st.subheader("Your Focus Overview")

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Total Focus Time",
    f"{total_hours:.2f} hrs"
)

c2.metric(
    "Instagram Blocks",
    total_blocks
)

c3.metric(
    "Completed Sessions",
    completed_sessions
)

c4.metric(
    "Completion Rate",
    f"{completion_rate:.1f}%"
    if total_sessions else "—"
)


# ==========================================
# ADDITIONAL STATISTICS
# ==========================================

c5, c6, c7 = st.columns(3)

c5.metric(
    "Average Session",
    f"{average_session:.1f} min"
)

c6.metric(
    "Unfinished Sessions",
    unfinished_sessions
)

c7.metric(
    "Blocks During Focus",
    session_distractions
)


# ==========================================
# PLOTLY CHART STYLING
# ==========================================

def style_chart(fig):

    fig.update_layout(

        paper_bgcolor="rgba(0,0,0,0)",

        plot_bgcolor="rgba(0,0,0,0)",

        font=dict(
            color=DARK_GREEN,
            size=12
        ),

        legend=dict(
            font=dict(color=DARK_GREEN)
        ),

        margin=dict(
            l=20,
            r=20,
            t=35,
            b=20
        )
    )

    fig.update_xaxes(
        gridcolor="#DDE8D5",
        tickfont=dict(color=DARK_GREEN),
        title_font=dict(color=DARK_GREEN)
    )

    fig.update_yaxes(
        gridcolor="#DDE8D5",
        tickfont=dict(color=DARK_GREEN),
        title_font=dict(color=DARK_GREEN)
    )

    return fig


# ==========================================
# CREATE DAILY DATE RANGE
# ==========================================

dates = pd.date_range(
    start=start_date,
    end=end_date
).date

st.divider()


# ==========================================
# DAILY FOCUS TIME
# ==========================================

col1, col2 = st.columns(2)

with col1:

    st.subheader("📚 Daily Focus Time")

    daily_focus = (
        filtered_sessions
        .groupby("date")["duration_minutes"]
        .sum()
        .reindex(dates, fill_value=0)
        .rename_axis("date")
        .reset_index()
    )

    fig = px.bar(
        daily_focus,
        x="date",
        y="duration_minutes",
        labels={
            "date": "Date",
            "duration_minutes": "Focus Minutes"
        },
        color_discrete_sequence=[GREEN]
    )

    fig.update_traces(
        marker_line_width=0
    )

    st.plotly_chart(
        style_chart(fig),
        use_container_width=True
    )


# ==========================================
# DISTRACTION TRENDS
# ==========================================

with col2:

    st.subheader("📵 Distraction Trends")

    daily_blocks = (
        filtered_distractions
        .groupby("date")
        .size()
        .reindex(dates, fill_value=0)
        .rename("blocks")
        .rename_axis("date")
        .reset_index()
    )

    fig = px.line(
        daily_blocks,
        x="date",
        y="blocks",
        markers=True,
        labels={
            "date": "Date",
            "blocks": "Instagram Blocks"
        },
        color_discrete_sequence=[DARK_GREEN]
    )

    fig.update_traces(
        line_width=3
    )

    st.plotly_chart(
        style_chart(fig),
        use_container_width=True
    )


# ==========================================
# SESSION COMPLETION
# ==========================================

col3, col4 = st.columns(2)

with col3:

    st.subheader("🎯 Session Completion")

    if total_sessions == 0:

        st.info("No focus sessions recorded yet.")

    else:

        completion_data = pd.DataFrame({
            "Status": [
                "Completed",
                "Unfinished"
            ],
            "Sessions": [
                completed_sessions,
                unfinished_sessions
            ]
        })

        fig = px.pie(
            completion_data,
            names="Status",
            values="Sessions",
            hole=0.65,
            color="Status",
            color_discrete_map={
                "Completed": GREEN,
                "Unfinished": LIGHT_GREEN
            }
        )

        st.plotly_chart(
            style_chart(fig),
            use_container_width=True
        )


# ==========================================
# DISTRACTIONS BY HOUR
# ==========================================

with col4:

    st.subheader("🕒 Distractions by Hour")

    hourly_blocks = (
        filtered_distractions
        .groupby("hour")
        .size()
        .reindex(range(24), fill_value=0)
        .rename("blocks")
        .rename_axis("hour")
        .reset_index()
    )

    hourly_blocks["time"] = (
        hourly_blocks["hour"].apply(
            lambda h: datetime.strptime(
                str(h), "%H"
            ).strftime("%I %p").lstrip("0")
        )
    )

    fig = px.bar(
        hourly_blocks,
        x="time",
        y="blocks",
        labels={
            "time": "Time of Day",
            "blocks": "Instagram Blocks"
        },
        color_discrete_sequence=[GREEN]
    )

    st.plotly_chart(
        style_chart(fig),
        use_container_width=True
    )


# ==========================================
# WEEKLY DISTRACTION HEATMAP
# ==========================================

st.subheader("🗓️ Weekly Distraction Heatmap")

weekdays = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]

heatmap_data = pd.crosstab(
    filtered_distractions["weekday"],
    filtered_distractions["hour"]
)

heatmap_data = heatmap_data.reindex(
    index=weekdays,
    columns=range(24),
    fill_value=0
)

fig = px.imshow(
    heatmap_data,
    labels={
        "x": "Hour of Day",
        "y": "Day of Week",
        "color": "Blocks"
    },
    color_continuous_scale=[
        "#F1F5EB",
        "#CDE1B9",
        "#83A96F",
        "#47663D"
    ],
    aspect="auto",
    text_auto=True
)

st.plotly_chart(
    style_chart(fig),
    use_container_width=True
)


# ==========================================
# SEVEN-DAY MOVING AVERAGE
# ==========================================

st.divider()

st.subheader("📈 Focus Time Moving Average")

rolling_focus = daily_focus.copy()

rolling_focus["7_day_average"] = (
    rolling_focus["duration_minutes"]
    .rolling(window=7, min_periods=7)
    .mean()
)

if len(rolling_focus) >= 7:

    fig = px.line(
        rolling_focus,
        x="date",
        y=[
            "duration_minutes",
            "7_day_average"
        ],
        labels={
            "date": "Date",
            "value": "Focus Minutes",
            "variable": "Metric"
        },
        color_discrete_sequence=[
            LIGHT_GREEN,
            DARK_GREEN
        ]
    )

    fig.for_each_trace(
        lambda trace: trace.update(
            name={
                "duration_minutes": "Daily Focus",
                "7_day_average": "7-Day Average"
            }.get(trace.name, trace.name)
        )
    )

    fig.update_traces(line_width=3)

    st.plotly_chart(
        style_chart(fig),
        use_container_width=True
    )

    st.caption(
        "The moving average smooths daily fluctuations "
        "and helps reveal longer-term focus time trends."
    )

else:

    st.info(
        "Select at least seven days to display "
        "the seven-day moving average."
    )


# ==========================================
# FOCUS TIME BY HOUR
# ==========================================

st.subheader("⏰ Focus Time by Starting Hour")

hourly_focus = (
    filtered_sessions
    .groupby("hour")["duration_minutes"]
    .sum()
    .reindex(range(24), fill_value=0)
    .rename_axis("hour")
    .reset_index()
)

hourly_focus["time"] = (
    hourly_focus["hour"].apply(
        lambda h: datetime.strptime(
            str(h), "%H"
        ).strftime("%I %p").lstrip("0")
    )
)

fig = px.bar(
    hourly_focus,
    x="time",
    y="duration_minutes",
    labels={
        "time": "Session Starting Hour",
        "duration_minutes": "Focus Minutes"
    },
    color_discrete_sequence=[GREEN]
)

st.plotly_chart(
    style_chart(fig),
    use_container_width=True
)

st.caption(
    "Session duration is attributed to the hour "
    "in which the timer started."
)


# ==========================================
# DISTRACTIONS VS SESSION COMPLETION
# ==========================================

st.subheader("🔍 Distractions and Session Completion")

if total_sessions > 0:

    completion_analysis = (
        filtered_sessions
        .groupby("status")
        .agg(
            average_distractions=("distractions", "mean"),
            session_count=("id", "count")
        )
        .reset_index()
    )

    fig = px.bar(
        completion_analysis,
        x="status",
        y="average_distractions",
        color="status",
        text_auto=".2f",
        hover_data=["session_count"],
        labels={
            "status": "Session Status",
            "average_distractions": "Average Blocks",
            "session_count": "Number of Sessions"
        },
        color_discrete_map={
            "Completed": GREEN,
            "Unfinished": LIGHT_GREEN
        }
    )

    fig.update_layout(
        showlegend=False
    )

    st.plotly_chart(
        style_chart(fig),
        use_container_width=True
    )

    st.caption(
        "This comparison explores the relationship "
        "between recorded distractions and session "
        "completion. It does not establish causation."
    )

else:

    st.info("No study sessions available for comparison.")


# ==========================================
# AUTOMATIC INSIGHTS
# ==========================================

st.divider()

st.subheader("💡 Your Focus Insights")

if total_blocks == 0 and total_sessions == 0:

    st.info(
        "Start using your Smiski focus timer "
        "to discover your study patterns!"
    )

else:

    if total_blocks > 0:

        peak_hour = int(
            filtered_distractions["hour"]
            .value_counts()
            .idxmax()
        )

        peak_time = datetime.strptime(
            str(peak_hour), "%H"
        ).strftime("%I %p").lstrip("0")

        peak_day = (
            filtered_distractions["weekday"]
            .value_counts()
            .idxmax()
        )

        st.info(
            f"The highest recorded number of Instagram "
            f"blocks occurs around {peak_time}."
        )

        st.info(
            f"{peak_day} has the most recorded "
            f"Instagram blocks in this date range."
        )

    if total_sessions > 0:

        st.info(
            f"The average focus session lasts "
            f"{average_session:.1f} minutes."
        )

        st.info(
            f"{completed_sessions} out of "
            f"{total_sessions} recorded focus "
            f"sessions were completed."
        )

        focus_by_hour = (
            filtered_sessions
            .groupby("hour")["duration_minutes"]
            .sum()
        )

        if focus_by_hour.sum() > 0:

            best_hour = int(
                focus_by_hour.idxmax()
            )

            best_time = datetime.strptime(
                str(best_hour), "%H"
            ).strftime("%I %p").lstrip("0")

            st.success(
                f"Sessions starting around {best_time} "
                f"account for the most recorded focus time."
            )


# ==========================================
# STUDY HISTORY
# ==========================================

st.divider()

st.subheader("📖 Your Study History")

if filtered_sessions.empty:

    st.info(
        "No study sessions found for this date range."
    )

else:

    history = filtered_sessions[[
        "start_time",
        "end_time",
        "duration_minutes",
        "status",
        "distractions"
    ]].copy()

    history = history.sort_values(
        "start_time",
        ascending=False
    )

    history.columns = [
        "Started",
        "Ended",
        "Minutes",
        "Status",
        "Distractions"
    ]

    st.dataframe(
        history,
        use_container_width=True,
        hide_index=True
    )


# ==========================================
# DOWNLOAD CSV REPORTS
# ==========================================

st.subheader("📥 Download Your Data")

if demo_mode:

    st.caption(
        "These downloads contain synthetic sample data."
    )

download1, download2 = st.columns(2)

with download1:

    st.download_button(
        label="Download Study Sessions",
        data=filtered_sessions.to_csv(index=False),
        file_name=(
            "demo_study_sessions.csv"
            if demo_mode
            else "smiski_study_sessions.csv"
        ),
        mime="text/csv"
    )

with download2:

    st.download_button(
        label="Download Distraction History",
        data=filtered_distractions.to_csv(index=False),
        file_name=(
            "demo_distractions.csv"
            if demo_mode
            else "smiski_distractions.csv"
        ),
        mime="text/csv"
    )


# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "Focus time represents recorded timer usage. "
    "Instagram blocks represent recorded blocking events, "
    "not every possible distraction."
)

if demo_mode:

    st.caption(
        "Demo Mode uses reproducible synthetic data "
        "generated with a fixed random seed."
    )

st.markdown(
    "<p style='text-align:center;color:#47663D;'>"
    "Made for better study habits 🌱 | Smiski Focus"
    "</p>",
    unsafe_allow_html=True
)


# ==========================================
# OPTIONAL AUTOMATIC REFRESH
# ==========================================

if auto_refresh and not demo_mode:

    time.sleep(10)

    st.rerun()
