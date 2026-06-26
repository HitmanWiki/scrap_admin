const { Pool } = require('@neondatabase/serverless');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const path = require('path');
const fs = require('fs');

// ============================================
// CONFIG
// ============================================
const JWT_SECRET = process.env.JWT_SECRET || 'ghostwire-admin-secret-key-2024';

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
    'activity_logs': 'id'
};

function getPrimaryKey(table) {
    return TABLE_PRIMARY_KEYS[table] || 'id';
}

// ============================================
// DATABASE
// ============================================
let pool;
let dbInitialized = false;

function getPool() {
    if (!pool) {
        pool = new Pool({
            connectionString: process.env.DATABASE_URL
        });
    }
    return pool;
}

async function initDB() {
    if (dbInitialized) return;
    
    const client = await getPool().connect();
    try {
        await client.query(`CREATE TABLE IF NOT EXISTS admin_users (id SERIAL PRIMARY KEY, username TEXT UNIQUE NOT NULL, email TEXT DEFAULT '', password_hash TEXT NOT NULL, role TEXT DEFAULT 'admin', is_active BOOLEAN DEFAULT true, last_login TIMESTAMP, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)`);
        await client.query(`CREATE TABLE IF NOT EXISTS whitelist (id SERIAL PRIMARY KEY, wallet_address TEXT NOT NULL, label TEXT DEFAULT '', added_by INTEGER REFERENCES admin_users(id), is_active BOOLEAN DEFAULT true, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)`);
        await client.query(`CREATE TABLE IF NOT EXISTS blacklist (id SERIAL PRIMARY KEY, telegram_id TEXT DEFAULT '', username TEXT DEFAULT '', reason TEXT DEFAULT '', added_by INTEGER REFERENCES admin_users(id), is_active BOOLEAN DEFAULT true, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)`);
        await client.query(`CREATE TABLE IF NOT EXISTS activity_logs (id SERIAL PRIMARY KEY, admin_id INTEGER REFERENCES admin_users(id), action TEXT NOT NULL, table_name TEXT DEFAULT '', record_id INTEGER, details JSONB DEFAULT '{}', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)`);

        const existingAdmin = await client.query('SELECT COUNT(*) as cnt FROM admin_users');
        if (existingAdmin.rows[0].cnt === 0) {
            const hashedPassword = await bcrypt.hash('GhostWire@2026', 10);
            await client.query('INSERT INTO admin_users (username, email, password_hash, role) VALUES ($1, $2, $3, $4)', ['admin', 'admin@ghostwire.io', hashedPassword, 'superadmin']);
        }
        dbInitialized = true;
    } catch (error) {
        console.error('DB init error:', error);
    } finally {
        client.release();
    }
}

// ============================================
// AUTH MIDDLEWARE
// ============================================
function authenticateToken(req) {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];
    if (!token) return null;
    try {
        return jwt.verify(token, JWT_SECRET);
    } catch (err) {
        return null;
    }
}

// ============================================
// REQUEST HANDLER
// ============================================
module.exports = async (req, res) => {
    // Enable CORS
    res.setHeader('Access-Control-Allow-Credentials', true);
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
    res.setHeader('Access-Control-Allow-Headers', 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version, Authorization');

    // Handle OPTIONS request
    if (req.method === 'OPTIONS') {
        res.status(200).end();
        return;
    }

    // Initialize database
    try {
        await initDB();
    } catch (e) {
        console.error('DB init failed:', e);
    }

    // Parse request body for POST/PUT
    let body = {};
    if (req.method === 'POST' || req.method === 'PUT') {
        try {
            body = await parseBody(req);
        } catch (e) {
            body = {};
        }
    }

    const url = req.url;
    const method = req.method;
    const user = authenticateToken(req);

    try {
        // ============================================
        // SERVE STATIC FILES
        // ============================================
        if (!url.startsWith('/api')) {
            const publicPath = path.join(__dirname, '..', 'public');
            let filePath = path.join(publicPath, url === '/' ? 'index.html' : url);
            
            if (fs.existsSync(filePath)) {
                const ext = path.extname(filePath);
                const mimeTypes = {
                    '.html': 'text/html',
                    '.css': 'text/css',
                    '.js': 'application/javascript',
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.svg': 'image/svg+xml',
                    '.ico': 'image/x-icon'
                };
                res.setHeader('Content-Type', mimeTypes[ext] || 'application/octet-stream');
                res.status(200).send(fs.readFileSync(filePath));
                return;
            }
            // SPA fallback
            res.setHeader('Content-Type', 'text/html');
            res.status(200).send(fs.readFileSync(path.join(publicPath, 'index.html')));
            return;
        }

        // ============================================
        // API ROUTES
        // ============================================
        
        // Public routes
        if (url === '/api/auth/login' && method === 'POST') {
            const { username, password } = body;
            if (!username || !password) {
                return sendJSON(res, 400, { error: 'Username and password required' });
            }
            
            const result = await getPool().query('SELECT * FROM admin_users WHERE LOWER(username) = LOWER($1) AND is_active = true', [username]);
            
            if (result.rows.length === 0) {
                return sendJSON(res, 401, { error: 'Invalid credentials' });
            }
            
            const adminUser = result.rows[0];
            const validPassword = await bcrypt.compare(password, adminUser.password_hash);
            
            if (!validPassword) {
                return sendJSON(res, 401, { error: 'Invalid credentials' });
            }
            
            await getPool().query('UPDATE admin_users SET last_login = CURRENT_TIMESTAMP WHERE id = $1', [adminUser.id]);
            
            const token = jwt.sign({ id: adminUser.id, username: adminUser.username, role: adminUser.role }, JWT_SECRET, { expiresIn: '24h' });
            
            return sendJSON(res, 200, {
                token,
                user: {
                    id: adminUser.id,
                    username: adminUser.username,
                    email: adminUser.email || '',
                    role: adminUser.role,
                    last_login: adminUser.last_login
                }
            });
        }

        if (url === '/api/health') {
            return sendJSON(res, 200, { status: 'ok' });
        }

        // Protected routes
        if (!user) {
            return sendJSON(res, 401, { error: 'Authentication required' });
        }

        // Auth profile
        if (url === '/api/auth/profile' && method === 'GET') {
            const result = await getPool().query('SELECT id, username, email, role, last_login, created_at FROM admin_users WHERE id = $1', [user.id]);
            if (result.rows.length === 0) return sendJSON(res, 404, { error: 'User not found' });
            return sendJSON(res, 200, result.rows[0]);
        }

        if (url === '/api/auth/profile' && method === 'PUT') {
            await getPool().query('UPDATE admin_users SET email = $1 WHERE id = $2', [body.email || '', user.id]);
            return sendJSON(res, 200, { message: 'Profile updated' });
        }

        if (url === '/api/auth/change-password' && method === 'PUT') {
            const { current_password, new_password } = body;
            if (!current_password || !new_password) return sendJSON(res, 400, { error: 'Both passwords required' });
            const result = await getPool().query('SELECT password_hash FROM admin_users WHERE id = $1', [user.id]);
            const valid = await bcrypt.compare(current_password, result.rows[0].password_hash);
            if (!valid) return sendJSON(res, 400, { error: 'Current password incorrect' });
            const hash = await bcrypt.hash(new_password, 10);
            await getPool().query('UPDATE admin_users SET password_hash = $1 WHERE id = $2', [hash, user.id]);
            return sendJSON(res, 200, { message: 'Password changed' });
        }

        // Admins CRUD
        if (url === '/api/admins' && method === 'GET') {
            const result = await getPool().query('SELECT id, username, email, role, is_active, last_login, created_at FROM admin_users ORDER BY created_at DESC');
            return sendJSON(res, 200, result.rows);
        }

        if (url === '/api/admins' && method === 'POST') {
            if (user.role !== 'superadmin') return sendJSON(res, 403, { error: 'Only superadmins can create admins' });
            const { username, email, password, role } = body;
            if (!username || !password) return sendJSON(res, 400, { error: 'Username and password required' });
            const hash = await bcrypt.hash(password, 10);
            const result = await getPool().query('INSERT INTO admin_users (username, email, password_hash, role) VALUES ($1, $2, $3, $4) RETURNING id, username, email, role, is_active, created_at', [username, email || '', hash, role || 'admin']);
            await getPool().query('INSERT INTO activity_logs (admin_id, action, table_name, record_id, details) VALUES ($1, $2, $3, $4, $5)', [user.id, 'CREATE', 'admin_users', result.rows[0].id, JSON.stringify({ username, role })]);
            return sendJSON(res, 201, result.rows[0]);
        }

        // Generic query
        if (url === '/api/query' && method === 'POST') {
            const { sql } = body;
            if (!sql || !sql.trim().toUpperCase().startsWith('SELECT')) return sendJSON(res, 403, { error: 'Only SELECT allowed' });
            const result = await getPool().query(sql);
            return sendJSON(res, 200, { rows: result.rows, rowCount: result.rowCount });
        }

        // Dashboard stats
// Dashboard stats
// Dashboard stats
if (url === '/api/dashboard/stats' && method === 'GET') {
    const result = await getPool().query(`
        SELECT 
            (SELECT COUNT(*) FROM users WHERE is_active=true) as total_users,
            (SELECT COUNT(*) FROM wallets WHERE is_active=true) as total_wallets,
            (SELECT COUNT(*) FROM positions WHERE is_active=true AND amount>0) as open_positions,
            (SELECT COUNT(*) FROM channels WHERE is_active=true) as active_channels,
            (SELECT COUNT(*) FROM trade_history WHERE DATE(created_at)=CURRENT_DATE) as today_trades,
            (SELECT COUNT(*) FROM whitelist WHERE is_active=true) as whitelist_count,
            (SELECT COUNT(*) FROM blacklist WHERE is_active=true) as blacklist_count,
            (SELECT COUNT(*) FROM admin_users WHERE is_active=true) as admin_count,
            (SELECT COALESCE(SUM(total_value) / 1000.0, 0)::numeric(20,3) FROM trade_history WHERE DATE(created_at)=CURRENT_DATE AND trade_type = 'sell') as today_volume_sol,
            (SELECT COALESCE(SUM(total_value) / 100000.0, 0)::numeric(20,3) FROM trade_history WHERE trade_type = 'sell') as total_volume_sol
    `);
    return sendJSON(res, 200, result.rows[0] || {});
}

        if (url === '/api/dashboard/trade-volume' && method === 'GET') {
            try {
                const result = await getPool().query(`SELECT TO_CHAR(DATE(created_at),'Dy') as day, DATE(created_at) as date, COUNT(*)::int as trade_count FROM trade_history WHERE created_at >= CURRENT_DATE - INTERVAL '7 days' GROUP BY DATE(created_at), TO_CHAR(DATE(created_at),'Dy') ORDER BY DATE(created_at)`);
                const days=[],counts=[],dayNames=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
                for(let i=6;i>=0;i--){const d=new Date();d.setDate(d.getDate()-i);const ds=d.toISOString().split('T')[0],dn=dayNames[d.getDay()],f=result.rows.find(r=>new Date(r.date).toISOString().split('T')[0]===ds);days.push(dn);counts.push(f?f.trade_count:0)}
                return sendJSON(res, 200, {days,counts});
            } catch(e) { return sendJSON(res, 200, {days:['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],counts:[0,0,0,0,0,0,0]}); }
        }

        if (url === '/api/dashboard/user-registrations' && method === 'GET') {
            try {
                const result = await getPool().query(`SELECT TO_CHAR(DATE(created_at),'Dy') as day, DATE(created_at) as date, COUNT(*)::int as user_count FROM users WHERE created_at >= CURRENT_DATE - INTERVAL '7 days' GROUP BY DATE(created_at), TO_CHAR(DATE(created_at),'Dy') ORDER BY DATE(created_at)`);
                const days=[],counts=[],dayNames=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
                for(let i=6;i>=0;i--){const d=new Date();d.setDate(d.getDate()-i);const ds=d.toISOString().split('T')[0],dn=dayNames[d.getDay()],f=result.rows.find(r=>new Date(r.date).toISOString().split('T')[0]===ds);days.push(dn);counts.push(f?f.user_count:0)}
                return sendJSON(res, 200, {days,counts});
            } catch(e) { return sendJSON(res, 200, {days:['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],counts:[0,0,0,0,0,0,0]}); }
        }

        if (url === '/api/dashboard/recent-trades' && method === 'GET') {
            try {
                const result = await getPool().query(`SELECT th.created_at, u.username, th.trade_type, LEFT(th.token_address,12)||'...' as token, ROUND(th.amount::numeric,4) as amount FROM trade_history th JOIN users u ON th.user_id=u.user_id ORDER BY th.created_at DESC LIMIT 10`);
                return sendJSON(res, 200, result.rows);
            } catch(e) { return sendJSON(res, 200, []); }
        }

        if (url === '/api/logs' && method === 'GET') {
            const result = await getPool().query('SELECT al.*, a.username FROM activity_logs al LEFT JOIN admin_users a ON al.admin_id=a.id ORDER BY al.created_at DESC LIMIT 100');
            return sendJSON(res, 200, result.rows);
        }

        // Whitelist
        if (url === '/api/whitelist' && method === 'GET') {
            const result = await getPool().query('SELECT w.*, a.username as added_by_username FROM whitelist w LEFT JOIN admin_users a ON w.added_by=a.id WHERE w.is_active=true ORDER BY w.created_at DESC');
            return sendJSON(res, 200, result.rows);
        }

        if (url === '/api/whitelist' && method === 'POST') {
            const { wallet_address, label } = body;
            if (!wallet_address) return sendJSON(res, 400, { error: 'Wallet required' });
            const result = await getPool().query('INSERT INTO whitelist (wallet_address, label, added_by) VALUES ($1,$2,$3) RETURNING *', [wallet_address, label||'', user.id]);
            return sendJSON(res, 201, result.rows[0]);
        }

        // Blacklist
        if (url === '/api/blacklist' && method === 'GET') {
            const result = await getPool().query('SELECT b.*, a.username as added_by_username FROM blacklist b LEFT JOIN admin_users a ON b.added_by=a.id WHERE b.is_active=true ORDER BY b.created_at DESC');
            return sendJSON(res, 200, result.rows);
        }

        if (url === '/api/blacklist' && method === 'POST') {
            const { telegram_id, username, reason } = body;
            const result = await getPool().query('INSERT INTO blacklist (telegram_id, username, reason, added_by) VALUES ($1,$2,$3,$4) RETURNING *', [telegram_id||'', username||'', reason||'', user.id]);
            return sendJSON(res, 201, result.rows[0]);
        }
        // DEBUG - Check actual total_value values
if (url === '/api/debug/volume' && method === 'GET') {
    const result = await getPool().query(`
        SELECT 
            trade_type,
            total_value,
            created_at
        FROM trade_history 
        WHERE trade_type = 'sell'
        ORDER BY created_at DESC
        LIMIT 10
    `);
    return sendJSON(res, 200, result.rows);
}
        // Generic record CRUD - handle /api/records/:table/:id
        const recordMatch = url.match(/^\/api\/records\/([^\/]+)\/(.+)$/);
        if (recordMatch) {
            const table = recordMatch[1];
            const id = recordMatch[2];
            const pk = getPrimaryKey(table);

            if (method === 'GET') {
                const result = await getPool().query(`SELECT * FROM ${table} WHERE ${pk} = $1`, [id]);
                if (result.rows.length === 0) return sendJSON(res, 404, { error: 'Not found' });
                return sendJSON(res, 200, result.rows[0]);
            }

            if (method === 'PUT') {
                const keys = Object.keys(body);
                if (keys.length === 0) return sendJSON(res, 400, { error: 'No fields' });
                const setClauses = keys.map((k, i) => `${k} = $${i + 1}`);
                const values = keys.map(k => body[k]);
                const result = await getPool().query(`UPDATE ${table} SET ${setClauses.join(', ')} WHERE ${pk} = $${values.length + 1} RETURNING *`, [...values, id]);
                if (result.rows.length === 0) return sendJSON(res, 404, { error: 'Not found' });
                return sendJSON(res, 200, result.rows[0]);
            }

            if (method === 'DELETE') {
                await getPool().query(`DELETE FROM ${table} WHERE ${pk} = $1`, [id]);
                return sendJSON(res, 200, { message: 'Deleted' });
            }
        }

        // Handle /api/admins/:id and /api/whitelist/:id and /api/blacklist/:id
        const adminMatch = url.match(/^\/api\/admins\/(.+)$/);
        if (adminMatch) {
            const id = adminMatch[1];
            if (method === 'PUT') {
                const { email, role, is_active } = body;
                const result = await getPool().query('UPDATE admin_users SET email=$1, role=COALESCE($2,role), is_active=$3 WHERE id=$4 RETURNING id, username, email, role, is_active', [email||'', role, is_active, id]);
                if (result.rows.length === 0) return sendJSON(res, 404, { error: 'Not found' });
                return sendJSON(res, 200, result.rows[0]);
            }
            if (method === 'DELETE') {
                if (parseInt(id) === user.id) return sendJSON(res, 400, { error: 'Cannot delete yourself' });
                await getPool().query('DELETE FROM admin_users WHERE id=$1', [id]);
                return sendJSON(res, 200, { message: 'Deleted' });
            }
        }

        const whitelistMatch = url.match(/^\/api\/whitelist\/(.+)$/);
        if (whitelistMatch) {
            const id = whitelistMatch[1];
            if (method === 'PUT') {
                const { wallet_address, label, is_active } = body;
                await getPool().query('UPDATE whitelist SET wallet_address=$1, label=$2, is_active=$3 WHERE id=$4', [wallet_address, label, is_active, id]);
                return sendJSON(res, 200, { message: 'Updated' });
            }
            if (method === 'DELETE') {
                await getPool().query('UPDATE whitelist SET is_active=false WHERE id=$1', [id]);
                return sendJSON(res, 200, { message: 'Removed' });
            }
        }

        const blacklistMatch = url.match(/^\/api\/blacklist\/(.+)$/);
        if (blacklistMatch) {
            const id = blacklistMatch[1];
            if (method === 'PUT') {
                const { telegram_id, username, reason, is_active } = body;
                await getPool().query('UPDATE blacklist SET telegram_id=$1, username=$2, reason=$3, is_active=$4 WHERE id=$5', [telegram_id, username, reason, is_active, id]);
                return sendJSON(res, 200, { message: 'Updated' });
            }
            if (method === 'DELETE') {
                await getPool().query('UPDATE blacklist SET is_active=false WHERE id=$1', [id]);
                return sendJSON(res, 200, { message: 'Removed' });
            }
        }

        // 404 for unmatched API routes
        return sendJSON(res, 404, { error: 'API route not found' });

    } catch (error) {
        console.error('Server error:', error);
        return sendJSON(res, 500, { error: 'Internal server error: ' + error.message });
    }
};

// ============================================
// HELPERS
// ============================================
function sendJSON(res, status, data) {
    res.status(status).json(data);
}

function parseBody(req) {
    return new Promise((resolve, reject) => {
        let data = '';
        req.on('data', chunk => { data += chunk; });
        req.on('end', () => {
            try {
                resolve(data ? JSON.parse(data) : {});
            } catch (e) {
                resolve({});
            }
        });
        req.on('error', reject);
    });
}