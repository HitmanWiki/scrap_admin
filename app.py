"""
GHOSTWIRE Admin Dashboard v5.0
CyberPunk Minimal | Premium Dark Theme | Pixel Perfect
"""

import streamlit as st
import pandas as pd
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
import time
import os
import hashlib
import base64
from pathlib import Path

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="GHOSTWIRE Admin",
    page_icon="👻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CONFIG
# ============================================
def get_config(key, default=None):
    try: return st.secrets[key]
    except: return os.getenv(key, default)

# ============================================
# LOGO HELPER
# ============================================
def get_logo_base64():
    """Load logo.png and convert to base64 for HTML embedding"""
    possible_paths = [
        Path(__file__).parent / "logo.png",
        Path("logo.png"),
        Path("assets/logo.png"),
        Path("static/logo.png")
    ]
    
    for path in possible_paths:
        if path.exists():
            with open(path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
    
    return None

def render_logo_html(width="80px", height="80px", css_class=""):
    """Render logo as HTML img tag"""
    logo_b64 = get_logo_base64()
    
    if logo_b64:
        return f'<img src="data:image/png;base64,{logo_b64}" width="{width}" height="{height}" class="{css_class}" style="object-fit: contain;">'
    else:
        return '👻'

# ============================================
# DATABASE
# ============================================
@st.cache_resource(ttl=300)
def get_db_connection():
    try:
        db_url = get_config("DATABASE_URL")
        if not db_url: return None
        return psycopg2.connect(db_url, sslmode='require', connect_timeout=10)
    except: return None

def query(sql, params=None):
    conn = get_db_connection()
    if not conn: return []
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params)
        result = cur.fetchall()
        cur.close(); return result
    except: return []

def execute(sql, params=None):
    conn = get_db_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit(); cur.close()
        return True
    except: return False

# ============================================
# ADMIN AUTH
# ============================================
def init_admin():
    execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            id SERIAL PRIMARY KEY, username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL, role TEXT DEFAULT 'admin',
            is_active BOOLEAN DEFAULT true, last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    existing = query("SELECT COUNT(*) as cnt FROM admin_users")
    if existing and existing[0]['cnt'] == 0:
        pwd = hashlib.sha256("GhostWire@2026".encode()).hexdigest()
        execute("INSERT INTO admin_users (username, password_hash, role) VALUES (%s,%s,%s)", ("admin", pwd, "superadmin"))

def verify_admin(username, password):
    conn = get_db_connection()
    if not conn: return None
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        cur.execute("SELECT * FROM admin_users WHERE username=%s AND password_hash=%s AND is_active=true", (username, pwd_hash))
        user = cur.fetchone(); cur.close()
        return user
    except: return None

def create_admin(username, password, role='admin'):
    pwd = hashlib.sha256(password.encode()).hexdigest()
    try:
        execute("INSERT INTO admin_users (username, password_hash, role) VALUES (%s,%s,%s)", (username, pwd, role))
        return True
    except: return False

def get_admins():
    return query("SELECT id, username, role, is_active, last_login, created_at FROM admin_users ORDER BY created_at DESC")

init_admin()

# ============================================
# CYBERPUNK PREMIUM CSS
# ============================================
def load_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
        
        * {
            font-family: 'Space Grotesk', sans-serif;
        }
        
        /* ========== GLOBAL BACKGROUND ========== */
        .stApp {
            background: #0a0a0a;
        }
        
        /* ========== AUTH SCREEN - FIXED CENTERING ========== */
        .auth-wrapper {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            background: 
                radial-gradient(ellipse at 20% 50%, rgba(0, 255, 136, 0.03) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 20%, rgba(0, 255, 136, 0.02) 0%, transparent 50%),
                #0a0a0a;
            z-index: 1000;
            overflow: auto;
        }
        
        .auth-box {
            background: #0d0d0d;
            border: 1px solid #1a1a1a;
            border-radius: 0;
            padding: 50px 50px 40px 50px;
            max-width: 440px;
            width: 90%;
            position: relative;
            margin: 20px;
        }
        
        .auth-box::before {
            content: '';
            position: absolute;
            top: -1px;
            left: 20px;
            right: 20px;
            height: 1px;
            background: linear-gradient(90deg, transparent, #00ff88, transparent);
        }
        
        .auth-logo-section {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .auth-logo-img {
            width: 80px;
            height: 80px;
            margin: 0 auto 15px;
            display: block;
            filter: drop-shadow(0 0 15px rgba(0, 255, 136, 0.3));
            animation: logoFloat 3s ease-in-out infinite;
        }
        
        .auth-logo-fallback {
            font-size: 48px;
            margin-bottom: 15px;
            filter: drop-shadow(0 0 15px rgba(0, 255, 136, 0.3));
            animation: logoFloat 3s ease-in-out infinite;
            display: block;
        }
        
        @keyframes logoFloat {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-8px); }
        }
        
        .auth-brand {
            font-size: 2.5rem;
            font-weight: 700;
            letter-spacing: 4px;
            color: #ffffff;
            margin: 0 0 8px 0;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .auth-brand-dot {
            color: #00ff88;
        }
        
        .auth-tagline {
            color: #666;
            font-size: 0.7rem;
            letter-spacing: 5px;
            text-transform: uppercase;
            margin: 0;
            font-weight: 300;
        }
        
        /* ========== INPUT FIELDS ========== */
        .stTextInput > div > div > input {
            background: #0f0f0f !important;
            border: 1px solid #1a1a1a !important;
            border-radius: 0 !important;
            color: #ffffff !important;
            padding: 16px 18px !important;
            font-size: 0.9rem !important;
            font-family: 'JetBrains Mono', monospace !important;
            letter-spacing: 1px !important;
            transition: all 0.3s ease !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #00ff88 !important;
            box-shadow: none !important;
            outline: none !important;
            background: #111111 !important;
        }
        
        .stTextInput > div > div > input::placeholder {
            color: #333 !important;
            font-family: 'JetBrains Mono', monospace !important;
            letter-spacing: 2px !important;
        }
        
        /* ========== BUTTON ========== */
        .stButton > button {
            background: transparent !important;
            color: #00ff88 !important;
            border: 1px solid #00ff88 !important;
            border-radius: 0 !important;
            padding: 16px 32px !important;
            font-weight: 500 !important;
            font-size: 0.85rem !important;
            letter-spacing: 3px !important;
            text-transform: uppercase !important;
            transition: all 0.3s ease !important;
            font-family: 'JetBrains Mono', monospace !important;
        }
        
        .stButton > button:hover {
            background: #00ff88 !important;
            color: #0a0a0a !important;
            box-shadow: 0 0 30px rgba(0, 255, 136, 0.3) !important;
            transform: none !important;
        }
        
        .stButton > button:active {
            transform: scale(0.98) !important;
        }
        
        /* ========== ALERTS ========== */
        .stAlert {
            background: rgba(255, 0, 85, 0.05) !important;
            border: 1px solid rgba(255, 0, 85, 0.2) !important;
            border-radius: 0 !important;
            color: #ff0055 !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.8rem !important;
            letter-spacing: 1px !important;
            margin-bottom: 20px !important;
        }
        
        /* ========== SIDEBAR ========== */
        [data-testid="stSidebar"] {
            background: #0d0d0d !important;
            border-right: 1px solid #1a1a1a !important;
        }
        
        [data-testid="stSidebar"] .stRadio > label {
            color: #666 !important;
            padding: 12px 16px !important;
            border-radius: 0 !important;
            transition: all 0.2s ease !important;
            font-size: 0.85rem !important;
            letter-spacing: 0.5px !important;
            font-weight: 400 !important;
        }
        
        [data-testid="stSidebar"] .stRadio > label:hover {
            background: rgba(0, 255, 136, 0.05) !important;
            color: #00ff88 !important;
        }
        
        /* ========== METRICS ========== */
        div[data-testid="stMetric"] {
            background: #0d0d0d !important;
            border: 1px solid #1a1a1a !important;
            border-radius: 0 !important;
            padding: 25px !important;
            position: relative !important;
        }
        
        div[data-testid="stMetric"]::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 3px;
            height: 30px;
            background: #00ff88;
        }
        
        div[data-testid="stMetric"]:hover {
            border-color: #00ff88 !important;
        }
        
        div[data-testid="stMetricValue"] {
            color: #ffffff !important;
            font-weight: 700 !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 2.2rem !important;
        }
        
        div[data-testid="stMetric"] label {
            color: #666 !important;
            text-transform: uppercase !important;
            letter-spacing: 2px !important;
            font-size: 0.65rem !important;
            font-weight: 400 !important;
        }
        
        /* ========== DATAFRAME ========== */
        .stDataFrame {
            background: #0d0d0d !important;
            border-radius: 0 !important;
            border: 1px solid #1a1a1a !important;
        }
        
        .stDataFrame th {
            background: #111111 !important;
            color: #00ff88 !important;
            font-weight: 500 !important;
            font-size: 0.7rem !important;
            text-transform: uppercase !important;
            letter-spacing: 1.5px !important;
            padding: 16px 20px !important;
            border-bottom: 2px solid #1a1a1a !important;
            font-family: 'JetBrains Mono', monospace !important;
        }
        
        .stDataFrame td {
            background: transparent !important;
            color: #999 !important;
            padding: 14px 20px !important;
            border-bottom: 1px solid #111111 !important;
            font-size: 0.85rem !important;
            font-family: 'JetBrains Mono', monospace !important;
        }
        
        /* ========== HEADINGS ========== */
        h1 {
            font-family: 'JetBrains Mono', monospace !important;
            font-weight: 700 !important;
            letter-spacing: 1px !important;
            font-size: 2rem !important;
        }
        
        h3 {
            color: #999 !important;
            font-weight: 400 !important;
            letter-spacing: 2px !important;
            font-size: 0.9rem !important;
            text-transform: uppercase !important;
        }
        
        /* ========== DIVIDER ========== */
        hr {
            border-color: #1a1a1a !important;
            margin: 30px 0 !important;
        }
        
        /* ========== SCROLLBAR ========== */
        ::-webkit-scrollbar {
            width: 4px;
        }
        
        ::-webkit-scrollbar-track {
            background: #0a0a0a;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #1a1a1a;
            border-radius: 0;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #00ff88;
        }
        
        /* ========== EXPANDER ========== */
        .streamlit-expanderHeader {
            background: #0d0d0d !important;
            border: 1px solid #1a1a1a !important;
            border-radius: 0 !important;
            color: #00ff88 !important;
            font-family: 'JetBrains Mono', monospace !important;
            letter-spacing: 1px !important;
        }
        
        /* ========== SIDEBAR PROFILE ========== */
        .sidebar-profile-box {
            text-align: center;
            padding: 30px 20px;
            border-bottom: 1px solid #1a1a1a;
            margin-bottom: 20px;
        }
        
        .sidebar-logo-img {
            width: 60px;
            height: 60px;
            margin: 0 auto 12px;
            display: block;
        }
        
        .sidebar-logo-fallback {
            font-size: 36px;
            margin-bottom: 12px;
        }
        
        .sidebar-user-name {
            color: #ffffff;
            font-size: 1rem;
            font-weight: 500;
            letter-spacing: 1px;
            margin: 8px 0;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .sidebar-role-tag {
            display: inline-block;
            padding: 4px 16px;
            border: 1px solid #00ff88;
            color: #00ff88;
            font-size: 0.65rem;
            letter-spacing: 2px;
            font-family: 'JetBrains Mono', monospace;
        }
        
        /* Status indicator */
        .status-dot {
            width: 8px;
            height: 8px;
            background: #00ff88;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
            box-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
        }
        
        /* Info box */
        .info-box {
            background: #0d0d0d;
            border: 1px solid #1a1a1a;
            padding: 20px;
            margin: 20px 0;
        }
        
        .info-box p {
            color: #666;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            letter-spacing: 0.5px;
            margin: 0;
        }
        
        /* Hide Streamlit elements on login */
        .login-hidden [data-testid="stSidebar"],
        .login-hidden header,
        .login-hidden footer,
        .login-hidden [data-testid="stToolbar"] {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

# ============================================
# FIXED LOGIN PAGE
# ============================================
def login_page():
    # Add class to hide Streamlit UI elements
    st.markdown('<div class="login-hidden">', unsafe_allow_html=True)
    
    # Fixed centered wrapper
    st.markdown('<div class="auth-wrapper">', unsafe_allow_html=True)
    
    # Auth box - directly centered without column layout
    st.markdown('<div class="auth-box">', unsafe_allow_html=True)
    
    # Logo Section
    logo_html = render_logo_html(width="80px", height="80px", css_class="auth-logo-img")
    
    st.markdown(f"""
        <div class="auth-logo-section">
            {logo_html if logo_html else '<span class="auth-logo-fallback">👻</span>'}
            <h1 class="auth-brand">GHOST<span class="auth-brand-dot">.</span>WIRE</h1>
            <p class="auth-tagline">// admin console</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Login Form - no columns, full width
    username = st.text_input(
        "Username",
        placeholder="> username",
        label_visibility="collapsed",
        key="login_user"
    )
    
    # Minimal spacing
    st.markdown("<div style='margin: 8px 0;'></div>", unsafe_allow_html=True)
    
    password = st.text_input(
        "Password",
        type="password",
        placeholder="> password",
        label_visibility="collapsed",
        key="login_pass"
    )
    
    st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)
    
    # Full-width button, no column wrapping
    if st.button("// AUTHENTICATE", use_container_width=True, key="login_btn"):
        if not username or not password:
            st.error("> ERROR: All fields required")
        else:
            user = verify_admin(username, password)
            if user:
                execute(
                    "UPDATE admin_users SET last_login=CURRENT_TIMESTAMP WHERE id=%s",
                    (user['id'],)
                )
                st.session_state.authenticated = True
                st.session_state.admin_user = user
                st.rerun()
            else:
                st.error("> ERROR: Invalid credentials")
    
    # Footer
    st.markdown("""
        <div style="text-align: center; margin-top: 30px;">
            <p style="color: #333; font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; letter-spacing: 2px; margin: 0;">
                <span class="status-dot"></span> SYSTEM SECURED
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close auth-box
    st.markdown('</div>', unsafe_allow_html=True)  # Close auth-wrapper
    st.markdown('</div>', unsafe_allow_html=True)  # Close login-hidden

# ============================================
# SIDEBAR
# ============================================
def sidebar():
    with st.sidebar:
        admin_user = st.session_state.get('admin_user', {})
        username = admin_user.get('username', 'ADMIN')
        role = admin_user.get('role', 'admin').upper()
        
        # Profile Section with Logo
        logo_html = render_logo_html(width="60px", height="60px", css_class="sidebar-logo-img")
        
        st.markdown(f"""
            <div class="sidebar-profile-box">
                {logo_html if logo_html else '<div class="sidebar-logo-fallback">👻</div>'}
                <div class="sidebar-user-name">{username}</div>
                <span class="sidebar-role-tag">{role}</span>
            </div>
        """, unsafe_allow_html=True)
        
        # Navigation
        menu_options = {
            "// DASHBOARD": "Dashboard",
            "// USERS": "Users",
            "// WALLETS": "Wallets",
            "// CHANNELS": "Channels",
            "// POSITIONS": "Positions",
            "// TRADES": "Trades",
            "// REFERRALS": "Referrals",
            "// VERIFICATION": "Verification",
            "// TICKETS": "Tickets",
            "// FEES": "Fees",
            "// WHITELIST": "Whitelist",
            "// BLACKLIST": "Blacklist",
            "// SNIPE LOGS": "SnipeLogs",
            "// SESSIONS": "Sessions",
            "// ADMINS": "Admins",
            "// SETTINGS": "Settings"
        }
        
        selected = st.radio(
            "NAV",
            list(menu_options.keys()),
            label_visibility="collapsed"
        )
        
        page = menu_options[selected]
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Quick stats in sidebar
        try:
            users = query("SELECT COUNT(*) as c FROM users WHERE is_active=true")
            if users:
                st.markdown(f"""
                    <div style="padding: 15px; border: 1px solid #1a1a1a; margin: 10px 0;">
                        <p style="color: #666; font-size: 0.6rem; letter-spacing: 2px; margin: 0 0 5px 0;">ACTIVE USERS</p>
                        <p style="color: #00ff88; font-family: 'JetBrains Mono', monospace; font-size: 1.5rem; font-weight: 700; margin: 0;">{users[0]['c']}</p>
                    </div>
                """, unsafe_allow_html=True)
        except:
            pass
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Sign Out
        if st.button("// SIGN OUT", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.admin_user = None
            st.rerun()
        
        return page

# ============================================
# PAGES
# ============================================
def dashboard_page():
    st.markdown('<h1 style="color: #ffffff;">// DASHBOARD</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #666; font-family: \'JetBrains Mono\', monospace; font-size: 0.8rem; letter-spacing: 1px;">SYSTEM OVERVIEW</p>', unsafe_allow_html=True)
    
    stats = query("""
        SELECT 
            (SELECT COUNT(*) FROM users WHERE is_active=true) as users,
            (SELECT COUNT(*) FROM wallets WHERE is_active=true) as wallets,
            (SELECT COUNT(*) FROM positions WHERE is_active=true AND amount>0) as positions,
            (SELECT COUNT(*) FROM channels WHERE is_active=true) as channels,
            (SELECT COUNT(*) FROM trade_history WHERE DATE(created_at)=CURRENT_DATE) as today
    """)
    
    if stats:
        s = stats[0]
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("TOTAL USERS", s['users'] or 0)
        with col2:
            st.metric("ACTIVE WALLETS", s['wallets'] or 0)
        with col3:
            st.metric("OPEN POSITIONS", s['positions'] or 0)
        with col4:
            st.metric("CHANNELS", s['channels'] or 0)
        with col5:
            st.metric("TODAY'S TRADES", s['today'] or 0)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Recent Trades
    st.markdown('<h3>// RECENT TRANSACTIONS</h3>', unsafe_allow_html=True)
    trades = query("""
        SELECT 
            th.created_at as "TIME",
            u.username as "USER",
            th.trade_type as "TYPE",
            LEFT(th.token_address, 10) || '...' as "TOKEN",
            ROUND(th.amount::numeric, 4) as "AMOUNT"
        FROM trade_history th 
        JOIN users u ON th.user_id = u.user_id
        ORDER BY th.created_at DESC 
        LIMIT 15
    """)
    
    if trades:
        st.dataframe(
            pd.DataFrame(trades),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.markdown('<div class="info-box"><p>> No transactions found</p></div>', unsafe_allow_html=True)

def create_page(title, query_str, empty_msg="> No data found"):
    st.markdown(f'<h1 style="color: #ffffff;">// {title.upper()}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p style="color: #666; font-family: \'JetBrains Mono\', monospace; font-size: 0.8rem; letter-spacing: 1px;">{title.upper()} MANAGEMENT</p>', unsafe_allow_html=True)
    
    data = query(query_str)
    
    if data:
        st.dataframe(
            pd.DataFrame(data),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.markdown(f'<div class="info-box"><p>{empty_msg}</p></div>', unsafe_allow_html=True)
    
    return data

def users_page():
    create_page("Users", """
        SELECT 
            user_id as "ID",
            username as "USERNAME",
            is_active as "ACTIVE",
            created_at as "JOINED"
        FROM users 
        ORDER BY created_at DESC 
        LIMIT 200
    """)

def wallets_page():
    create_page("Wallets", """
        SELECT 
            w.id as "ID",
            u.username as "USER",
            w.wallet_name as "WALLET",
            LEFT(w.public_key, 12) || '...' as "KEY",
            w.default_buy_amount as "BUY AMOUNT"
        FROM wallets w 
        JOIN users u ON w.user_id = u.user_id 
        WHERE w.is_active = true 
        LIMIT 200
    """)

def channels_page():
    create_page("Channels", """
        SELECT 
            c.id as "ID",
            u.username as "USER",
            COALESCE(c.display_name, c.channel_name) as "CHANNEL",
            CASE WHEN c.is_private THEN 'PRIVATE' ELSE 'PUBLIC' END as "TYPE",
            COALESCE(c.sender_filter, '-') as "FILTER",
            CASE WHEN c.max_market_cap > 0 
                 THEN '$' || ROUND(c.max_market_cap)::text 
                 ELSE '-' END as "MAX MC"
        FROM channels c 
        JOIN users u ON c.user_id = u.user_id 
        WHERE c.is_active = true 
        ORDER BY c.created_at DESC
    """)

def positions_page():
    create_page("Positions", """
        SELECT 
            p.id as "ID",
            u.username as "USER",
            LEFT(p.token_address, 12) || '...' as "TOKEN",
            ROUND(p.amount::numeric, 2) as "AMOUNT",
            p.created_at as "CREATED"
        FROM positions p 
        JOIN users u ON p.user_id = u.user_id 
        WHERE p.is_active = true AND p.amount > 0 
        LIMIT 100
    """)

def trades_page():
    create_page("Trades", """
        SELECT 
            th.created_at as "TIME",
            u.username as "USER",
            th.trade_type as "TYPE",
            LEFT(th.token_address, 12) || '...' as "TOKEN",
            ROUND(th.amount::numeric, 4) as "AMOUNT"
        FROM trade_history th 
        JOIN users u ON th.user_id = u.user_id 
        ORDER BY th.created_at DESC 
        LIMIT 150
    """)

def referrals_page():
    create_page("Referrals", """
        SELECT 
            u.username as "REFERRER",
            COUNT(*) as "REFERRALS",
            COALESCE(SUM(re.commission::numeric), 0) as "EARNED"
        FROM referrals r2 
        JOIN users u ON r2.referrer_id = u.user_id 
        LEFT JOIN referral_earnings re ON r2.referrer_id = re.referrer_id 
        WHERE r2.is_active = true 
        GROUP BY r2.referrer_id, u.username 
        ORDER BY "EARNED" DESC 
        LIMIT 20
    """)

def verification_page():
    create_page("Token Verification", """
        SELECT 
            u.username as "USER",
            LEFT(tv.wallet_address, 12) || '...' as "WALLET",
            ROUND(tv.token_balance::numeric, 2) as "GHOSTWIRE",
            ROUND(tv.token_percent::numeric, 4) as "%",
            CASE WHEN tv.token_percent >= 2 
                 THEN 'WHALE' 
                 ELSE 'HOLDER' END as "TIER"
        FROM token_verifications tv 
        JOIN users u ON tv.user_id = u.user_id 
        WHERE tv.is_verified = true 
        ORDER BY tv.token_percent DESC
    """)

def tickets_page():
    create_page("Support Tickets", """
        SELECT 
            t.id as "ID",
            t.created_at as "CREATED",
            COALESCE(u.username, 'UNKNOWN') as "USER",
            t.ticket_type as "TYPE",
            t.subject as "SUBJECT",
            t.status as "STATUS"
        FROM support_tickets t 
        LEFT JOIN users u ON t.user_id = u.user_id 
        ORDER BY t.created_at DESC 
        LIMIT 50
    """)

def fees_page():
    st.markdown('<h1 style="color: #ffffff;">// FEE SYSTEM</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #666; font-family: \'JetBrains Mono\', monospace; font-size: 0.8rem; letter-spacing: 1px;">FEE CONFIGURATION</p>', unsafe_allow_html=True)
    
    fees = query("SELECT * FROM fee_config WHERE is_active=true ORDER BY id DESC LIMIT 1")
    if fees:
        f = fees[0]
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("FEE %", f"{f.get('fee_percent', 0.05)}%")
        with col2:
            wallet = str(f.get('fee_wallet', 'NOT SET'))
            st.metric("WALLET", wallet[:12] + '...' if len(wallet) > 12 else wallet)
        with col3:
            st.metric("STATUS", "ACTIVE")
    else:
        st.markdown('<div class="info-box"><p>> No fee config found</p></div>', unsafe_allow_html=True)

def whitelist_page():
    create_page("Fee Whitelist", """
        SELECT 
            fw.user_id as "USER ID",
            u.username as "USERNAME",
            fw.created_at as "ADDED"
        FROM fee_whitelist fw 
        LEFT JOIN users u ON fw.user_id = u.user_id 
        WHERE fw.is_active = true
    """)

def blacklist_page():
    create_page("Blacklist", """
        SELECT 
            user_id as "USER ID",
            username as "USERNAME",
            updated_at as "BLACKLISTED"
        FROM users 
        WHERE is_active = false
    """)

def snipelogs_page():
    create_page("Snipe Logs", """
        SELECT 
            sl.created_at as "TIME",
            u.username as "USER",
            sl.channel_name as "CHANNEL",
            LEFT(sl.token_address, 12) || '...' as "TOKEN",
            sl.status as "STATUS"
        FROM snipe_logs sl 
        JOIN users u ON sl.user_id = u.user_id 
        ORDER BY sl.created_at DESC 
        LIMIT 200
    """)

def sessions_page():
    create_page("Active Sessions", """
        SELECT 
            user_id as "USER ID",
            username as "USERNAME",
            LEFT(COALESCE(telegram_phone, ''), 12) || '...' as "PHONE",
            updated_at as "LAST ACTIVE"
        FROM users 
        WHERE telegram_session_string IS NOT NULL
    """)

def admins_page():
    st.markdown('<h1 style="color: #ffffff;">// ADMIN PANEL</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #666; font-family: \'JetBrains Mono\', monospace; font-size: 0.8rem; letter-spacing: 1px;">ADMINISTRATOR MANAGEMENT</p>', unsafe_allow_html=True)
    
    st.markdown('<h3>// CURRENT ADMINS</h3>', unsafe_allow_html=True)
    admins = get_admins()
    if admins:
        st.dataframe(
            pd.DataFrame(admins),
            use_container_width=True,
            hide_index=True
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.expander("// CREATE NEW ADMIN"):
        col1, col2 = st.columns(2)
        with col1:
            new_user = st.text_input("Username", placeholder="> username", key="new_admin_user", label_visibility="collapsed")
        with col2:
            new_pass = st.text_input("Password", type="password", placeholder="> password", key="new_admin_pass", label_visibility="collapsed")
        
        if st.button("// CREATE ADMIN", use_container_width=True):
            if new_user and new_pass:
                if create_admin(new_user, new_pass):
                    st.success("// ADMIN CREATED SUCCESSFULLY")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("// ERROR: USERNAME EXISTS")
            else:
                st.error("// ERROR: ALL FIELDS REQUIRED")

def settings_page():
    st.markdown('<h1 style="color: #ffffff;">// SETTINGS</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #666; font-family: \'JetBrains Mono\', monospace; font-size: 0.8rem; letter-spacing: 1px;">SYSTEM CONFIGURATION</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<h3>// MAINTENANCE</h3>', unsafe_allow_html=True)
        if st.button("// CLEAN OLD LOGS", use_container_width=True):
            execute("DELETE FROM snipe_logs WHERE created_at < CURRENT_DATE - INTERVAL '30 days'")
            st.success("// LOGS CLEANED SUCCESSFULLY")
    
    with col2:
        st.markdown('<h3>// DATABASE</h3>', unsafe_allow_html=True)
        try:
            tables = query("""
                SELECT tablename as "TABLE", n_live_tup as "ROWS"
                FROM pg_stat_user_tables
                ORDER BY n_live_tup DESC
                LIMIT 5
            """)
            if tables:
                st.dataframe(
                    pd.DataFrame(tables),
                    use_container_width=True,
                    hide_index=True
                )
        except:
            st.markdown('<div class="info-box"><p>> Stats unavailable</p></div>', unsafe_allow_html=True)

# ============================================
# MAIN
# ============================================
def main():
    load_css()
    
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.admin_user = None
    
    if not st.session_state.authenticated:
        login_page()
        return
    
    page = sidebar()
    
    pages = {
        "Dashboard": dashboard_page,
        "Users": users_page,
        "Wallets": wallets_page,
        "Channels": channels_page,
        "Positions": positions_page,
        "Trades": trades_page,
        "Referrals": referrals_page,
        "Verification": verification_page,
        "Tickets": tickets_page,
        "Fees": fees_page,
        "Whitelist": whitelist_page,
        "Blacklist": blacklist_page,
        "SnipeLogs": snipelogs_page,
        "Sessions": sessions_page,
        "Admins": admins_page,
        "Settings": settings_page
    }
    
    if page in pages:
        pages[page]()

if __name__ == "__main__":
    main()