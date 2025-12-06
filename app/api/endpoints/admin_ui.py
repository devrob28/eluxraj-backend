from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def admin_dashboard():
    """Admin Dashboard UI"""
    
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ELUXRAJ Admin</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0f; color: #fff; }
            .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
            
            /* Header */
            header { background: #12121a; border-bottom: 1px solid #333; padding: 20px; margin-bottom: 30px; }
            header h1 { font-size: 24px; background: linear-gradient(135deg, #7c3aed, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            header p { color: #888; font-size: 14px; margin-top: 5px; }
            
            /* Login Form */
            .login-form { max-width: 400px; margin: 100px auto; background: #12121a; padding: 40px; border-radius: 16px; border: 1px solid #333; }
            .login-form h2 { margin-bottom: 20px; text-align: center; }
            .login-form input { width: 100%; padding: 14px; margin-bottom: 15px; background: #1a1a2e; border: 1px solid #333; border-radius: 8px; color: #fff; font-size: 16px; }
            .login-form button { width: 100%; padding: 14px; background: linear-gradient(135deg, #7c3aed, #06b6d4); border: none; border-radius: 8px; color: #fff; font-size: 16px; font-weight: 600; cursor: pointer; }
            .login-form button:hover { opacity: 0.9; }
            
            /* Dashboard */
            .dashboard { display: none; }
            .dashboard.active { display: block; }
            
            /* Stats Grid */
            .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }
            @media (max-width: 1000px) { .stats-grid { grid-template-columns: repeat(2, 1fr); } }
            @media (max-width: 600px) { .stats-grid { grid-template-columns: 1fr; } }
            
            .stat-card { background: #12121a; border: 1px solid #333; border-radius: 12px; padding: 24px; }
            .stat-card .label { color: #888; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }
            .stat-card .value { font-size: 32px; font-weight: 700; margin-top: 8px; }
            .stat-card .value.green { color: #22c55e; }
            .stat-card .value.purple { background: linear-gradient(135deg, #7c3aed, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            
            /* Sections */
            .section { background: #12121a; border: 1px solid #333; border-radius: 12px; padding: 24px; margin-bottom: 20px; }
            .section h3 { margin-bottom: 20px; display: flex; align-items: center; gap: 10px; }
            
            /* Tables */
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #333; }
            th { color: #888; font-size: 12px; text-transform: uppercase; }
            tr:hover { background: rgba(124, 58, 237, 0.1); }
            
            /* Badges */
            .badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
            .badge.free { background: rgba(255,255,255,0.1); color: #888; }
            .badge.pro { background: rgba(124, 58, 237, 0.2); color: #a78bfa; }
            .badge.elite { background: rgba(6, 182, 212, 0.2); color: #22d3ee; }
            .badge.buy { background: rgba(34, 197, 94, 0.2); color: #22c55e; }
            .badge.sell { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
            .badge.hold { background: rgba(245, 158, 11, 0.2); color: #f59e0b; }
            .badge.active { background: rgba(34, 197, 94, 0.2); color: #22c55e; }
            
            /* Buttons */
            .btn { padding: 8px 16px; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; border: none; }
            .btn-primary { background: linear-gradient(135deg, #7c3aed, #06b6d4); color: #fff; }
            .btn-secondary { background: rgba(255,255,255,0.1); color: #fff; }
            .btn:hover { opacity: 0.8; }
            
            /* Tabs */
            .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
            .tab { padding: 10px 20px; background: rgba(255,255,255,0.05); border-radius: 8px; cursor: pointer; }
            .tab.active { background: linear-gradient(135deg, #7c3aed, #06b6d4); }
            
            /* Actions */
            .actions { display: flex; gap: 10px; margin-bottom: 20px; }
            
            /* Loading */
            .loading { text-align: center; padding: 40px; color: #888; }
            
            /* Error */
            .error { background: rgba(239, 68, 68, 0.2); color: #ef4444; padding: 12px; border-radius: 8px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div id="app">
            <!-- Login Form -->
            <div id="loginForm" class="login-form">
                <h2>🔐 Admin Login</h2>
                <input type="email" id="email" placeholder="Email" />
                <input type="password" id="password" placeholder="Password" />
                <button onclick="login()">Login</button>
                <p id="loginError" class="error" style="display:none; margin-top:15px;"></p>
            </div>
            
            <!-- Dashboard -->
            <div id="dashboard" class="dashboard">
                <header>
                    <div class="container" style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <h1>ELUXRAJ Admin</h1>
                            <p>Manage users, signals, and system</p>
                        </div>
                        <button class="btn btn-secondary" onclick="logout()">Logout</button>
                    </div>
                </header>
                
                <div class="container">
                    <!-- Stats -->
                    <div class="stats-grid" id="statsGrid">
                        <div class="stat-card"><div class="label">Total Users</div><div class="value purple" id="totalUsers">-</div></div>
                        <div class="stat-card"><div class="label">Pro Users</div><div class="value" id="proUsers">-</div></div>
                        <div class="stat-card"><div class="label">Elite Users</div><div class="value" id="eliteUsers">-</div></div>
                        <div class="stat-card"><div class="label">MRR</div><div class="value green" id="mrr">-</div></div>
                        <div class="stat-card"><div class="label">Total Signals</div><div class="value purple" id="totalSignals">-</div></div>
                        <div class="stat-card"><div class="label">Active Signals</div><div class="value" id="activeSignals">-</div></div>
                        <div class="stat-card"><div class="label">Signals Today</div><div class="value" id="signalsToday">-</div></div>
                        <div class="stat-card"><div class="label">Avg Score</div><div class="value" id="avgScore">-</div></div>
                    </div>
                    
                    <!-- Tabs -->
                    <div class="tabs">
                        <div class="tab active" onclick="showTab('users')">👥 Users</div>
                        <div class="tab" onclick="showTab('signals')">📊 Signals</div>
                        <div class="tab" onclick="showTab('system')">⚙️ System</div>
                    </div>
                    
                    <!-- Users Section -->
                    <div id="usersSection" class="section">
                        <h3>👥 User Management</h3>
                        <div class="actions">
                            <input type="text" id="userSearch" placeholder="Search users..." style="padding:8px 12px; background:#1a1a2e; border:1px solid #333; border-radius:8px; color:#fff;" onkeyup="searchUsers()" />
                        </div>
                        <table>
                            <thead>
                                <tr><th>ID</th><th>Email</th><th>Name</th><th>Tier</th><th>Status</th><th>Joined</th><th>Actions</th></tr>
                            </thead>
                            <tbody id="usersTable"></tbody>
                        </table>
                    </div>
                    
                    <!-- Signals Section -->
                    <div id="signalsSection" class="section" style="display:none;">
                        <h3>📊 Signal Management</h3>
                        <div class="actions">
                            <button class="btn btn-primary" onclick="triggerScan()">🔍 Trigger Scan</button>
                            <button class="btn btn-secondary" onclick="triggerCleanup()">🧹 Cleanup Expired</button>
                        </div>
                        <table>
                            <thead>
                                <tr><th>ID</th><th>Symbol</th><th>Type</th><th>Score</th><th>Entry</th><th>Target</th><th>Status</th><th>Created</th></tr>
                            </thead>
                            <tbody id="signalsTable"></tbody>
                        </table>
                    </div>
                    
                    <!-- System Section -->
                    <div id="systemSection" class="section" style="display:none;">
                        <h3>⚙️ System Health</h3>
                        <div id="systemHealth"></div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            const API_BASE = window.location.origin;
            let token = localStorage.getItem('adminToken');
            
            // Check if logged in
            if (token) {
                showDashboard();
            }
            
            async function login() {
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;
                
                try {
                    const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ email, password })
                    });
                    
                    const data = await res.json();
                    
                    if (data.access_token) {
                        token = data.access_token;
                        localStorage.setItem('adminToken', token);
                        showDashboard();
                    } else {
                        showLoginError(data.detail || 'Login failed');
                    }
                } catch (e) {
                    showLoginError('Connection error');
                }
            }
            
            function showLoginError(msg) {
                const el = document.getElementById('loginError');
                el.textContent = msg;
                el.style.display = 'block';
            }
            
            function logout() {
                localStorage.removeItem('adminToken');
                token = null;
                document.getElementById('loginForm').style.display = 'block';
                document.getElementById('dashboard').classList.remove('active');
            }
            
            async function showDashboard() {
                document.getElementById('loginForm').style.display = 'none';
                document.getElementById('dashboard').classList.add('active');
                await loadStats();
                await loadUsers();
            }
            
            async function apiCall(endpoint, method = 'GET', body = null) {
                const options = {
                    method,
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                };
                if (body) options.body = JSON.stringify(body);
                
                const res = await fetch(`${API_BASE}${endpoint}`, options);
                if (res.status === 403) {
                    alert('Admin access required');
                    logout();
                    return null;
                }
                return await res.json();
            }
            
            async function loadStats() {
                const data = await apiCall('/api/v1/admin/stats');
                if (!data) return;
                
                document.getElementById('totalUsers').textContent = data.users.total;
                document.getElementById('proUsers').textContent = data.users.by_tier.pro;
                document.getElementById('eliteUsers').textContent = data.users.by_tier.elite;
                document.getElementById('mrr').textContent = '$' + data.revenue.mrr.toLocaleString();
                document.getElementById('totalSignals').textContent = data.signals.total;
                document.getElementById('activeSignals').textContent = data.signals.active;
                document.getElementById('signalsToday').textContent = data.signals.today;
                document.getElementById('avgScore').textContent = data.signals.avg_oracle_score;
            }
            
            async function loadUsers() {
                const data = await apiCall('/api/v1/admin/users');
                if (!data) return;
                
                const tbody = document.getElementById('usersTable');
                tbody.innerHTML = data.users.map(u => `
                    <tr>
                        <td>${u.id}</td>
                        <td>${u.email}</td>
                        <td>${u.full_name || '-'}</td>
                        <td><span class="badge ${u.subscription_tier}">${u.subscription_tier}</span></td>
                        <td><span class="badge ${u.is_active ? 'active' : ''}">${u.is_active ? 'Active' : 'Inactive'}</span></td>
                        <td>${u.created_at ? new Date(u.created_at).toLocaleDateString() : '-'}</td>
                        <td>
                            <select onchange="updateTier(${u.id}, this.value)" style="background:#1a1a2e;color:#fff;border:1px solid #333;padding:4px 8px;border-radius:4px;">
                                <option value="free" ${u.subscription_tier==='free'?'selected':''}>Free</option>
                                <option value="pro" ${u.subscription_tier==='pro'?'selected':''}>Pro</option>
                                <option value="elite" ${u.subscription_tier==='elite'?'selected':''}>Elite</option>
                            </select>
                        </td>
                    </tr>
                `).join('');
            }
            
            async function loadSignals() {
                const data = await apiCall('/api/v1/admin/signals');
                if (!data) return;
                
                const tbody = document.getElementById('signalsTable');
                tbody.innerHTML = data.signals.map(s => `
                    <tr>
                        <td>${s.id}</td>
                        <td><strong>${s.symbol}</strong></td>
                        <td><span class="badge ${s.signal_type}">${s.signal_type.toUpperCase()}</span></td>
                        <td>${s.oracle_score}</td>
                        <td>$${s.entry_price.toLocaleString()}</td>
                        <td>$${s.target_price.toLocaleString()}</td>
                        <td><span class="badge ${s.status}">${s.status}</span></td>
                        <td>${new Date(s.created_at).toLocaleDateString()}</td>
                    </tr>
                `).join('');
            }
            
            async function loadSystemHealth() {
                const data = await apiCall('/api/v1/admin/system/health');
                if (!data) return;
                
                document.getElementById('systemHealth').innerHTML = `
                    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:20px;">
                        <div class="stat-card">
                            <div class="label">API Status</div>
                            <div class="value green">${data.api}</div>
                        </div>
                        <div class="stat-card">
                            <div class="label">Scheduler</div>
                            <div class="value green">${data.scheduler.status}</div>
                        </div>
                        <div class="stat-card">
                            <div class="label">Email</div>
                            <div class="value ${data.email.enabled ? 'green' : ''}">${data.email.enabled ? 'Enabled' : 'Disabled'}</div>
                        </div>
                    </div>
                    <div style="margin-top:20px;">
                        <h4 style="margin-bottom:10px;">Scheduled Jobs</h4>
                        ${data.scheduler.jobs.map(j => `<div style="padding:8px;background:#1a1a2e;border-radius:4px;margin-bottom:8px;">${j.name} - Next: ${j.next_run ? new Date(j.next_run).toLocaleString() : 'N/A'}</div>`).join('')}
                    </div>
                `;
            }
            
            async function updateTier(userId, tier) {
                await apiCall(`/api/v1/admin/users/${userId}/tier?tier=${tier}`, 'PATCH');
                await loadStats();
            }
            
            async function triggerScan() {
                const data = await apiCall('/api/v1/admin/system/scan', 'POST');
                if (data) {
                    alert(`Scan complete! Saved: ${data.result.saved} signals`);
                    await loadStats();
                    await loadSignals();
                }
            }
            
            async function triggerCleanup() {
                await apiCall('/api/v1/admin/system/cleanup', 'POST');
                alert('Cleanup complete!');
                await loadSignals();
            }
            
            function showTab(tab) {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                event.target.classList.add('active');
                
                document.getElementById('usersSection').style.display = tab === 'users' ? 'block' : 'none';
                document.getElementById('signalsSection').style.display = tab === 'signals' ? 'block' : 'none';
                document.getElementById('systemSection').style.display = tab === 'system' ? 'block' : 'none';
                
                if (tab === 'signals') loadSignals();
                if (tab === 'system') loadSystemHealth();
            }
            
            function searchUsers() {
                // Simple client-side search for now
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
