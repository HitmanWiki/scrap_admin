require('dotenv').config();
const express = require('express');
const { Pool } = require('@neondatabase/serverless');
const cors = require('cors');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const path = require('path');
const fs = require('fs');

const app = express();
const JWT_SECRET = process.env.JWT_SECRET || 'ghostwire-secret-key-2024';

// ============================================
// TABLE PRIMARY KEY MAPPING
// ============================================
const TABLE_PRIMARY_KEYS = {
    'users': 'user_id',
    'wallets': 'id',
    'channels': 'id',
    'positions': 'id',
    'trade_history': 'id',
    'referrals': 'id',
    'token_verifications': 'id',
    'support_tickets': 'id',
    'fee_config': 'id',
    'snipe_logs': 'id',
    'admin_users': 'id',
    'whitelist': 'id',
    'blacklist': 'id',
    'activity_logs': 'id',
    'fee_whitelist': 'id'
};

function getPrimaryKey(table) {
    return TABLE_PRIMARY_KEYS[table] || 'id';
}

// ============================================
// MIDDLEWARE
// ============================================
app.use(cors({
    origin: true,
    credentials: true
}));
app.use(express.json());

// Serve static files from public directory
const publicPath = path.join(__dirname, '..', 'public');
if (fs.existsSync(publicPath)) {
    app.use(express.static(publicPath));
}

// ============================================
// DATABASE
// ============================================
let pool;

function getPool() {
    if (!pool) {
        pool = new Pool({
            connectionString: process.env.DATABASE_URL
        });
    }
    return pool;
}

// Initialize database (called once on first request)
let dbInitialized = false;

async function initDB() {
    if (dbInitialized) return;
    
    const client = await getPool().connect();
    try {
        console.log('📦 Setting up database...');
        
        await client.query(`
            CREATE TABLE IF NOT EXISTS admin_users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT DEFAULT '',
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'admin',
                is_active BOOLEAN DEFAULT true,
                last_login TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        `);

        await client.query(`
            CREATE TABLE IF NOT EXISTS whitelist (
                id SERIAL PRIMARY KEY,
                wallet_address TEXT NOT NULL,
                label TEXT DEFAULT '',
                added_by INTEGER REFERENCES admin_users(id),
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        `);

        await client.query(`
            CREATE TABLE IF NOT EXISTS blacklist (
                id SERIAL PRIMARY KEY,
                telegram_id TEXT DEFAULT '',
                username TEXT DEFAULT '',
                reason TEXT DEFAULT '',
                added_by INTEGER REFERENCES admin_users(id),
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        `);

        await client.query(`
            CREATE TABLE IF NOT EXISTS activity_logs (
                id SERIAL PRIMARY KEY,
                admin_id INTEGER REFERENCES admin_users(id),
                action TEXT NOT NULL,
                table_name TEXT DEFAULT '',
                record_id INTEGER,
                details JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        `);

        const existingAdmin = await client.query('SELECT COUNT(*) as cnt FROM admin_users');
        if (existingAdmin.rows[0].cnt === 0) {
            const hashedPassword = await bcrypt.hash('GhostWire@2026', 10);
            await client.query(
                'INSERT INTO admin_users (username, email, password_hash, role) VALUES ($1, $2, $3, $4)',
                ['admin', 'admin@ghostwire.io', hashedPassword, 'superadmin']
            );
            console.log('✅ Default admin created');
        }

        dbInitialized = true;
        console.log('✅ Database setup complete');
    } catch (error) {
        console.error('❌ Setup error:', error.message);
    } finally {
        client.release();
    }
}

// Auto-init middleware
app.use(async (req, res, next) => {
    try {
        await initDB();
    } catch (e) {
        console.error('DB init error:', e);
    }
    next();
});

// ============================================
// AUTH MIDDLEWARE
// ============================================
function authenticateToken(req, res, next) {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];
    
    if (!token) {
        return res.status(401).json({ error: 'Access denied - no token' });
    }
    
    try {
        const user = jwt.verify(token, JWT_SECRET);
        req.user = user;
        next();
    } catch (err) {
        return res.status(403).json({ error: 'Invalid or expired token' });
    }
}

// ============================================
// AUTH ROUTES
// ============================================
app.post('/api/auth/login', async (req, res) => {
    try {
        const { username, password } = req.body;
        
        if (!username || !password) {
            return res.status(400).json({ error: 'Username and password required' });
        }
        
        const result = await getPool().query(
            'SELECT * FROM admin_users WHERE LOWER(username) = LOWER($1) AND is_active = true',
            [username]
        );
        
        if (result.rows.length === 0) {
            return res.status(401).json({ error: 'Invalid credentials' });
        }
        
        const user = result.rows[0];
        const validPassword = await bcrypt.compare(password, user.password_hash);
        
        if (!validPassword) {
            return res.status(401).json({ error: 'Invalid credentials' });
        }
        
        await getPool().query('UPDATE admin_users SET last_login = CURRENT_TIMESTAMP WHERE id = $1', [user.id]);
        
        const token = jwt.sign(
            { id: user.id, username: user.username, role: user.role },
            JWT_SECRET,
            { expiresIn: '24h' }
        );
        
        return res.json({
            token,
            user: {
                id: user.id,
                username: user.username,
                email: user.email || '',
                role: user.role,
                last_login: user.last_login
            }
        });
    } catch (error) {
        console.error('Login error:', error);
        return res.status(500).json({ error: 'Server error' });
    }
});

app.get('/api/auth/profile', authenticateToken, async (req, res) => {
    try {
        const result = await getPool().query(
            'SELECT id, username, email, role, last_login, created_at FROM admin_users WHERE id = $1',
            [req.user.id]
        );
        if (result.rows.length === 0) return res.status(404).json({ error: 'User not found' });
        return res.json(result.rows[0]);
    } catch (error) {
        return res.status(500).json({ error: 'Server error' });
    }
});

app.put('/api/auth/profile', authenticateToken, async (req, res) => {
    try {
        const { email } = req.body;
        await getPool().query('UPDATE admin_users SET email = $1 WHERE id = $2', [email || '', req.user.id]);
        return res.json({ message: 'Profile updated' });
    } catch (error) {
        return res.status(500).json({ error: 'Server error' });
    }
});

app.put('/api/auth/change-password', authenticateToken, async (req, res) => {
    try {
        const { current_password, new_password } = req.body;
        if (!current_password || !new_password) return res.status(400).json({ error: 'Both passwords required' });
        
        const result = await getPool().query('SELECT password_hash FROM admin_users WHERE id = $1', [req.user.id]);
        if (result.rows.length === 0) return res.status(404).json({ error: 'User not found' });
        
        const valid = await bcrypt.compare(current_password, result.rows[0].password_hash);
        if (!valid) return res.status(400).json({ error: 'Current password is incorrect' });
        
        const hash = await bcrypt.hash(new_password, 10);
        await getPool().query('UPDATE admin_users SET password_hash = $1 WHERE id = $2', [hash, req.user.id]);
        return res.json({ message: 'Password changed' });
    } catch (error) {
        return res.status(500).json({ error: 'Server error' });
    }
});

// ============================================
// ADMIN USERS CRUD
// ============================================
app.get('/api/admins', authenticateToken, async (req, res) => {
    try {
        const result = await getPool().query(
            'SELECT id, username, email, role, is_active, last_login, created_at FROM admin_users ORDER BY created_at DESC'
        );
        return res.json(result.rows);
    } catch (error) {
        return res.status(500).json({ error: 'Server error' });
    }
});

app.post('/api/admins', authenticateToken, async (req, res) => {
    try {
        // Only superadmin can create admins
        if (req.user.role !== 'superadmin') {
            return res.status(403).json({ error: 'Only superadmins can create admin users' });
        }
        
        const { username, email, password, role } = req.body;
        if (!username || !password) return res.status(400).json({ error: 'Username and password required' });
        
        const hash = await bcrypt.hash(password, 10);
        const result = await getPool().query(
            'INSERT INTO admin_users (username, email, password_hash, role) VALUES ($1, $2, $3, $4) RETURNING id, username, email, role, is_active, created_at',
            [username, email || '', hash, role || 'admin']
        );
        
        await getPool().query(
            'INSERT INTO activity_logs (admin_id, action, table_name, record_id, details) VALUES ($1, $2, $3, $4, $5)',
            [req.user.id, 'CREATE', 'admin_users', result.rows[0].id, JSON.stringify({ username, role })]
        );
        
        return res.status(201).json(result.rows[0]);
    } catch (error) {
        if (error.code === '23505') return res.status(400).json({ error: 'Username already exists' });
        return res.status(500).json({ error: 'Server error' });
    }
});

app.put('/api/admins/:id', authenticateToken, async (req, res) => {
    try {
        const { id } = req.params;
        const { email, role, is_active } = req.body;
        
        // Only superadmin can change roles
        if (role && req.user.role !== 'superadmin') {
            return res.status(403).json({ error: 'Only superadmins can change roles' });
        }
        
        const result = await getPool().query(
            'UPDATE admin_users SET email = $1, role = COALESCE($2, role), is_active = $3 WHERE id = $4 RETURNING id, username, email, role, is_active',
            [email || '', role, is_active, id]
        );
        
        if (result.rows.length === 0) return res.status(404).json({ error: 'Admin not found' });
        return res.json(result.rows[0]);
    } catch (error) {
        return res.status(500).json({ error: 'Server error' });
    }
});

app.delete('/api/admins/:id', authenticateToken, async (req, res) => {
    try {
        // Only superadmin can delete admins
        if (req.user.role !== 'superadmin') {
            return res.status(403).json({ error: 'Only superadmins can delete admin users' });
        }
        
        const { id } = req.params;
        if (parseInt(id) === req.user.id) return res.status(400).json({ error: 'Cannot delete yourself' });
        
        const result = await getPool().query('DELETE FROM admin_users WHERE id = $1 RETURNING id', [id]);
        if (result.rows.length === 0) return res.status(404).json({ error: 'Admin not found' });
        
        return res.json({ message: 'Admin deleted' });
    } catch (error) {
        return res.status(500).json({ error: 'Server error' });
    }
});

// ============================================
// WHITELIST CRUD
// ============================================
app.get('/api/whitelist', authenticateToken, async (req, res) => {
    try {
        const result = await getPool().query(`
            SELECT w.*, a.username as added_by_username 
            FROM whitelist w LEFT JOIN admin_users a ON w.added_by = a.id 
            WHERE w.is_active = true ORDER BY w.created_at DESC
        `);
        return res.json(result.rows);
    } catch (error) {
        return res.status(500).json({ error: 'Server error' });
    }
});

app.post('/api/whitelist', authenticateToken, async (req, res) => {
    try {
        const { wallet_address, label } = req.body;
        if (!wallet_address) return res.status(400).json({ error: 'Wallet address required' });
        
        const result = await getPool().query(
            'INSERT INTO whitelist (wallet_address, label, added_by) VALUES ($1, $2, $3) RETURNING *',
            [wallet_address, label || '', req.user.id]
        );
        
        await getPool().query(
            'INSERT INTO activity_logs (admin_id, action, table_name, record_id, details) VALUES ($1, $2, $3, $4, $5)',
            [req.user.id, 'CREATE', 'whitelist', result.rows[0].id, JSON.stringify({ wallet_address })]
        );
        
        return res.status(201).json(result.rows[0]);
    } catch (error) {
        return res.status(500).json({ error: 'Server error' });
    }
});

app.put('/api/whitelist/:id', authenticateToken, async (req, res) => {
    try {
        const { id } = req.params;
        const { wallet_address, label, is_active } = req.body;
        
        const result = await getPool().query(
            'UPDATE whitelist SET wallet_address = $1, label = $2, is_active = $3 WHERE id = $4 RETURNING *',
            [wallet_address, label || '', is_active, id]
        );
        
        if (result.rows.length === 0) return res.status(404).json({ error: 'Not found' });
        return res.json(result.rows[0]);
    } catch (error) {
        return res.status(500).json({ error: 'Server error' });
    }
});

app.delete('/api/whitelist/:id', authenticateToken, async (req, res) => {
    try {
        await getPool().query('UPDATE whitelist SET is_active = false WHERE id = $1', [req.params.id]);
        return res.json({ message: 'Removed from whitelist' });
    } catch (error) {
        return res.status(500).json({ error: 'Server error' });
    }
});

// ============================================
// BLACKLIST CRUD
// ============================================
app.get('/api/blacklist', authenticateToken, async (req, res) => {
    try {
        const result = await getPool().query(`
            SELECT b.*, a.username as added_by_username 
            FROM blacklist b LEFT JOIN admin_users a ON b.added_by = a.id 
            WHERE b.is_active = true ORDER BY b.created_at DESC
        `);
        return res.json(result.rows);
    } catch (error) {
        return res.status(500).json({ error: 'Server error' });
    }
});

app.post('/api/blacklist', authenticateToken, async (req, res) => {
    try {
        const { telegram_id, username, reason } = req.body;
        const result = await getPool().query(
            'INSERT INTO blacklist (telegram_id, username, reason, added_by) VALUES ($1, $2, $3, $4) RETURNING *',
            [telegram_id || '', username || '', reason || '', req.user.id]
        );
        
        await getPool().query(
            'INSERT INTO activity_logs (admin_id, action, table_name, record_id, details) VALUES ($1, $2, $3, $4, $5)',
            [req.user.id, 'CREATE', 'blacklist', result.rows[0].id, JSON.stringify({ telegram_id, username })]
        );
        
        return res.status(201).json(result.rows[0]);
    } catch (error) {
        return res.status(500).json({ error: 'Server error' });
    }
});

app.put('/api/blacklist/:id', authenticateToken, async (req, res) => {
    try {
        const { id } = req.params;
        const { telegram_id, username, reason, is_active } = req.body;
        
        const result = await getPool().query(
            'UPDATE blacklist SET telegram_id = $1, username = $2, reason = $3, is_active = $4 WHERE id = $5 RETURNING *',
            [telegram_id || '', username || '', reason || '', is_active, id]
        );
        
        if (result.rows.length === 0) return res.status(404).json({ error: 'Not found' });
        return res.json(result.rows[0]);
    } catch (error) {
        return res.status(500).json({ error: 'Server error' });
    }
});

app.delete('/api/blacklist/:id', authenticateToken, async (req, res) => {
    try {
        await getPool().query('UPDATE blacklist SET is_active = false WHERE id = $1', [req.params.id]);
        return res.json({ message: 'Removed from blacklist' });
    } catch (error) {
        return res.status(500).json({ error: 'Server error' });
    }
});

// ============================================
// GENERIC QUERY (SELECT ONLY)
// ============================================
app.post('/api/query', authenticateToken, async (req, res) => {
    try {
        const { sql } = req.body;
        if (!sql) return res.status(400).json({ error: 'SQL query required' });
        
        const trimmedSQL = sql.trim().toUpperCase();
        if (!trimmedSQL.startsWith('SELECT')) return res.status(403).json({ error: 'Only SELECT queries allowed' });
        
        const result = await getPool().query(sql);
        return res.json({ rows: result.rows, rowCount: result.rowCount });
    } catch (error) {
        return res.status(500).json({ error: error.message });
    }
});

// ============================================
// GENERIC RECORD CRUD
// ============================================
app.get('/api/records/:table/:id', authenticateToken, async (req, res) => {
    try {
        const { table, id } = req.params;
        const pk = getPrimaryKey(table);
        const result = await getPool().query(`SELECT * FROM ${table} WHERE ${pk} = $1`, [id]);
        if (result.rows.length === 0) return res.status(404).json({ error: 'Record not found' });
        return res.json(result.rows[0]);
    } catch (error) {
        return res.status(500).json({ error: error.message });
    }
});

app.put('/api/records/:table/:id', authenticateToken, async (req, res) => {
    try {
        const { table, id } = req.params;
        const updates = req.body;
        const pk = getPrimaryKey(table);
        
        const keys = Object.keys(updates);
        if (keys.length === 0) return res.status(400).json({ error: 'No fields to update' });
        
        const setClauses = keys.map((k, i) => `${k} = $${i + 1}`);
        const values = keys.map(k => updates[k]);
        
        const query = `UPDATE ${table} SET ${setClauses.join(', ')} WHERE ${pk} = $${values.length + 1} RETURNING *`;
        const result = await getPool().query(query, [...values, id]);
        
        if (result.rows.length === 0) return res.status(404).json({ error: 'Record not found' });
        
        await getPool().query(
            'INSERT INTO activity_logs (admin_id, action, table_name, record_id, details) VALUES ($1, $2, $3, $4, $5)',
            [req.user.id, 'UPDATE', table, id, JSON.stringify(updates)]
        );
        
        return res.json(result.rows[0]);
    } catch (error) {
        return res.status(500).json({ error: error.message });
    }
});

app.delete('/api/records/:table/:id', authenticateToken, async (req, res) => {
    try {
        const { table, id } = req.params;
        const pk = getPrimaryKey(table);
        const result = await getPool().query(`DELETE FROM ${table} WHERE ${pk} = $1 RETURNING ${pk}`, [id]);
        if (result.rows.length === 0) return res.status(404).json({ error: 'Record not found' });
        
        await getPool().query(
            'INSERT INTO activity_logs (admin_id, action, table_name, record_id) VALUES ($1, $2, $3, $4)',
            [req.user.id, 'DELETE', table, id]
        );
        
        return res.json({ message: 'Record deleted' });
    } catch (error) {
        return res.status(500).json({ error: error.message });
    }
});

// ============================================
// DASHBOARD DATA
// ============================================
app.get('/api/dashboard/stats', authenticateToken, async (req, res) => {
    try {
        const result = await getPool().query(`SELECT 
            (SELECT COUNT(*) FROM users WHERE is_active=true) as total_users,
            (SELECT COUNT(*) FROM wallets WHERE is_active=true) as total_wallets,
            (SELECT COUNT(*) FROM positions WHERE is_active=true AND amount>0) as open_positions,
            (SELECT COUNT(*) FROM channels WHERE is_active=true) as active_channels,
            (SELECT COUNT(*) FROM trade_history WHERE DATE(created_at)=CURRENT_DATE) as today_trades,
            (SELECT COUNT(*) FROM whitelist WHERE is_active=true) as whitelist_count,
            (SELECT COUNT(*) FROM blacklist WHERE is_active=true) as blacklist_count,
            (SELECT COUNT(*) FROM admin_users WHERE is_active=true) as admin_count`);
        return res.json(result.rows[0] || {});
    } catch (error) {
        return res.json({ total_users:0,total_wallets:0,open_positions:0,active_channels:0,today_trades:0,whitelist_count:0,blacklist_count:0,admin_count:1 });
    }
});

app.get('/api/dashboard/trade-volume', authenticateToken, async (req, res) => {
    try {
        const result = await getPool().query(`SELECT TO_CHAR(DATE(created_at),'Dy') as day, DATE(created_at) as date, COUNT(*)::int as trade_count FROM trade_history WHERE created_at >= CURRENT_DATE - INTERVAL '7 days' GROUP BY DATE(created_at), TO_CHAR(DATE(created_at),'Dy') ORDER BY DATE(created_at)`);
        const days=[],counts=[],dayNames=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
        for(let i=6;i>=0;i--){const d=new Date();d.setDate(d.getDate()-i);const ds=d.toISOString().split('T')[0],dn=dayNames[d.getDay()],f=result.rows.find(r=>new Date(r.date).toISOString().split('T')[0]===ds);days.push(dn);counts.push(f?f.trade_count:0)}
        return res.json({days,counts});
    } catch(e) { return res.json({days:['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],counts:[0,0,0,0,0,0,0]}); }
});

app.get('/api/dashboard/user-registrations', authenticateToken, async (req, res) => {
    try {
        const result = await getPool().query(`SELECT TO_CHAR(DATE(created_at),'Dy') as day, DATE(created_at) as date, COUNT(*)::int as user_count FROM users WHERE created_at >= CURRENT_DATE - INTERVAL '7 days' GROUP BY DATE(created_at), TO_CHAR(DATE(created_at),'Dy') ORDER BY DATE(created_at)`);
        const days=[],counts=[],dayNames=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
        for(let i=6;i>=0;i--){const d=new Date();d.setDate(d.getDate()-i);const ds=d.toISOString().split('T')[0],dn=dayNames[d.getDay()],f=result.rows.find(r=>new Date(r.date).toISOString().split('T')[0]===ds);days.push(dn);counts.push(f?f.user_count:0)}
        return res.json({days,counts});
    } catch(e) { return res.json({days:['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],counts:[0,0,0,0,0,0,0]}); }
});

app.get('/api/dashboard/recent-trades', authenticateToken, async (req, res) => {
    try {
        const result = await getPool().query(`SELECT th.created_at, u.username, th.trade_type, LEFT(th.token_address,12)||'...' as token, ROUND(th.amount::numeric,4) as amount FROM trade_history th JOIN users u ON th.user_id=u.user_id ORDER BY th.created_at DESC LIMIT 10`);
        return res.json(result.rows);
    } catch(e) { return res.json([]); }
});

app.get('/api/logs', authenticateToken, async (req, res) => {
    try {
        const result = await getPool().query('SELECT al.*, a.username FROM activity_logs al LEFT JOIN admin_users a ON al.admin_id=a.id ORDER BY al.created_at DESC LIMIT 100');
        return res.json(result.rows);
    } catch(e) { return res.json([]); }
});

app.get('/api/health', (req, res) => {
    return res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// ============================================
// FRONTEND (MUST BE LAST)
// ============================================
app.get('*', (req, res) => {
    if (req.path.startsWith('/api')) {
        return res.status(404).json({ error: 'API route not found' });
    }
    const indexPath = path.join(__dirname, '..', 'public', 'index.html');
    if (fs.existsSync(indexPath)) {
        return res.sendFile(indexPath);
    }
    return res.status(200).send('GHOSTWIRE Admin API is running');
});

// ============================================
// EXPORT FOR VERCEL
// ============================================
module.exports = app;