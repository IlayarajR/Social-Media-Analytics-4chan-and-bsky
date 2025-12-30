import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
sys.path.append('utils')
from db_utils import load_bsky_data, load_4chan_data, get_latest_stats

# Page config
st.set_page_config(
    page_title="Sports Social Media Dashboard",
    page_icon="📊",
    layout="wide"
)

# Title and description
st.title("📊 Sports Social Media Analytics Dashboard")
st.markdown("Interactive analysis of 4chan (/sp/, /pol/) and Bluesky sports discussions")

# Sidebar - Live Stats
st.sidebar.header("📡 Live Database Stats")

try:
    stats = get_latest_stats()
    st.sidebar.metric("Bluesky Posts", f"{stats['bsky']:,}")
    st.sidebar.metric("/sp/ Posts", f"{stats['sp']:,}")
    st.sidebar.metric("/pol/ Posts", f"{stats['pol']:,}")
    
    if stats['latest_update']:
        time_ago = datetime.now(stats['latest_update'].tzinfo) - stats['latest_update']
        minutes_ago = int(time_ago.total_seconds() / 60)
        st.sidebar.success(f"✅ Last update: {minutes_ago} min ago")
except Exception as e:
    st.sidebar.error("⚠️ Database connection issue")

st.sidebar.markdown("---")
st.sidebar.info("💡 Data updates live from PostgreSQL crawler")

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🏈 Event Spike Analyzer",
    "📸 Media vs Text Engagement", 
    "🏆 Sports Topic Explorer",
    "☣️ Toxicity Deep Dive"
])

with tab1:
    st.header("Event Spike Analyzer")
    st.info("🚧 Feature 1: Coming soon - Analyze posting patterns around sporting events")
    
with tab2:
    st.header("Media Engagement Comparator")
    st.info("🚧 Feature 2: Coming soon - Compare engagement for media vs text-only posts")
    
with tab3:
    st.header("Sports Topic Explorer")
    st.info("🚧 Feature 3: Coming soon - Discover trending sports topics")
    
with tab4:
    st.header("Toxicity Deep Dive")
    st.info("🚧 Feature 4: Coming soon - Explore toxicity patterns")

# Footer
st.markdown("---")
st.caption("CS515 Project 3 - Ilayaraj Rajmohan & Sanjitha Praveen | Binghamton University")
