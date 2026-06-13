"""
Solana Sniper Bot - Professional Admin Dashboard
Streamlit + Neon PostgreSQL
"""

import streamlit as st
import pandas as pd
import psycopg2
import psycopg2.extras
import os
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

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
# DATABASE CONNECTION
# ============================================
def get_db_connection():
    try:
        conn = psycopg2.connect(
            os.getenv('DATABASE_URL'),
            sslmode='require',
            connect_timeout=10
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
    finally:
        conn.close()

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
    finally:
        conn.close()

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
                <div style="text-align: center; padding: 40px 0;">
                    <div style="width: 70px; height: 70px; background: linear-gradient(135deg, #6719ff, #8a4dff); border-radius: 18px; margin: 0 auto; display: flex; align-items: center; justify-content: center;">
                        <span style="font-size: 36px;">👻</span>
                    </div>
                    <h1 style="margin-top: 24px; background: linear-gradient(135deg, #6719ff, #8a4dff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">GHOSTwire</h1>
                    <p style="color: #6e6e80; margin-bottom: 32px;">Admin Dashboard</p>
                </div>
            """, unsafe_allow_html=True)
            
            password = st.text_input("Password", type="password", placeholder="Enter admin password")
            
            if st.button("Login", use_container_width=True):
                admin_pass = os.getenv('ADMIN_PASSWORD', 'GhostWire@2026')
                if password == admin_pass:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Wrong password!")
        return False
    return True

# ============================================
# SIDEBAR
# ============================================
def sidebar():
    with st.sidebar:
        st.markdown("""
            <div style="text-align: center; padding: 20px 0;">
                <div style="width: 50px; height: 50px; background: linear-gradient(135deg, #6719ff, #8a4dff); border-radius: 12px; margin: 0 auto; display: flex; align-items: center; justify-content: center;">
                    <span style="font-size: 28px;">👻</span>
                </div>
                <h3 style="margin-top: 12px;">GHOSTwire</h3>
                <p style="color: #6e6e80; font-size: 12px;">Admin Panel</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        page = st.radio(
            "Navigation",
            ["Dashboard", "Users", "Wallets", "Channels", "Positions", "Trades", "Referrals", "Fees", "Whitelist", "Blacklist", "Snipe Logs", "Sessions", "Settings"],
            index=0
        )
        
        st.markdown("---")
        
        try:
            stats = query("SELECT COUNT(*) as count FROM users WHERE is_active = true")
            if stats:
                st.caption(f"Active Users: {stats[0]['count']}")
        except:
            pass
        
        st.caption(f"{datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        if st.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
        
        return page

# ============================================
# DASHBOARD PAGE
# ============================================
def dashboard_page():
    st.title("Dashboard")
    st.caption("Real-time statistics from your sniper bot")
    
    st.markdown("---")
    
    # Stats row 1
    stats = query("""
        SELECT 
            (SELECT COUNT(*) FROM users WHERE is_active = true) as total_users,
            (SELECT COUNT(*) FROM wallets WHERE is_active = true) as total_wallets,
            (SELECT COUNT(*) FROM positions WHERE is_active = true AND amount > 0) as active_positions,
            (SELECT COUNT(*) FROM channels WHERE is_active = true) as active_channels
    """)
    
    if stats:
        s = stats[0]
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Active Users", s.get('total_users', 0))
        with c2:
            st.metric("Total Wallets", s.get('total_wallets', 0))
        with c3:
            st.metric("Active Positions", s.get('active_positions', 0))
        with c4:
            st.metric("Active Channels", s.get('active_channels', 0))
    
    # Stats row 2
    stats2 = query("""
        SELECT 
            (SELECT COUNT(*) FROM trade_history) as total_trades,
            (SELECT COUNT(*) FROM trade_history WHERE DATE(created_at) = CURRENT_DATE) as today_trades,
            (SELECT COUNT(*) FROM referrals WHERE is_active = true) as total_referrals,
            (SELECT COALESCE(SUM(commission), 0) FROM referral_earnings) as total_commission
    """)
    
    if stats2:
        s = stats2[0]
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Total Trades", s.get('total_trades', 0))
        with c2:
            st.metric("Today's Trades", s.get('today_trades', 0))
        with c3:
            st.metric("Total Referrals", s.get('total_referrals', 0))
        with c4:
            st.metric("Total Commission", f"{s.get('total_commission', 0):.4f} SOL")
    
    st.markdown("---")
    
    # Charts
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Trades (Last 7 Days)")
        trades = query("""
            SELECT DATE(created_at) as date, 
                   COUNT(*) as total,
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
            fig.add_trace(go.Bar(x=df['date'], y=df['buys'], name='Buys', marker_color='#4ecca3'))
            fig.add_trace(go.Bar(x=df['date'], y=df['sells'], name='Sells', marker_color='#e94560'))
            fig.update_layout(
                height=350,
                margin=dict(l=0, r=0, t=30, b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(gridcolor='#2a2a40', tickangle=45),
                yaxis=dict(gridcolor='#2a2a40')
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No trades in last 7 days")
    
    with c2:
        st.subheader("New Users (Last 7 Days)")
        users = query("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM users 
            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
        if users:
            df = pd.DataFrame(users)
            fig = px.line(df, x='date', y='count', markers=True, color_discrete_sequence=['#6719ff'])
            fig.update_layout(
                height=350,
                margin=dict(l=0, r=0, t=30, b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(gridcolor='#2a2a40', tickangle=45),
                yaxis=dict(gridcolor='#2a2a40')
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No new users in last 7 days")
    
    # Recent trades
    st.markdown("---")
    st.subheader("Recent Trades")
    recent = query("""
        SELECT th.created_at, u.username, th.trade_type, th.token_address, th.amount, th.price
        FROM trade_history th
        JOIN users u ON th.user_id = u.user_id
        ORDER BY th.created_at DESC 
        LIMIT 10
    """)
    if recent:
        df = pd.DataFrame(recent)
        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        st.dataframe(df, use_container_width=True)

# ============================================
# USERS PAGE
# ============================================
def users_page():
    st.title("User Management")
    
    search = st.text_input("Search by username or ID", placeholder="Enter username or user ID")
    
    users = query("""
        SELECT u.user_id, u.username, u.is_active, u.created_at,
            (SELECT COUNT(*) FROM wallets WHERE user_id = u.user_id AND is_active = true) as wallets,
            (SELECT COUNT(*) FROM trade_history WHERE user_id = u.user_id) as trades,
            (SELECT COALESCE(SUM(commission), 0) FROM referral_earnings WHERE referrer_id = u.user_id) as ref_earned
        FROM users u
        ORDER BY u.created_at DESC
        LIMIT 200
    """)
    
    if users:
        if search:
            users = [u for u in users if search.lower() in u.get('username', '').lower() or search in str(u.get('user_id', ''))]
        
        df = pd.DataFrame(users)
        st.dataframe(df, use_container_width=True)
    
    st.markdown("---")
    st.subheader("User Actions")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        user_id = st.number_input("User ID", min_value=1, step=1)
    with c2:
        action = st.selectbox("Action", ["Whitelist", "Blacklist", "Activate", "Deactivate"])
    with c3:
        if st.button("Execute"):
            if action == "Whitelist":
                execute("INSERT INTO fee_whitelist (user_id) VALUES (%s) ON CONFLICT DO NOTHING", (user_id,))
                st.success(f"User {user_id} whitelisted")
            elif action == "Blacklist":
                execute("UPDATE users SET is_active = false WHERE user_id = %s", (user_id,))
                st.success(f"User {user_id} blacklisted")
            elif action == "Activate":
                execute("UPDATE users SET is_active = true WHERE user_id = %s", (user_id,))
                st.success(f"User {user_id} activated")
            elif action == "Deactivate":
                execute("UPDATE users SET is_active = false WHERE user_id = %s", (user_id,))
                st.success(f"User {user_id} deactivated")
            st.rerun()

# ============================================
# WALLETS PAGE
# ============================================
def wallets_page():
    st.title("Wallet Management")
    
    wallets = query("""
        SELECT w.id, w.user_id, u.username, w.wallet_name, w.wallet_number, w.public_key, w.default_buy_amount, w.created_at
        FROM wallets w
        JOIN users u ON w.user_id = u.user_id
        WHERE w.is_active = true
        ORDER BY w.created_at DESC
        LIMIT 200
    """)
    
    if wallets:
        df = pd.DataFrame(wallets)
        st.dataframe(df, use_container_width=True)

# ============================================
# CHANNELS PAGE
# ============================================
def channels_page():
    st.title("Channel Monitoring")
    
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
            st.metric("Total Channels", s.get('total', 0))
        with c2:
            st.metric("Public", s.get('public', 0))
        with c3:
            st.metric("Private", s.get('private', 0))
    
    st.markdown("---")
    
    channels = query("""
        SELECT c.id, c.user_id, u.username, c.channel_name, c.is_private, c.signal_count, c.created_at
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
    st.title("Active Positions")
    
    positions = query("""
        SELECT p.id, p.user_id, u.username, p.token_address, p.token_symbol, p.amount, p.entry_price, p.created_at
        FROM positions p
        JOIN users u ON p.user_id = u.user_id
        WHERE p.is_active = true AND p.amount > 0
        ORDER BY p.created_at DESC
        LIMIT 100
    """)
    
    if positions:
        df = pd.DataFrame(positions)
        st.dataframe(df, use_container_width=True)

# ============================================
# TRADES PAGE
# ============================================
def trades_page():
    st.title("Trade History")
    
    c1, c2 = st.columns(2)
    with c1:
        trade_type = st.selectbox("Type", ["All", "buy", "sell", "auto-sell"])
    with c2:
        limit = st.selectbox("Limit", [50, 100, 200, 500], index=1)
    
    type_filter = "" if trade_type == "All" else f"AND th.trade_type = '{trade_type}'"
    
    trades = query(f"""
        SELECT th.created_at, u.username, th.trade_type, th.token_address, th.amount, th.price, th.txid
        FROM trade_history th
        JOIN users u ON th.user_id = u.user_id
        WHERE 1=1 {type_filter}
        ORDER BY th.created_at DESC
        LIMIT {limit}
    """)
    
    if trades:
        df = pd.DataFrame(trades)
        st.dataframe(df, use_container_width=True)
        
        csv = df.to_csv(index=False)
        st.download_button("Download CSV", csv, "trades.csv", "text/csv")

# ============================================
# REFERRALS PAGE
# ============================================
def referrals_page():
    st.title("Referral System")
    
    st.subheader("Top Referrers")
    top = query("""
        SELECT r.referrer_id, u.username, COUNT(*) as referrals, COALESCE(SUM(re.commission), 0) as earned
        FROM referrals r
        JOIN users u ON r.referrer_id = u.user_id
        LEFT JOIN referral_earnings re ON r.referrer_id = re.referrer_id
        WHERE r.is_active = true
        GROUP BY r.referrer_id, u.username
        ORDER BY earned DESC
        LIMIT 20
    """)
    
    if top:
        df = pd.DataFrame(top)
        st.dataframe(df, use_container_width=True)

# ============================================
# FEES PAGE
# ============================================
def fees_page():
    st.title("Fee Configuration")
    
    current = query("SELECT * FROM fee_config WHERE is_active = true ORDER BY id DESC LIMIT 1")
    
    if current:
        c = current[0]
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Current Fee", f"{c.get('fee_percent', 0)}%")
            wallet = c.get('fee_wallet', 'Not Set')
            st.metric("Fee Wallet", wallet[:30] + "..." if wallet and wallet != 'Not Set' else "Not Set")
        
        with c2:
            new_fee = st.number_input("Update Fee %", min_value=0.0, max_value=100.0, value=float(c.get('fee_percent', 0.05)), step=0.05)
            if st.button("Save"):
                execute("INSERT INTO fee_config (fee_percent, is_active) VALUES (%s, true)", (new_fee,))
                st.success(f"Fee updated to {new_fee}%")
                st.rerun()

# ============================================
# WHITELIST PAGE
# ============================================
def whitelist_page():
    st.title("Whitelist")
    
    whitelist = query("""
        SELECT fw.user_id, u.username, fw.created_at
        FROM fee_whitelist fw
        LEFT JOIN users u ON fw.user_id = u.user_id
        WHERE fw.is_active = true
        ORDER BY fw.created_at DESC
    """)
    
    if whitelist:
        df = pd.DataFrame(whitelist)
        st.dataframe(df, use_container_width=True)
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        add_id = st.number_input("Add User ID", min_value=1, step=1)
        if st.button("Add to Whitelist"):
            execute("INSERT INTO fee_whitelist (user_id) VALUES (%s) ON CONFLICT DO NOTHING", (add_id,))
            st.success(f"User {add_id} whitelisted")
            st.rerun()
    with c2:
        remove_id = st.number_input("Remove User ID", min_value=1, step=1)
        if st.button("Remove from Whitelist"):
            execute("UPDATE fee_whitelist SET is_active = false WHERE user_id = %s", (remove_id,))
            st.success(f"User {remove_id} removed")
            st.rerun()

# ============================================
# BLACKLIST PAGE
# ============================================
def blacklist_page():
    st.title("Blacklisted Users")
    
    blacklist = query("""
        SELECT user_id, username, updated_at
        FROM users
        WHERE is_active = false
        ORDER BY updated_at DESC
    """)
    
    if blacklist:
        df = pd.DataFrame(blacklist)
        st.dataframe(df, use_container_width=True)
        
        st.markdown("---")
        reactivate_id = st.number_input("Reactivate User ID", min_value=1, step=1)
        if st.button("Reactivate"):
            execute("UPDATE users SET is_active = true WHERE user_id = %s", (reactivate_id,))
            st.success(f"User {reactivate_id} reactivated")
            st.rerun()
    else:
        st.info("No blacklisted users")

# ============================================
# SNIPE LOGS PAGE
# ============================================
def snipelogs_page():
    st.title("Snipe Logs")
    
    logs = query("""
        SELECT sl.created_at, u.username, sl.channel_name, sl.token_address, sl.status, sl.error_message
        FROM snipe_logs sl
        JOIN users u ON sl.user_id = u.user_id
        ORDER BY sl.created_at DESC
        LIMIT 100
    """)
    
    if logs:
        df = pd.DataFrame(logs)
        st.dataframe(df, use_container_width=True)

# ============================================
# SESSIONS PAGE
# ============================================
def sessions_page():
    st.title("Active Sessions")
    
    sessions = query("""
        SELECT user_id, username, telegram_api_id, telegram_phone, updated_at
        FROM users
        WHERE telegram_session_string IS NOT NULL
        ORDER BY updated_at DESC
    """)
    
    if sessions:
        df = pd.DataFrame(sessions)
        st.dataframe(df, use_container_width=True)

# ============================================
# SETTINGS PAGE
# ============================================
def settings_page():
    st.title("System Settings")
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Database Stats")
        stats = query("""
            SELECT 
                (SELECT COUNT(*) FROM users) as users,
                (SELECT COUNT(*) FROM wallets) as wallets,
                (SELECT COUNT(*) FROM positions) as positions,
                (SELECT COUNT(*) FROM channels) as channels
        """)
        if stats:
            s = stats[0]
            for k, v in s.items():
                st.metric(k.title(), v)
    
    with c2:
        st.subheader("Cleanup")
        if st.button("Clean Old Snipe Logs (>30 days)"):
            execute("DELETE FROM snipe_logs WHERE created_at < CURRENT_DATE - INTERVAL '30 days'")
            st.success("Old logs cleaned!")
        
        if st.button("Reset Daily Trades"):
            execute("UPDATE users SET daily_trades = 0")
            st.success("Daily trades reset!")

# ============================================
# MAIN
# ============================================
def main():
    if not check_password():
        return
    
    page = sidebar()
    
    if page == "Dashboard":
        dashboard_page()
    elif page == "Users":
        users_page()
    elif page == "Wallets":
        wallets_page()
    elif page == "Channels":
        channels_page()
    elif page == "Positions":
        positions_page()
    elif page == "Trades":
        trades_page()
    elif page == "Referrals":
        referrals_page()
    elif page == "Fees":
        fees_page()
    elif page == "Whitelist":
        whitelist_page()
    elif page == "Blacklist":
        blacklist_page()
    elif page == "Snipe Logs":
        snipelogs_page()
    elif page == "Sessions":
        sessions_page()
    elif page == "Settings":
        settings_page()

if __name__ == "__main__":
    main()