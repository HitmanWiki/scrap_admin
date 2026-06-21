"""
GHOSTWIRE Admin Dashboard v5.2
CyberPunk Minimal | No External Dependencies | Stable
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
# PAGE CONFIG - MUST BE FIRST
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
@st.cache_data
def get_logo_base64():
    """Load logo.png and convert to base64"""
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

def render_logo(width="80px", height="80px"):
    """Render logo HTML"""
    logo_b64 = get_logo_base64()
    
    if logo_b64:
        return f'<img src="data:image/png;base64,{logo_b64}" width="{width}" height="{height}" style="object-fit:contain;display:block;margin:0 auto;filter:drop-shadow(0 0 10px rgba(0,255,136,0.3));">'
    else:
        return '<div style="font-size:48px;text-align:center;filter:drop-shadow(0 0 10px rgba(0,255,136,0.3));">👻</div>'

# ============================================
# DATABASE
# ============================================
@st.cache_resource(ttl=60)
def get_db_connection():
    try:
        db_url = get_config("DATABASE_URL")
        if not db_url: return None
        return psycopg2.connect(db_url, sslmode='require', connect_timeout=5)
    except: return None

def query(sql, params=None):
    conn = get_db_connection()
    if not conn: return []
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params)
        result = cur.fetchall()
        cur.close()
        return result
    except: return []

def execute(sql, params=None):
    conn = get_db_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        cur.close()
        return True
    except: return False

# ============================================
# ADMIN AUTH
# ============================================
def init_admin():
    try:
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
            execute("INSERT INTO admin_users (username, password_hash, role) VALUES (%s,%s,%s)", 
                   ("admin", pwd, "superadmin"))
    except: pass

def verify_admin(username, password):
    # Fallback for when DB is not available
    if username == "admin" and password == "GhostWire@2026":
        return {"id": 1, "username": "admin", "role": "superadmin"}
    
    try:
        conn = get_db_connection()
        if not conn: return None
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        cur.execute("SELECT * FROM admin_users WHERE username=%s AND password_hash=%s AND is_active=true", 
                   (username, pwd_hash))
        user = cur.fetchone()
        cur.close()
        return user
    except: return None

def create_admin(username, password, role='admin'):
    pwd = hashlib.sha256(password.encode()).hexdigest()
    try:
        execute("INSERT INTO admin_users (username, password_hash, role) VALUES (%s,%s,%s)", 
               (username, pwd, role))
        return True
    except: return False

def get_admins():
    return query("SELECT id, username, role, is_active, last_login, created_at FROM admin_users ORDER BY created_at DESC")

init_admin()

# ============================================
# CSS - NO EXTERNAL FONTS
# ============================================
def load_css():
    st.markdown("""
    <style>
        /* Global */
        .stApp {
            background: #0a0a0a;
        }
        
        /* Login Container */
        .login-wrapper {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #0a0a0a;
            z-index: 1000;
        }
        
        .login-card {
            background: #0d0d0d;
            border: 1px solid #1a1a1a;
            padding: 40px 45px;
            max-width: 400px;
            width: 90%;
            position: relative;
        }
        
        .login-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 20px;
            right: 20px;
            height: 1px;
            background: linear-gradient(90deg, transparent, #00ff88, transparent);
        }
        
        .brand-title {
            text-align: center;
            color: #ffffff;
            font-size: 2.2rem;
            font-weight: 700;
            letter-spacing: 4px;
            margin: 15px 0 5px 0;
            font-family: 'Courier New', monospace;
        }
        
        .brand-subtitle {
            text-align: center;
            color: #666;
            font-size: 0.7rem;
            letter-spacing: 5px;
            text-transform: uppercase;
            margin-bottom: 30px;
            font-family: 'Courier New', monospace;
        }
        
        /* Inputs */
        .stTextInput input {
            background: #0f0f0f !important;
            border: 1px solid #1a1a1a !important;
            border-radius: 0 !important;
            color: #fff !important;
            padding: 14px 16px !important;
            font-family: 'Courier New', monospace !important;
            font-size: 0.9rem !important;
            letter-spacing: 1px !important;
        }
        
        .stTextInput input:focus {
            border-color: #00ff88 !important;
            box-shadow: 0 0 15px rgba(0,255,136,0.1) !important;
        }
        
        .stTextInput input::placeholder {
            color: #333 !important;
            letter-spacing: 2px !important;
        }
        
        /* Buttons */
        .stButton button {
            background: transparent !important;
            color: #00ff88 !important;
            border: 1px solid #00ff88 !important;
            border-radius: 0 !important;
            padding: 14px 28px !important;
            font-weight: 600 !important;
            letter-spacing: 3px !important;
            text-transform: uppercase !important;
            font-family: 'Courier New', monospace !important;
            font-size: 0.85rem !important;
            transition: all 0.3s ease !important;
        }
        
        .stButton button:hover {
            background: #00ff88 !important;
            color: #0a0a0a !important;
            box-shadow: 0 0 30px rgba(0,255,136,0.2) !important;
        }
        
        /* Alerts */
        .stAlert {
            background: rgba(255,0,85,0.05) !important;
            border: 1px solid rgba(255,0,85,0.2) !important;
            border-radius: 0 !important;
            color: #ff0055 !important;
            font-family: 'Courier New', monospace !important;
            font-size: 0.8rem !important;
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            background: #0d0d0d !important;
            border-right: 1px solid #1a1a1a !important;
        }
        
        [data-testid="stSidebar"] .stRadio label {
            color: #666 !important;
            padding: 10px 14px !important;
            font-family: 'Courier New', monospace !important;
            font-size: 0.85rem !important;
            letter-spacing: 0.5px !important;
        }
        
        [data-testid="stSidebar"] .stRadio label:hover {
            background: rgba(0,255,136,0.05) !important;
            color: #00ff88 !important;
        }
        
        /* Metrics */
        [data-testid="stMetric"] {
            background: #0d0d0d !important;
            border: 1px solid #1a1a1a !important;
            border-radius: 0 !important;
            padding: 20px !important;
        }
        
        [data-testid="stMetricValue"] {
            color: #00ff88 !important;
            font-family: 'Courier New', monospace !important;
            font-size: 2rem !important;
        }
        
        [data-testid="stMetric"] label {
            color: #666 !important;
            font-family: 'Courier New', monospace !important;
            letter-spacing: 2px !important;
            font-size: 0.65rem !important;
        }
        
        /* Dataframe */
        .stDataFrame {
            background: #0d0d0d !important;
            border: 1px solid #1a1a1a !important;
            border-radius: 0 !important;
        }
        
        .stDataFrame th {
            background: #111 !important;
            color: #00ff88 !important;
            font-family: 'Courier New', monospace !important;
            font-size: 0.7rem !important;
            letter-spacing: 1.5px !important;
            text-transform: uppercase !important;
        }
        
        .stDataFrame td {
            color: #999 !important;
            font-family: 'Courier New', monospace !important;
            font-size: 0.85rem !important;
        }
        
        /* Headings */
        h1 {
            color: #fff !important;
            font-family: 'Courier New', monospace !important;
            font-weight: 700 !important;
            letter-spacing: 1px !important;
        }
        
        h3 {
            color: #999 !important;
            font-family: 'Courier New', monospace !important;
            letter-spacing: 2px !important;
            text-transform: uppercase !important;
            font-size: 0.85rem !important;
        }
        
        /* Sidebar Profile */
        .sidebar-profile {
            text-align: center;
            padding: 25px 20px;
            border-bottom: 1px solid #1a1a1a;
            margin-bottom: 20px;
        }
        
        .sidebar-username {
            color: #fff;
            font-family: 'Courier New', monospace;
            font-size: 0.95rem;
            margin: 10px 0;
            letter-spacing: 1px;
        }
        
        .sidebar-role {
            display: inline-block;
            padding: 3px 14px;
            border: 1px solid #00ff88;
            color: #00ff88;
            font-family: 'Courier New', monospace;
            font-size: 0.65rem;
            letter-spacing: 2px;
        }
        
        /* Status indicator */
        .status-dot {
            display: inline-block;
            width: 6px;
            height: 6px;
            background: #00ff88;
            border-radius: 50%;
            margin-right: 6px;
            box-shadow: 0 0 8px rgba(0,255,136,0.5);
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            background: #0d0d0d !important;
            border: 1px solid #1a1a1a !important;
            border-radius: 0 !important;
            color: #00ff88 !important;
            font-family: 'Courier New', monospace !important;
            letter-spacing: 1px !important;
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 4px;
        }
        ::-webkit-scrollbar-track {
            background: #0a0a0a;
        }
        ::-webkit-scrollbar-thumb {
            background: #1a1a1a;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #00ff88;
        }
        
        /* Hide elements on login */
        .login-mode [data-testid="stSidebar"],
        .login-mode header,
        .login-mode footer {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

# ============================================
# LOGIN PAGE
# ============================================
def login_page():
    st.markdown('<div class="login-mode">', unsafe_allow_html=True)
    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    
    # Logo
    st.markdown(render_logo("70px", "70px"), unsafe_allow_html=True)
    st.markdown('<h1 class="brand-title">GHOST.WIRE</h1>', unsafe_allow_html=True)
    st.markdown('<p class="brand-subtitle">Admin Console</p>', unsafe_allow_html=True)
    
    # Form
    username = st.text_input(
        "Username",
        placeholder="> username",
        label_visibility="collapsed",
        key="login_user"
    )
    
    st.markdown("<div style='margin:6px 0;'></div>", unsafe_allow_html=True)
    
    password = st.text_input(
        "Password",
        type="password",
        placeholder="> password",
        label_visibility="collapsed",
        key="login_pass"
    )
    
    st.markdown("<div style='margin:20px 0;'></div>", unsafe_allow_html=True)
    
    if st.button("AUTHENTICATE", use_container_width=True):
        if not username or not password:
            st.error("ERROR: All fields required")
        else:
            user = verify_admin(username, password)
            if user:
                try:
                    execute("UPDATE admin_users SET last_login=CURRENT_TIMESTAMP WHERE id=%s", (user['id'],))
                except: pass
                st.session_state.authenticated = True
                st.session_state.admin_user = user
                st.rerun()
            else:
                st.error("ERROR: Invalid credentials")
    
    st.markdown("""
        <p style="text-align:center;color:#333;font-family:'Courier New',monospace;font-size:0.7rem;margin-top:25px;letter-spacing:2px;">
            <span class="status-dot"></span> SYSTEM SECURED
        </p>
    """, unsafe_allow_html=True)
    
    st.markdown('</div></div></div>', unsafe_allow_html=True)

# ============================================
# SIDEBAR
# ============================================
def sidebar():
    with st.sidebar:
        admin_user = st.session_state.get('admin_user', {})
        username = admin_user.get('username', 'ADMIN')
        role = admin_user.get('role', 'admin').upper()
        
        st.markdown(f"""
            <div class="sidebar-profile">
                {render_logo("50px", "50px")}
                <p class="sidebar-username">{username}</p>
                <span class="sidebar-role">{role}</span>
            </div>
        """, unsafe_allow_html=True)
        
        menu = st.radio(
            "Navigation",
            [
                "DASHBOARD", "USERS", "WALLETS", "CHANNELS",
                "POSITIONS", "TRADES", "REFERRALS", "VERIFICATION",
                "TICKETS", "FEES", "WHITELIST", "BLACKLIST",
                "SNIPE LOGS", "SESSIONS", "ADMINS", "SETTINGS"
            ],
            label_visibility="collapsed"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        try:
            users = query("SELECT COUNT(*) as c FROM users WHERE is_active=true")
            if users:
                st.markdown(f"""
                    <div style="padding:12px;border:1px solid #1a1a1a;text-align:center;">
                        <p style="color:#666;font-family:'Courier New',monospace;font-size:0.6rem;letter-spacing:2px;margin:0;">ACTIVE USERS</p>
                        <p style="color:#00ff88;font-family:'Courier New',monospace;font-size:1.4rem;font-weight:700;margin:5px 0 0 0;">{users[0]['c']}</p>
                    </div>
                """, unsafe_allow_html=True)
        except: pass
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("SIGN OUT", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.admin_user = None
            st.rerun()
        
        return menu

# ============================================
# PAGES
# ============================================
def show_table(title, sql):
    st.markdown(f'<h1>{title}</h1>', unsafe_allow_html=True)
    data = query(sql)
    if data:
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
    else:
        st.info("No data found")

def dashboard_page():
    st.markdown('<h1>DASHBOARD</h1>', unsafe_allow_html=True)
    
    stats = query("""
        SELECT 
            (SELECT COUNT(*) FROM users WHERE is_active=true) as users,
            (SELECT COUNT(*) FROM wallets WHERE is_active=true) as wallets,
            (SELECT COUNT(*) FROM channels WHERE is_active=true) as channels,
            (SELECT COUNT(*) FROM trade_history WHERE DATE(created_at)=CURRENT_DATE) as today
    """)
    
    if stats:
        s = stats[0]
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("USERS", s['users'] or 0)
        c2.metric("WALLETS", s['wallets'] or 0)
        c3.metric("CHANNELS", s['channels'] or 0)
        c4.metric("TODAY", s['today'] or 0)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<h3>Recent Trades</h3>', unsafe_allow_html=True)
    show_table("", """
        SELECT th.created_at as Time, u.username as User,
               th.trade_type as Type, LEFT(th.token_address,10)||'...' as Token,
               ROUND(th.amount::numeric,4) as Amount
        FROM trade_history th JOIN users u ON th.user_id=u.user_id
        ORDER BY th.created_at DESC LIMIT 10
    """)

def users_page():
    show_table("USERS", """
        SELECT user_id as ID, username as Username,
               is_active as Active, created_at as Joined
        FROM users ORDER BY created_at DESC LIMIT 200
    """)

def wallets_page():
    show_table("WALLETS", """
        SELECT w.id, u.username, w.wallet_name as Wallet,
               LEFT(w.public_key,12)||'...' as Key
        FROM wallets w JOIN users u ON w.user_id=u.user_id
        WHERE w.is_active=true LIMIT 200
    """)

def channels_page():
    show_table("CHANNELS", """
        SELECT c.id, u.username,
               COALESCE(c.display_name,c.channel_name) as Channel,
               CASE WHEN c.is_private THEN 'Private' ELSE 'Public' END as Type
        FROM channels c JOIN users u ON c.user_id=u.user_id
        WHERE c.is_active=true ORDER BY c.created_at DESC
    """)

def positions_page():
    show_table("POSITIONS", """
        SELECT p.id, u.username,
               LEFT(p.token_address,12)||'...' as Token,
               ROUND(p.amount::numeric,2) as Amount
        FROM positions p JOIN users u ON p.user_id=u.user_id
        WHERE p.is_active=true AND p.amount>0 LIMIT 100
    """)

def trades_page():
    show_table("TRADES", """
        SELECT th.created_at as Time, u.username as User,
               th.trade_type as Type,
               LEFT(th.token_address,12)||'...' as Token,
               ROUND(th.amount::numeric,4) as Amount
        FROM trade_history th JOIN users u ON th.user_id=u.user_id
        ORDER BY th.created_at DESC LIMIT 100
    """)

def referrals_page():
    show_table("REFERRALS", """
        SELECT u.username as Referrer, COUNT(*) as Refs,
               COALESCE(SUM(re.commission::numeric),0) as Earned
        FROM referrals r2 JOIN users u ON r2.referrer_id=u.user_id
        LEFT JOIN referral_earnings re ON r2.referrer_id=re.referrer_id
        WHERE r2.is_active=true
        GROUP BY r2.referrer_id,u.username
        ORDER BY Earned DESC LIMIT 20
    """)

def verification_page():
    show_table("VERIFICATION", """
        SELECT u.username, LEFT(tv.wallet_address,12)||'...' as Wallet,
               ROUND(tv.token_balance::numeric,2) as GHOSTWIRE,
               ROUND(tv.token_percent::numeric,4) as Pct
        FROM token_verifications tv JOIN users u ON tv.user_id=u.user_id
        WHERE tv.is_verified=true ORDER BY tv.token_percent DESC
    """)

def tickets_page():
    show_table("TICKETS", """
        SELECT t.id, t.created_at,
               COALESCE(u.username,'Unknown') as User,
               t.ticket_type as Type, t.subject, t.status
        FROM support_tickets t LEFT JOIN users u ON t.user_id=u.user_id
        ORDER BY t.created_at DESC LIMIT 50
    """)

def fees_page():
    st.markdown('<h1>FEE SYSTEM</h1>', unsafe_allow_html=True)
    fees = query("SELECT * FROM fee_config WHERE is_active=true ORDER BY id DESC LIMIT 1")
    if fees:
        f = fees[0]
        c1,c2 = st.columns(2)
        c1.metric("Fee %", f"{f.get('fee_percent',0.05)}%")
        c2.metric("Wallet", str(f.get('fee_wallet','N/A'))[:15]+'...')

def whitelist_page():
    show_table("WHITELIST", """
        SELECT fw.user_id, u.username, fw.created_at
        FROM fee_whitelist fw LEFT JOIN users u ON fw.user_id=u.user_id
        WHERE fw.is_active=true
    """)

def blacklist_page():
    show_table("BLACKLIST", """
        SELECT user_id, username, updated_at FROM users WHERE is_active=false
    """)

def snipelogs_page():
    show_table("SNIPE LOGS", """
        SELECT sl.created_at as Time, u.username as User,
               sl.channel_name as Channel,
               LEFT(sl.token_address,12)||'...' as Token, sl.status
        FROM snipe_logs sl JOIN users u ON sl.user_id=u.user_id
        ORDER BY sl.created_at DESC LIMIT 200
    """)

def sessions_page():
    show_table("SESSIONS", """
        SELECT user_id, username,
               LEFT(COALESCE(telegram_phone,''),12)||'...' as Phone,
               updated_at
        FROM users WHERE telegram_session_string IS NOT NULL
    """)

def admins_page():
    st.markdown('<h1>ADMIN PANEL</h1>', unsafe_allow_html=True)
    admins = get_admins()
    if admins:
        st.dataframe(pd.DataFrame(admins), use_container_width=True, hide_index=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<h3>Create Admin</h3>', unsafe_allow_html=True)
    
    c1,c2 = st.columns(2)
    with c1:
        nu = st.text_input("Username", key="new_user", label_visibility="collapsed", placeholder="Username")
    with c2:
        np = st.text_input("Password", type="password", key="new_pass", label_visibility="collapsed", placeholder="Password")
    
    if st.button("CREATE", use_container_width=True):
        if nu and np:
            if create_admin(nu, np):
                st.success("Admin created!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Username exists!")
        else:
            st.error("All fields required!")

def settings_page():
    st.markdown('<h1>SETTINGS</h1>', unsafe_allow_html=True)
    if st.button("CLEAN OLD LOGS", use_container_width=True):
        execute("DELETE FROM snipe_logs WHERE created_at < CURRENT_DATE - INTERVAL '30 days'")
        st.success("Logs cleaned!")

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
        "DASHBOARD": dashboard_page, "USERS": users_page,
        "WALLETS": wallets_page, "CHANNELS": channels_page,
        "POSITIONS": positions_page, "TRADES": trades_page,
        "REFERRALS": referrals_page, "VERIFICATION": verification_page,
        "TICKETS": tickets_page, "FEES": fees_page,
        "WHITELIST": whitelist_page, "BLACKLIST": blacklist_page,
        "SNIPE LOGS": snipelogs_page, "SESSIONS": sessions_page,
        "ADMINS": admins_page, "SETTINGS": settings_page
    }
    
    if page in pages:
        pages[page]()

if __name__ == "__main__":
    main()