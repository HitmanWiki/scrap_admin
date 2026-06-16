"""
Solana Sniper Bot - Professional Admin Dashboard
Streamlit + Neon PostgreSQL - Premium UI Edition
"""

import streamlit as st
import pandas as pd
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="GHOSTwire Admin",
    page_icon="👻",
    layout="wide",
    initial_sidebar_state="expanded"
)
# ============================================
# CUSTOM CSS FOR DARK MODERN THEME
# ============================================
def load_css():
    st.markdown("""
    <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Global Styles */
        .stApp {
            background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 50%, #16213e 100%);
        }
        
        /* Main content area */
        .main .block-container {
            padding: 2rem 3rem;
            background: rgba(10, 10, 26, 0.7);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            border: 1px solid rgba(103, 25, 255, 0.1);
        }
        
        /* Typography */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            background: linear-gradient(135deg, #6719ff, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        h1 {
            font-size: 2.5rem !important;
            margin-bottom: 0.5rem !important;
        }
        
        /* Metric Cards */
        div[data-testid="stMetric"] {
            background: rgba(20, 20, 40, 0.6) !important;
            backdrop-filter: blur(10px) !important;
            border: 1px solid rgba(103, 25, 255, 0.2) !important;
            border-radius: 16px !important;
            padding: 1.5rem !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 20px rgba(103, 25, 255, 0.1) !important;
        }
        
        div[data-testid="stMetric"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 30px rgba(103, 25, 255, 0.3) !important;
            border-color: rgba(103, 25, 255, 0.4) !important;
        }
        
        div[data-testid="stMetric"] label {
            color: #a78bfa !important;
            font-weight: 500 !important;
        }
        
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
            color: #ffffff !important;
            font-weight: 700 !important;
            font-size: 2rem !important;
        }
        
        /* DataFrames */
        .stDataFrame {
            background: rgba(20, 20, 40, 0.6) !important;
            border-radius: 16px !important;
            border: 1px solid rgba(103, 25, 255, 0.2) !important;
            overflow: hidden !important;
        }
        
        .stDataFrame table {
            background: transparent !important;
        }
        
        .stDataFrame th {
            background: rgba(103, 25, 255, 0.2) !important;
            color: #a78bfa !important;
            font-weight: 600 !important;
            padding: 12px 16px !important;
        }
        
        .stDataFrame td {
            background: transparent !important;
            color: #e0e0e0 !important;
            padding: 10px 16px !important;
            border-bottom: 1px solid rgba(103, 25, 255, 0.1) !important;
        }
        
        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #6719ff, #8a4dff) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 12px 24px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 15px rgba(103, 25, 255, 0.3) !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 25px rgba(103, 25, 255, 0.5) !important;
        }
        
        /* Text Inputs */
        .stTextInput > div > div > input {
            background: rgba(20, 20, 40, 0.8) !important;
            border: 1px solid rgba(103, 25, 255, 0.3) !important;
            border-radius: 12px !important;
            color: #ffffff !important;
            padding: 12px 16px !important;
        }
        
        .stTextInput > div > div > input::placeholder {
            color: #6e6e80 !important;
        }
        
        /* Select boxes */
        .stSelectbox > div > div {
            background: rgba(20, 20, 40, 0.8) !important;
            border: 1px solid rgba(103, 25, 255, 0.3) !important;
            border-radius: 12px !important;
        }
        
        /* Number inputs */
        .stNumberInput > div > div > input {
            background: rgba(20, 20, 40, 0.8) !important;
            border: 1px solid rgba(103, 25, 255, 0.3) !important;
            border-radius: 12px !important;
            color: #ffffff !important;
        }
        
        /* Sidebar */
        .css-1d391kg, .css-1lcbmhc, [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0a0a1a 0%, #1a1a2e 100%) !important;
            border-right: 1px solid rgba(103, 25, 255, 0.2) !important;
        }
        
        /* Radio buttons */
        .stRadio > div {
            background: transparent !important;
        }
        
        .stRadio label {
            color: #a78bfa !important;
        }
        
        /* Charts */
        .js-plotly-plot {
            background: transparent !important;
        }
        
        /* Separator */
        hr {
            border-color: rgba(103, 25, 255, 0.2) !important;
        }
        
        /* Info/Success/Error Messages */
        .stAlert {
            background: rgba(20, 20, 40, 0.8) !important;
            border: 1px solid rgba(103, 25, 255, 0.3) !important;
            border-radius: 12px !important;
            color: #ffffff !important;
        }
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(10, 10, 26, 0.5);
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #6719ff, #8a4dff);
            border-radius: 10px;
        }
        
        /* Title animations */
        @keyframes gradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        .title-gradient {
            background: linear-gradient(135deg, #6719ff, #8a4dff, #a78bfa, #6719ff);
            background-size: 400% 400%;
            animation: gradient 6s ease infinite;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        /* Pulse animation for live indicators */
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .live-pulse {
            animation: pulse 2s ease-in-out infinite;
            color: #4ecca3;
        }
        
        /* Slider styling */
        .stSlider > div > div > div {
            background: linear-gradient(135deg, #6719ff, #8a4dff) !important;
        }
    </style>
    """, unsafe_allow_html=True)

# ============================================
# DATABASE CONNECTION
# ============================================
@st.cache_resource
def get_db_connection():
    try:
        # Get database URL from environment variable
        db_url = os.getenv("DATABASE_URL")
        
        if not db_url:
            st.error("DATABASE_URL not found in environment variables")
            return None
        
        conn = psycopg2.connect(
            db_url,
            sslmode='require',
            connect_timeout=10,
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=5
        )
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

def query(sql, params=None):
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params)
        result = cur.fetchall()
        cur.close()
        return result
    except Exception as e:
        st.error(f"Query error: {e}")
        return []

def execute(sql, params=None):
    conn = get_db_connection()
    if conn is None:
        return False
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        st.error(f"Execute error: {e}")
        return False

# ============================================
# AUTHENTICATION
# ============================================
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
                <div style="text-align: center; padding: 60px 0;">
                    <div style="width: 100px; height: 100px; background: linear-gradient(135deg, #6719ff, #8a4dff); 
                         border-radius: 25px; margin: 0 auto; display: flex; align-items: center; justify-content: center;
                         box-shadow: 0 10px 40px rgba(103, 25, 255, 0.5);">
                        <span style="font-size: 50px;">👻</span>
                    </div>
                    <h1 style="margin-top: 30px; font-size: 3rem;" class="title-gradient">GHOSTwire</h1>
                    <p style="color: #a78bfa; margin-bottom: 40px; font-size: 1.1rem;">Professional Admin Dashboard</p>
                </div>
            """, unsafe_allow_html=True)
            
            password = st.text_input("Password", type="password", placeholder="Enter admin password")
            
            if st.button("🚀 Access Dashboard", use_container_width=True):
                # Try to get from secrets, fallback to default
                try:
                    admin_pass = st.secrets["ADMIN_PASSWORD"]
                except:
                    admin_pass = "GhostWire@2026"
                
                if password == admin_pass:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("🔒 Invalid password!")
        
        # Footer
        st.markdown("""
            <div style="text-align: center; margin-top: 40px; color: #6e6e80; font-size: 0.85rem;">
                <p>Protected by GHOSTwire Security 🔐</p>
            </div>
        """, unsafe_allow_html=True)
        return False
    return True

# ============================================
# SIDEBAR
# ============================================
def sidebar():
    with st.sidebar:
        st.markdown("""
            <div style="text-align: center; padding: 20px 0;">
                <div style="width: 60px; height: 60px; background: linear-gradient(135deg, #6719ff, #8a4dff); 
                     border-radius: 18px; margin: 0 auto; display: flex; align-items: center; justify-content: center;
                     box-shadow: 0 8px 25px rgba(103, 25, 255, 0.4);">
                    <span style="font-size: 32px;">👻</span>
                </div>
                <h3 style="margin-top: 15px;" class="title-gradient">GHOSTwire</h3>
                <p style="color: #a78bfa; font-size: 0.8rem; margin-bottom: 5px;">Admin Panel v2.0</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation with icons
        pages = {
            "📊 Dashboard": "Dashboard",
            "👥 Users": "Users",
            "💼 Wallets": "Wallets",
            "📡 Channels": "Channels",
            "📈 Positions": "Positions",
            "💱 Trades": "Trades",
            "🔗 Referrals": "Referrals",
            "💰 Fees": "Fees",
            "✅ Whitelist": "Whitelist",
            "🚫 Blacklist": "Blacklist",
            "🎯 Snipe Logs": "Snipe Logs",
            "🔐 Sessions": "Sessions",
            "⚙️ Settings": "Settings"
        }
        
        selected = st.radio(
            "Navigation",
            list(pages.keys()),
            index=0,
            label_visibility="collapsed"
        )
        
        page = pages[selected]
        
        st.markdown("---")
        
        # Quick stats
        try:
            stats = query("SELECT COUNT(*) as count FROM users WHERE is_active = true")
            if stats:
                st.markdown(f"""
                    <div style="text-align: center; padding: 10px; background: rgba(103, 25, 255, 0.1); 
                         border-radius: 12px; border: 1px solid rgba(103, 25, 255, 0.2);">
                        <p style="color: #a78bfa; margin: 0; font-size: 0.8rem;">Active Users</p>
                        <p style="color: white; margin: 5px 0; font-size: 1.5rem; font-weight: 700;">{stats[0]['count']}</p>
                    </div>
                """, unsafe_allow_html=True)
        except:
            pass
        
        st.markdown("---")
        
        # Time and logout
        st.markdown(f"""
            <div style="text-align: center; color: #6e6e80; font-size: 0.75rem;">
                <p>{datetime.now().strftime('%Y-%m-%d %H:%M')} UTC</p>
                <p style="color: #4ecca3;" class="live-pulse">● System Online</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
        
        return page

# ============================================
# REUSABLE COMPONENTS
# ============================================
def section_header(title, subtitle=None):
    st.markdown(f"""
        <div style="margin-bottom: 30px;">
            <h1 style="margin-bottom: 5px;">{title}</h1>
            {f'<p style="color: #a78bfa; font-size: 1.1rem;">{subtitle}</p>' if subtitle else ''}
        </div>
    """, unsafe_allow_html=True)

def metric_card(title, value, icon, delta=None):
    delta_color = "normal"
    if delta:
        delta_color = "normal"
    st.metric(f"{icon} {title}", value, delta=delta, delta_color=delta_color)

# ============================================
# DASHBOARD PAGE
# ============================================
def dashboard_page():
    section_header("📊 Dashboard", "Real-time analytics and performance metrics")
    
    # Stats row 1
    stats = query("""
        SELECT 
            (SELECT COUNT(*) FROM users WHERE is_active = true) as total_users,
            (SELECT COUNT(*) FROM wallets WHERE is_active = true) as total_wallets,
            (SELECT COUNT(*) FROM positions WHERE is_active = true AND amount > 0) as active_positions,
            (SELECT COUNT(*) FROM channels WHERE is_active = true) as active_channels,
            (SELECT COUNT(*) FROM trade_history WHERE DATE(created_at) = CURRENT_DATE) as today_trades,
            (SELECT COALESCE(SUM(amount::numeric * price::numeric), 0) FROM trade_history WHERE DATE(created_at) = CURRENT_DATE) as today_volume
    """)
    
    if stats:
        s = stats[0]
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            metric_card("Active Users", s.get('total_users', 0), "👥")
        with c2:
            metric_card("Total Wallets", s.get('total_wallets', 0), "💼")
        with c3:
            metric_card("Active Positions", s.get('active_positions', 0), "📈")
        with c4:
            metric_card("Active Channels", s.get('active_channels', 0), "📡")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Stats row 2
    stats2 = query("""
        SELECT 
            (SELECT COUNT(*) FROM trade_history) as total_trades,
            (SELECT COUNT(*) FROM trade_history WHERE trade_type = 'buy') as total_buys,
            (SELECT COUNT(*) FROM trade_history WHERE trade_type IN ('sell', 'auto-sell')) as total_sells,
            (SELECT COUNT(*) FROM referrals WHERE is_active = true) as total_referrals,
            (SELECT COALESCE(SUM(commission::numeric), 0) FROM referral_earnings) as total_commission
    """)
    
    if stats2:
        s = stats2[0]
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            metric_card("Total Trades", s.get('total_trades', 0), "💱")
        with c2:
            metric_card("Total Buys", s.get('total_buys', 0), "🟢")
        with c3:
            metric_card("Total Sells", s.get('total_sells', 0), "🔴")
        with c4:
            metric_card("Referral Earnings", f"{s.get('total_commission', 0):.4f} SOL", "💰")
    
    st.markdown("---")
    
    # Charts with improved styling
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("### 📊 Trading Activity (Last 7 Days)")
        trades = query("""
            SELECT DATE(created_at) as date, 
                   COUNT(CASE WHEN trade_type = 'buy' THEN 1 END) as buys,
                   COUNT(CASE WHEN trade_type IN ('sell', 'auto-sell') THEN 1 END) as sells
            FROM trade_history 
            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
        if trades:
            df = pd.DataFrame(trades)
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df['date'], 
                y=df['buys'], 
                name='Buys', 
                marker_color='#4ecca3',
                marker=dict(
                    line=dict(color='#2dd4a8', width=1),
                    opacity=0.9
                )
            ))
            fig.add_trace(go.Bar(
                x=df['date'], 
                y=df['sells'], 
                name='Sells', 
                marker_color='#e94560',
                marker=dict(
                    line=dict(color='#ff6b81', width=1),
                    opacity=0.9
                )
            ))
            fig.update_layout(
                height=400,
                margin=dict(l=20, r=20, t=40, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(
                    gridcolor='rgba(103, 25, 255, 0.1)',
                    tickangle=45,
                    tickfont=dict(color='#a78bfa'),
                    title=None
                ),
                yaxis=dict(
                    gridcolor='rgba(103, 25, 255, 0.1)',
                    tickfont=dict(color='#a78bfa'),
                    title=None
                ),
                legend=dict(
                    font=dict(color='#a78bfa'),
                    bgcolor='rgba(0,0,0,0)'
                ),
                hovermode='x unified',
                barmode='group'
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No trades in last 7 days")
    
    with c2:
        st.markdown("### 👥 User Growth (Last 30 Days)")
        users = query("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM users 
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
        if users:
            df = pd.DataFrame(users)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['date'], 
                y=df['count'], 
                mode='lines+markers',
                line=dict(color='#6719ff', width=3, shape='spline'),
                marker=dict(
                    color='#8a4dff',
                    size=8,
                    line=dict(color='#a78bfa', width=2)
                ),
                fill='tozeroy',
                fillcolor='rgba(103, 25, 255, 0.1)'
            ))
            fig.update_layout(
                height=400,
                margin=dict(l=20, r=20, t=40, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(
                    gridcolor='rgba(103, 25, 255, 0.1)',
                    tickangle=45,
                    tickfont=dict(color='#a78bfa'),
                    title=None
                ),
                yaxis=dict(
                    gridcolor='rgba(103, 25, 255, 0.1)',
                    tickfont=dict(color='#a78bfa'),
                    title=None
                ),
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No new users in last 30 days")
    
    # Top tokens trading volume
    st.markdown("---")
    st.markdown("### 🏆 Top Traded Tokens (Today)")
    
    top_tokens = query("""
        SELECT 
            COALESCE(p.token_symbol, LEFT(th.token_address, 8) || '...') as token,
            COUNT(*) as trades,
            COALESCE(SUM(th.amount::numeric * th.price::numeric), 0) as volume
        FROM trade_history th
        LEFT JOIN positions p ON th.token_address = p.token_address
        WHERE DATE(th.created_at) = CURRENT_DATE
        GROUP BY p.token_symbol, th.token_address
        ORDER BY trades DESC
        LIMIT 10
    """)
    
    if top_tokens:
        df = pd.DataFrame(top_tokens)
        fig = px.bar(
            df, 
            x='token', 
            y='trades',
            color='trades',
            color_continuous_scale=['#4ecca3', '#6719ff', '#e94560'],
            title=None
        )
        fig.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                gridcolor='rgba(103, 25, 255, 0.1)',
                tickangle=45,
                tickfont=dict(color='#a78bfa'),
                title=None
            ),
            yaxis=dict(
                gridcolor='rgba(103, 25, 255, 0.1)',
                tickfont=dict(color='#a78bfa'),
                title=None
            ),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # Recent trades table with styling
    st.markdown("---")
    st.markdown("### 🔄 Recent Activity Feed")
    
    recent = query("""
        SELECT 
            th.created_at as "Time",
            u.username as "User",
            th.trade_type as "Type",
            LEFT(th.token_address, 8) || '...' as "Token",
            ROUND(th.amount::numeric, 4) as "Amount",
            ROUND(th.price::numeric, 6) as "Price (SOL)"
        FROM trade_history th
        JOIN users u ON th.user_id = u.user_id
        ORDER BY th.created_at DESC 
        LIMIT 20
    """)
    
    if recent:
        df = pd.DataFrame(recent)
        if 'Time' in df.columns:
            df['Time'] = pd.to_datetime(df['Time']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Style the trade type column
        def style_trade_type(val):
            if val == 'buy':
                return 'background-color: rgba(78, 204, 163, 0.2); color: #4ecca3; font-weight: 600;'
            elif val in ['sell', 'auto-sell']:
                return 'background-color: rgba(233, 69, 96, 0.2); color: #e94560; font-weight: 600;'
            return ''
        
        styled_df = df.style.applymap(style_trade_type, subset=['Type'])
        st.dataframe(styled_df, use_container_width=True, height=400)
    else:
        st.info("No recent trades available")

# ============================================
# USERS PAGE
# ============================================
def users_page():
    section_header("👥 User Management", "Monitor and manage user accounts")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search = st.text_input("🔍 Search Users", placeholder="Search by username or ID...")
    
    with col2:
        status_filter = st.selectbox("Status", ["All Users", "Active Only", "Inactive Only"])
    
    where_clause = ""
    if status_filter == "Active Only":
        where_clause = "WHERE u.is_active = true"
    elif status_filter == "Inactive Only":
        where_clause = "WHERE u.is_active = false"
    
    users = query(f"""
        SELECT 
            u.user_id as "ID",
            u.username as "Username",
            u.is_active as "Active",
            u.created_at as "Joined",
            COALESCE(w.wallet_count, 0) as "Wallets",
            COALESCE(t.trade_count, 0) as "Trades",
            COALESCE(r.ref_earned, 0) as "Ref Earnings"
        FROM users u
        LEFT JOIN (
            SELECT user_id, COUNT(*) as wallet_count 
            FROM wallets 
            WHERE is_active = true 
            GROUP BY user_id
        ) w ON u.user_id = w.user_id
        LEFT JOIN (
            SELECT user_id, COUNT(*) as trade_count 
            FROM trade_history 
            GROUP BY user_id
        ) t ON u.user_id = t.user_id
        LEFT JOIN (
            SELECT referrer_id, COALESCE(SUM(commission::numeric), 0) as ref_earned
            FROM referral_earnings
            GROUP BY referrer_id
        ) r ON u.user_id = r.referrer_id
        {where_clause}
        ORDER BY u.created_at DESC
        LIMIT 200
    """)
    
    if users:
        if search:
            users = [u for u in users if search.lower() in str(u.get('Username', '')).lower() or search in str(u.get('ID', ''))]
        
        df = pd.DataFrame(users)
        
        # Style the dataframe
        def highlight_active(val):
            if val == True:
                return 'background-color: rgba(78, 204, 163, 0.2); color: #4ecca3; font-weight: 600;'
            return 'background-color: rgba(233, 69, 96, 0.2); color: #e94560; font-weight: 600;'
        
        styled_df = df.style.applymap(highlight_active, subset=['Active'])
        st.dataframe(styled_df, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        user_id = st.number_input("User ID", min_value=1, step=1)
    with c2:
        action = st.selectbox("Action", ["Whitelist", "Blacklist", "Activate", "Deactivate"])
    with c3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⚡ Execute", use_container_width=True):
            if action == "Whitelist":
                execute("INSERT INTO fee_whitelist (user_id) VALUES (%s) ON CONFLICT DO NOTHING", (user_id,))
                st.success(f"✅ User {user_id} whitelisted")
            elif action == "Blacklist":
                execute("UPDATE users SET is_active = false WHERE user_id = %s", (user_id,))
                st.success(f"🚫 User {user_id} blacklisted")
            elif action == "Activate":
                execute("UPDATE users SET is_active = true WHERE user_id = %s", (user_id,))
                st.success(f"✅ User {user_id} activated")
            elif action == "Deactivate":
                execute("UPDATE users SET is_active = false WHERE user_id = %s", (user_id,))
                st.success(f"⚠️ User {user_id} deactivated")
            time.sleep(1)
            st.rerun()

# ============================================
# WALLETS PAGE
# ============================================
def wallets_page():
    section_header("💼 Wallet Management", "Monitor connected wallets")
    
    wallets = query("""
        SELECT 
            w.id as "ID",
            u.username as "User",
            w.wallet_name as "Wallet Name",
            w.wallet_number as "Wallet #",
            LEFT(w.public_key, 12) || '...' as "Public Key",
            w.default_buy_amount as "Default Buy (SOL)",
            w.created_at as "Created"
        FROM wallets w
        JOIN users u ON w.user_id = u.user_id
        WHERE w.is_active = true
        ORDER BY w.created_at DESC
        LIMIT 200
    """)
    
    if wallets:
        df = pd.DataFrame(wallets)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No wallets found")

# ============================================
# CHANNELS PAGE
# ============================================
def channels_page():
    section_header("📡 Channel Monitoring", "Track Telegram channels")
    
    stats = query("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN is_private THEN 1 END) as private,
            COUNT(CASE WHEN NOT is_private THEN 1 END) as public
        FROM channels WHERE is_active = true
    """)
    
    if stats:
        s = stats[0]
        c1, c2, c3 = st.columns(3)
        with c1:
            metric_card("Total Channels", s.get('total', 0), "📡")
        with c2:
            metric_card("Public Channels", s.get('public', 0), "🌐")
        with c3:
            metric_card("Private Channels", s.get('private', 0), "🔒")
    
    st.markdown("---")
    
    channels = query("""
        SELECT 
            c.id as "ID",
            u.username as "User",
            c.channel_name as "Channel",
            CASE WHEN c.is_private THEN '🔒 Private' ELSE '🌐 Public' END as "Type",
            c.signal_count as "Signals",
            c.created_at as "Added"
        FROM channels c
        JOIN users u ON c.user_id = u.user_id
        WHERE c.is_active = true
        ORDER BY c.created_at DESC
        LIMIT 100
    """)
    
    if channels:
        df = pd.DataFrame(channels)
        st.dataframe(df, use_container_width=True)

# ============================================
# POSITIONS PAGE
# ============================================
def positions_page():
    section_header("📈 Active Positions", "Current trading positions")
    
    positions = query("""
        SELECT 
            p.id as "ID",
            u.username as "User",
            COALESCE(p.token_symbol, LEFT(p.token_address, 12) || '...') as "Token",
            ROUND(p.amount::numeric, 4) as "Amount",
            ROUND(p.entry_price::numeric, 8) as "Entry Price",
            ROUND((p.amount::numeric * p.entry_price::numeric), 4) as "Value (SOL)",
            p.created_at as "Opened"
        FROM positions p
        JOIN users u ON p.user_id = u.user_id
        WHERE p.is_active = true AND p.amount > 0
        ORDER BY p.created_at DESC
        LIMIT 100
    """)
    
    if positions:
        df = pd.DataFrame(positions)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No active positions")

# ============================================
# TRADES PAGE
# ============================================
def trades_page():
    section_header("💱 Trade History", "Complete trading records")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        trade_type = st.selectbox("Type", ["All", "buy", "sell", "auto-sell"])
    with c2:
        date_range = st.selectbox("Period", ["Today", "Last 7 Days", "Last 30 Days", "All Time"])
    with c3:
        limit = st.selectbox("Records", [50, 100, 200, 500], index=1)
    
    type_filter = "" if trade_type == "All" else f"AND th.trade_type = '{trade_type}'"
    
    date_filter = ""
    if date_range == "Today":
        date_filter = "AND DATE(th.created_at) = CURRENT_DATE"
    elif date_range == "Last 7 Days":
        date_filter = "AND th.created_at >= CURRENT_DATE - INTERVAL '7 days'"
    elif date_range == "Last 30 Days":
        date_filter = "AND th.created_at >= CURRENT_DATE - INTERVAL '30 days'"
    
    trades = query(f"""
        SELECT 
            th.created_at as "Time",
            u.username as "User",
            th.trade_type as "Type",
            LEFT(th.token_address, 12) || '...' as "Token",
            ROUND(th.amount::numeric, 4) as "Amount",
            ROUND(th.price::numeric, 8) as "Price (SOL)",
            ROUND((th.amount::numeric * th.price::numeric), 4) as "Value",
            LEFT(th.txid, 12) || '...' as "TxID"
        FROM trade_history th
        JOIN users u ON th.user_id = u.user_id
        WHERE 1=1 {type_filter} {date_filter}
        ORDER BY th.created_at DESC
        LIMIT {limit}
    """)
    
    if trades:
        df = pd.DataFrame(trades)
        
        # Style trade types
        def style_trade_type(val):
            if val == 'buy':
                return 'background-color: rgba(78, 204, 163, 0.2); color: #4ecca3; font-weight: 600;'
            elif val in ['sell', 'auto-sell']:
                return 'background-color: rgba(233, 69, 96, 0.2); color: #e94560; font-weight: 600;'
            return ''
        
        styled_df = df.style.applymap(style_trade_type, subset=['Type'])
        st.dataframe(styled_df, use_container_width=True)
        
        # Download button
        csv = df.to_csv(index=False)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.download_button(
                "📥 Download CSV",
                csv,
                f"trades_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                "text/csv",
                use_container_width=True
            )
    else:
        st.info("No trades found")

# ============================================
# REFERRALS PAGE
# ============================================
def referrals_page():
    section_header("🔗 Referral System", "Track referral earnings")
    
    st.markdown("### 🏆 Top Referrers")
    top = query("""
        SELECT 
            u.username as "Referrer",
            COUNT(*) as "Referrals",
            COALESCE(SUM(re.commission::numeric), 0) as "Total Earned (SOL)",
            ROUND(AVG(re.commission::numeric), 4) as "Avg Commission"
        FROM referrals r
        JOIN users u ON r.referrer_id = u.user_id
        LEFT JOIN referral_earnings re ON r.referrer_id = re.referrer_id
        WHERE r.is_active = true
        GROUP BY r.referrer_id, u.username
        ORDER BY "Total Earned (SOL)" DESC
        LIMIT 20
    """)
    
    if top:
        df = pd.DataFrame(top)
        
        # Bar chart for top referrers
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df['Referrer'],
            y=df['Total Earned (SOL)'],
            marker=dict(
                color=df['Total Earned (SOL)'],
                colorscale=['#4ecca3', '#6719ff', '#e94560'],
                showscale=False
            ),
            text=df['Total Earned (SOL)'].apply(lambda x: f'{x:.4f} SOL'),
            textposition='outside',
            textfont=dict(color='#a78bfa')
        ))
        fig.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                gridcolor='rgba(103, 25, 255, 0.1)',
                tickangle=45,
                tickfont=dict(color='#a78bfa')
            ),
            yaxis=dict(
                gridcolor='rgba(103, 25, 255, 0.1)',
                tickfont=dict(color='#a78bfa')
            )
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        st.markdown("---")
        st.dataframe(df, use_container_width=True)

# ============================================
# FEES PAGE
# ============================================
def fees_page():
    section_header("💰 Fee Configuration", "Manage transaction fees")
    
    current = query("SELECT * FROM fee_config WHERE is_active = true ORDER BY id DESC LIMIT 1")
    
    if current:
        c = current[0]
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("### Current Configuration")
            st.metric("Fee Percentage", f"{c.get('fee_percent', 0)}%")
            
            wallet = c.get('fee_wallet', 'Not Set')
            if wallet and wallet != 'Not Set':
                st.metric("Fee Wallet", f"{wallet[:12]}...{wallet[-8:]}")
            else:
                st.metric("Fee Wallet", "Not Set")
        
        with c2:
            st.markdown("### Update Fee")
            new_fee = st.slider(
                "Fee Percentage",
                min_value=0.0,
                max_value=10.0,
                value=float(c.get('fee_percent', 0.05)),
                step=0.05,
                format="%.3f%%"
            )
            
            st.markdown(f"""
                <div style="padding: 15px; background: rgba(103, 25, 255, 0.1); border-radius: 12px; 
                     border: 1px solid rgba(103, 25, 255, 0.2); margin-top: 10px;">
                    <p style="color: #a78bfa; margin: 0;">New Fee: <strong style="color: white;">{new_fee}%</strong></p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("💾 Save Configuration", use_container_width=True):
                execute("INSERT INTO fee_config (fee_percent, is_active) VALUES (%s, true)", (new_fee,))
                st.success(f"✅ Fee updated to {new_fee}%")
                time.sleep(1)
                st.rerun()
    else:
        st.warning("No fee configuration found")
        
        new_fee = st.slider(
            "Set Initial Fee Percentage",
            min_value=0.0,
            max_value=10.0,
            value=0.05,
            step=0.05,
            format="%.3f%%"
        )
        if st.button("💾 Create Configuration", use_container_width=True):
            execute("INSERT INTO fee_config (fee_percent, is_active) VALUES (%s, true)", (new_fee,))
            st.success(f"✅ Fee configuration created with {new_fee}%")
            st.rerun()

# ============================================
# WHITELIST PAGE
# ============================================
def whitelist_page():
    section_header("✅ Fee Whitelist", "Users exempt from transaction fees")
    
    whitelist = query("""
        SELECT 
            fw.user_id as "User ID",
            u.username as "Username",
            fw.created_at as "Whitelisted Since"
        FROM fee_whitelist fw
        LEFT JOIN users u ON fw.user_id = u.user_id
        WHERE fw.is_active = true
        ORDER BY fw.created_at DESC
    """)
    
    if whitelist:
        df = pd.DataFrame(whitelist)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No users whitelisted")
    
    st.markdown("---")
    st.markdown("### Manage Whitelist")
    
    c1, c2 = st.columns(2)
    with c1:
        add_id = st.number_input("Add User ID", min_value=1, step=1)
        if st.button("✅ Add to Whitelist", use_container_width=True):
            execute("INSERT INTO fee_whitelist (user_id) VALUES (%s) ON CONFLICT DO NOTHING", (add_id,))
            st.success(f"✅ User {add_id} added to whitelist")
            time.sleep(1)
            st.rerun()
    
    with c2:
        remove_id = st.number_input("Remove User ID", min_value=1, step=1)
        if st.button("❌ Remove from Whitelist", use_container_width=True):
            execute("UPDATE fee_whitelist SET is_active = false WHERE user_id = %s", (remove_id,))
            st.success(f"✅ User {remove_id} removed from whitelist")
            time.sleep(1)
            st.rerun()

# ============================================
# BLACKLIST PAGE
# ============================================
def blacklist_page():
    section_header("🚫 Blacklisted Users", "Deactivated accounts")
    
    blacklist = query("""
        SELECT 
            user_id as "User ID",
            username as "Username",
            updated_at as "Deactivated Since"
        FROM users
        WHERE is_active = false
        ORDER BY updated_at DESC
    """)
    
    if blacklist:
        df = pd.DataFrame(blacklist)
        
        # Highlight deactivated users
        def highlight_inactive(val):
            return 'background-color: rgba(233, 69, 96, 0.2);'
        
        styled_df = df.style.applymap(highlight_inactive, subset=['Deactivated Since'])
        st.dataframe(styled_df, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### Reactivate User")
        
        reactivate_id = st.number_input("Enter User ID to Reactivate", min_value=1, step=1)
        if st.button("✅ Reactivate User", use_container_width=True):
            execute("UPDATE users SET is_active = true WHERE user_id = %s", (reactivate_id,))
            st.success(f"✅ User {reactivate_id} reactivated")
            time.sleep(1)
            st.rerun()
    else:
        st.info("No blacklisted users - all accounts are active! 🎉")

# ============================================
# SNIPE LOGS PAGE
# ============================================
def snipelogs_page():
    section_header("🎯 Snipe Logs", "Bot execution history")
    
    logs = query("""
        SELECT 
            sl.created_at as "Time",
            u.username as "User",
            sl.channel_name as "Channel",
            LEFT(sl.token_address, 12) || '...' as "Token",
            sl.status as "Status",
            sl.error_message as "Error"
        FROM snipe_logs sl
        JOIN users u ON sl.user_id = u.user_id
        ORDER BY sl.created_at DESC
        LIMIT 100
    """)
    
    if logs:
        df = pd.DataFrame(logs)
        
        # Style status column
        def style_status(val):
            if val == 'success':
                return 'background-color: rgba(78, 204, 163, 0.2); color: #4ecca3; font-weight: 600;'
            elif val == 'failed':
                return 'background-color: rgba(233, 69, 96, 0.2); color: #e94560; font-weight: 600;'
            return ''
        
        styled_df = df.style.applymap(style_status, subset=['Status'])
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.info("No snipe logs available")

# ============================================
# SESSIONS PAGE
# ============================================
def sessions_page():
    section_header("🔐 Active Sessions", "Connected Telegram sessions")
    
    sessions = query("""
        SELECT 
            user_id as "User ID",
            username as "Username",
            telegram_api_id as "API ID",
            LEFT(telegram_phone, 12) || '...' as "Phone",
            updated_at as "Last Active"
        FROM users
        WHERE telegram_session_string IS NOT NULL
        ORDER BY updated_at DESC
    """)
    
    if sessions:
        df = pd.DataFrame(sessions)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No active sessions")

# ============================================
# SETTINGS PAGE
# ============================================
def settings_page():
    section_header("⚙️ System Settings", "Database management and maintenance")
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("### 📊 Database Overview")
        stats = query("""
            SELECT 
                (SELECT COUNT(*) FROM users) as "Total Users",
                (SELECT COUNT(*) FROM wallets) as "Total Wallets",
                (SELECT COUNT(*) FROM positions) as "Total Positions",
                (SELECT COUNT(*) FROM channels) as "Total Channels",
                (SELECT COUNT(*) FROM trade_history) as "Total Trades",
                (SELECT COUNT(*) FROM snipe_logs) as "Total Logs"
        """)
        if stats:
            s = stats[0]
            for k, v in s.items():
                st.metric(k, v)
    
    with c2:
        st.markdown("### 🛠️ Maintenance Tools")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🗑️ Clean Old Logs (>30 days)", use_container_width=True):
            execute("DELETE FROM snipe_logs WHERE created_at < CURRENT_DATE - INTERVAL '30 days'")
            st.success("✅ Old logs cleaned successfully!")
            time.sleep(1)
            st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🔄 Reset Daily Trade Counters", use_container_width=True):
            execute("UPDATE users SET daily_trades = 0")
            st.success("✅ Daily trade counters reset!")
            time.sleep(1)
            st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("📊 Optimize Database", use_container_width=True):
            try:
                execute("VACUUM ANALYZE")
                st.success("✅ Database optimized successfully!")
            except:
                st.warning("⚠️ VACUUM not available on this database")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("📈 Recalculate Statistics", use_container_width=True):
            execute("ANALYZE")
            st.success("✅ Statistics recalculated!")
    
    st.markdown("---")
    
    # System health
    st.markdown("### ❤️ System Health")
    
    # Check database connection
    db_status = "✅ Connected" if get_db_connection() else "❌ Disconnected"
    
    # Check active users
    active_users = query("SELECT COUNT(*) as count FROM users WHERE is_active = true")
    user_status = f"✅ {active_users[0]['count']} Online" if active_users else "❌ Error"
    
    health_checks = {
        "Database": db_status,
        "Active Users": user_status,
        "Trading Engine": "✅ Running",
        "Fee Collection": "✅ Active"
    }
    
    cols = st.columns(len(health_checks))
    for i, (key, value) in enumerate(health_checks.items()):
        with cols[i]:
            st.markdown(f"""
                <div style="padding: 15px; background: rgba(103, 25, 255, 0.1); border-radius: 12px; 
                     border: 1px solid rgba(103, 25, 255, 0.2); text-align: center;">
                    <p style="color: #a78bfa; font-size: 0.8rem; margin: 0;">{key}</p>
                    <p style="color: #4ecca3; font-size: 1.1rem; margin: 5px 0 0 0;">{value}</p>
                </div>
            """, unsafe_allow_html=True)

# ============================================
# MAIN
# ============================================
def main():
    load_css()
    
    if not check_password():
        return
    
    page = sidebar()
    
    # Page routing
    pages = {
        "Dashboard": dashboard_page,
        "Users": users_page,
        "Wallets": wallets_page,
        "Channels": channels_page,
        "Positions": positions_page,
        "Trades": trades_page,
        "Referrals": referrals_page,
        "Fees": fees_page,
        "Whitelist": whitelist_page,
        "Blacklist": blacklist_page,
        "Snipe Logs": snipelogs_page,
        "Sessions": sessions_page,
        "Settings": settings_page
    }
    
    if page in pages:
        pages[page]()

if __name__ == "__main__":
    main()