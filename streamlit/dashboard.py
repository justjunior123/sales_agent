"""
Streamlit dashboard for call metrics and analytics.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.data.db import get_call_logs, get_call_stats

# Import test core for demo controls
from tests.test_core import populate_database, clear_database


# Page configuration
st.set_page_config(
    page_title="Carrier Sales Dashboard",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Custom CSS for better styling
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .big-number {
        font-size: 36px;
        font-weight: bold;
        color: #1f77b4;
    }
    </style>
""", unsafe_allow_html=True)


def main():
    st.title("📞 Inbound Carrier Sales Dashboard")
    st.markdown("### Real-time analytics for HappyRobot AI Agent")

    # Sidebar filters
    st.sidebar.header("Filters")

    # Date range filter
    date_filter = st.sidebar.radio(
        "Time Period",
        ["Last 7 Days", "Last 30 Days", "All Time"]
    )

    # Outcome filter
    outcome_filter = st.sidebar.multiselect(
        "Call Outcome",
        ["booked", "negotiated", "rejected"],
        default=["booked", "negotiated", "rejected"]
    )

    # Demo Controls Section
    st.sidebar.markdown("---")
    st.sidebar.header("🎬 Demo Controls")
    st.sidebar.caption("For demonstration purposes only")

    col1, col2 = st.sidebar.columns(2)

    with col1:
        if st.button("📊 Load", use_container_width=True, key="load_data", help="Load 8 sample calls"):
            with st.spinner("Loading sample data..."):
                success, message = populate_database()

            if success:
                st.success(f"✅ {message}")
                st.info("🔄 Refresh the page or interact with any filter to see updated data")
            else:
                st.error(f"❌ {message}")

    with col2:
        if st.button("🗑️ Clear", use_container_width=True, key="clear_data", help="Clear all calls"):
            with st.spinner("Clearing database..."):
                success, message = clear_database()

            if success:
                st.success(f"✅ {message}")
                st.info("🔄 Refresh the page or interact with any filter to see updated data")
            else:
                st.error(f"❌ {message}")

    st.sidebar.warning("⚠️ Demo only - not for production")

    # Calculate date range
    if date_filter == "Last 7 Days":
        start_date = (datetime.now() - timedelta(days=7)).isoformat()
    elif date_filter == "Last 30 Days":
        start_date = (datetime.now() - timedelta(days=30)).isoformat()
    else:
        start_date = None

    # Fetch data
    try:
        stats = get_call_stats()
        all_logs = get_call_logs(start_date=start_date, limit=1000)

        # Filter by outcome
        if outcome_filter:
            all_logs = [log for log in all_logs if log["outcome"] in outcome_filter]

        # Convert to DataFrame
        df = pd.DataFrame(all_logs)

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return

    # ==================== Key Metrics Section ====================
    st.header("📊 Key Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_calls = stats["total_calls"]
        st.metric("Total Calls", total_calls)

    with col2:
        booked = stats["outcome_counts"].get("booked", 0)
        booking_rate = (booked / total_calls * 100) if total_calls > 0 else 0
        st.metric("Booked", booked, f"{booking_rate:.1f}%")

    with col3:
        negotiated = stats["outcome_counts"].get("negotiated", 0)
        st.metric("Negotiated", negotiated)

    with col4:
        rejected = stats["outcome_counts"].get("rejected", 0)
        st.metric("Rejected", rejected)

    st.divider()

    # ==================== Outcome & Sentiment Charts ====================
    st.header("📈 Call Distribution")

    col1, col2 = st.columns(2)

    with col1:
        # Outcome pie chart
        if stats["outcome_counts"]:
            outcome_df = pd.DataFrame(
                list(stats["outcome_counts"].items()),
                columns=["Outcome", "Count"]
            )
            fig_outcome = px.pie(
                outcome_df,
                values="Count",
                names="Outcome",
                title="Call Outcomes",
                color="Outcome",
                color_discrete_map={
                    "booked": "#2ecc71",
                    "negotiated": "#f39c12",
                    "rejected": "#e74c3c"
                }
            )
            st.plotly_chart(fig_outcome, use_container_width=True)
        else:
            st.info("No call data available yet")

    with col2:
        # Sentiment pie chart
        if stats["sentiment_counts"]:
            sentiment_df = pd.DataFrame(
                list(stats["sentiment_counts"].items()),
                columns=["Sentiment", "Count"]
            )
            fig_sentiment = px.pie(
                sentiment_df,
                values="Count",
                names="Sentiment",
                title="Call Sentiment",
                color="Sentiment",
                color_discrete_map={
                    "positive": "#2ecc71",
                    "neutral": "#95a5a6",
                    "negative": "#e74c3c"
                }
            )
            st.plotly_chart(fig_sentiment, use_container_width=True)
        else:
            st.info("No sentiment data available yet")

    st.divider()

    # ==================== Pricing Analysis ====================
    st.header("💰 Pricing Analysis")

    col1, col2, col3 = st.columns(3)

    with col1:
        avg_board_rate = stats["averages"].get("avg_loadboard_rate")
        if avg_board_rate:
            st.metric("Avg Board Rate", f"${avg_board_rate:.2f}")
        else:
            st.metric("Avg Board Rate", "N/A")

    with col2:
        avg_agreed_rate = stats["averages"].get("avg_agreed_rate")
        if avg_agreed_rate:
            st.metric("Avg Agreed Rate", f"${avg_agreed_rate:.2f}")
        else:
            st.metric("Avg Agreed Rate", "N/A")

    with col3:
        avg_discount = stats["margin_analysis"].get("avg_discount")
        if avg_discount is not None:
            discount_pct = (avg_discount / avg_board_rate * 100) if avg_board_rate else 0
            st.metric("Avg Discount", f"${avg_discount:.2f}", f"{discount_pct:.1f}%")
        else:
            st.metric("Avg Discount", "N/A")

    # Rate comparison chart
    if not df.empty and "loadboard_rate" in df.columns and "agreed_rate" in df.columns:
        # Filter out null values
        rate_df = df[df["loadboard_rate"].notna() & df["agreed_rate"].notna()].copy()

        if not rate_df.empty:
            rate_df["call_index"] = range(len(rate_df))

            fig_rates = go.Figure()
            fig_rates.add_trace(go.Scatter(
                x=rate_df["call_index"],
                y=rate_df["loadboard_rate"],
                mode='lines+markers',
                name='Board Rate',
                line=dict(color='#3498db', width=2)
            ))
            fig_rates.add_trace(go.Scatter(
                x=rate_df["call_index"],
                y=rate_df["agreed_rate"],
                mode='lines+markers',
                name='Agreed Rate',
                line=dict(color='#2ecc71', width=2)
            ))
            fig_rates.update_layout(
                title="Board Rate vs Agreed Rate by Call",
                xaxis_title="Call Number",
                yaxis_title="Rate ($)",
                hovermode='x unified'
            )
            st.plotly_chart(fig_rates, use_container_width=True)

    st.divider()

    # ==================== Recent Calls Table ====================
    st.header("📋 Recent Call Logs")

    if not df.empty:
        # Format the dataframe for display
        display_df = df[[
            "call_id", "carrier_mc", "carrier_name", "timestamp",
            "load_id", "loadboard_rate", "agreed_rate",
            "negotiation_rounds", "outcome", "sentiment"
        ]].copy()

        # Format timestamp
        display_df["timestamp"] = pd.to_datetime(display_df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M")

        # Format rates
        display_df["loadboard_rate"] = display_df["loadboard_rate"].apply(
            lambda x: f"${x:.2f}" if pd.notna(x) else "N/A"
        )
        display_df["agreed_rate"] = display_df["agreed_rate"].apply(
            lambda x: f"${x:.2f}" if pd.notna(x) else "N/A"
        )

        # Color code outcomes
        def highlight_outcome(row):
            if row["outcome"] == "booked":
                return ["background-color: #d5f4e6"] * len(row)
            elif row["outcome"] == "rejected":
                return ["background-color: #fadbd8"] * len(row)
            else:
                return [""] * len(row)

        styled_df = display_df.style.apply(highlight_outcome, axis=1)

        st.dataframe(styled_df, use_container_width=True)

        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download Call Logs (CSV)",
            data=csv,
            file_name=f"call_logs_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No call logs available for the selected filters")

    # ==================== Additional Metrics ====================
    st.divider()
    st.header("⏱️ Performance Metrics")

    col1, col2 = st.columns(2)

    with col1:
        avg_negotiation = stats["averages"].get("avg_negotiation_rounds")
        if avg_negotiation:
            st.metric("Avg Negotiation Rounds", f"{avg_negotiation:.1f}")
        else:
            st.metric("Avg Negotiation Rounds", "N/A")

    with col2:
        avg_duration = stats["averages"].get("avg_call_duration")
        if avg_duration:
            minutes = int(avg_duration // 60)
            seconds = int(avg_duration % 60)
            st.metric("Avg Call Duration", f"{minutes}m {seconds}s")
        else:
            st.metric("Avg Call Duration", "N/A")


if __name__ == "__main__":
    main()
