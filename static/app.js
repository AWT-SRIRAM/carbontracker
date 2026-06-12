// EcoTrace Frontend Core Logic

let activeUserId = null;
let allUsers = [];
let availableActions = [];
let currentDashboard = null;
let emissionsChart = null;

// DOM Elements
const userSelector = document.getElementById('user-selector');
const welcomeUserName = document.getElementById('current-user-name');
const notificationBar = document.getElementById('notification-bar');
const dashboardSetupAlert = document.getElementById('dashboard-setup-alert');

// Modal Elements
const createUserModal = document.getElementById('modal-create-user');
const btnCreateProfileModal = document.getElementById('btn-create-profile-modal');
const btnCloseModal = document.getElementById('btn-close-modal');
const createUserForm = document.getElementById('create-user-form');

// Form Inputs
const calculatorForm = document.getElementById('calculator-form');
const actionLogForm = document.getElementById('action-log-form');
const logActionSelect = document.getElementById('log-action-id');
const logDateInput = document.getElementById('log-date');
const logQuantityInput = document.getElementById('log-quantity');
const logQuantityUnitHelp = document.getElementById('log-quantity-unit-help');

// Navigation Tabs
function switchTab(tabId) {
    // Hide all tabs
    document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(btn => btn.classList.remove('active'));
    
    // Show selected tab
    const targetPane = document.getElementById(`tab-${tabId}`);
    const targetBtn = document.getElementById(`nav-btn-${tabId}`);
    
    if (targetPane && targetBtn) {
        targetPane.classList.add('active');
        targetBtn.classList.add('active');
    }

    // Update main heading contextually
    const heading = document.getElementById('main-heading');
    if (tabId === 'dashboard') heading.textContent = 'Carbon Footprint Dashboard';
    if (tabId === 'calculator') heading.textContent = 'Onboarding Baseline Calculator';
    if (tabId === 'tracker') heading.textContent = 'Daily Action Logger';
    if (tabId === 'insights') heading.textContent = 'Tailored Insights & Tips';
}

// Notification Helper
function showNotification(message, type = 'success') {
    notificationBar.className = `notification-bar ${type}`;
    notificationBar.textContent = message;
    notificationBar.classList.remove('hidden');
    
    setTimeout(() => {
        notificationBar.classList.add('hidden');
    }, 4000);
}

// Format number helper
function formatNum(val, decimals = 1) {
    return parseFloat(val).toFixed(decimals);
}

// Initialize Application
document.addEventListener('DOMContentLoaded', async () => {
    // Set default log date to today (local date in YYYY-MM-DD format)
    const today = new Date().toISOString().split('T')[0];
    logDateInput.value = today;

    // Load Actions and Users
    await loadActionCatalog();
    await loadUsers();

    // Setup Event Listeners
    setupEventListeners();
});

// Load catalog of carbon offset actions
async function loadActionCatalog() {
    try {
        const response = await fetch('/api/actions');
        if (response.ok) {
            availableActions = await response.ok ? await response.json() : [];
            populateActionDropdown();
        }
    } catch (err) {
        console.error('Failed to load action items:', err);
    }
}

// Populate Action Dropdown inside logger
function populateActionDropdown() {
    logActionSelect.innerHTML = '<option value="">-- Choose Sustainable Action --</option>';
    availableActions.forEach(action => {
        const opt = document.createElement('option');
        opt.value = action.id;
        opt.textContent = `${action.title} (${action.category}) - saves ${action.co2_savings_kg} kg CO₂/unit`;
        logActionSelect.appendChild(opt);
    });
}

// Update log quantity label dynamically based on selected action item
logActionSelect.addEventListener('change', () => {
    const selectedId = parseInt(logActionSelect.value);
    const action = availableActions.find(a => a.id === selectedId);
    if (action) {
        let unit = 'unit(s)';
        if (action.title.includes('Bike') || action.title.includes('Transit')) unit = 'kilometer(s)';
        else if (action.title.includes('Meal')) unit = 'meal(s)';
        else if (action.title.includes('Dry')) unit = 'load(s)';
        else if (action.title.includes('Thermostat')) unit = 'day(s)';
        else if (action.title.includes('Compost')) unit = 'kg(s)';
        
        logQuantityUnitHelp.textContent = `Enter quantity in ${unit} (Standard offset: ${action.co2_savings_kg} kg CO₂ per ${unit})`;
    } else {
        logQuantityUnitHelp.textContent = 'Units (meals, kilometers, loads, days)';
    }
});

// Load Users switcher
async function loadUsers() {
    try {
        const response = await fetch('/api/users');
        if (response.ok) {
            allUsers = await response.json();
            populateUserSelector();
            
            // Auto select first user if exists
            if (allUsers.length > 0) {
                userSelector.value = allUsers[0].id;
                selectUser(allUsers[0].id);
            } else {
                // If no users, prompt create user
                createUserModal.classList.remove('hidden');
            }
        }
    } catch (err) {
        console.error('Failed to load users:', err);
    }
}

function populateUserSelector() {
    userSelector.innerHTML = '<option value="">-- Choose Active Profile --</option>';
    allUsers.forEach(user => {
        const opt = document.createElement('option');
        opt.value = user.id;
        opt.textContent = `${user.name} (${user.email})`;
        userSelector.appendChild(opt);
    });
}

// Handle User Selection Change
userSelector.addEventListener('change', (e) => {
    const userId = parseInt(e.target.value);
    if (userId) {
        selectUser(userId);
    } else {
        resetAppToGuest();
    }
});

function selectUser(userId) {
    activeUserId = userId;
    const user = allUsers.find(u => u.id === userId);
    if (user) {
        welcomeUserName.textContent = user.name;
        refreshUserData();
    }
}

function resetAppToGuest() {
    activeUserId = null;
    welcomeUserName.textContent = 'Guest';
    dashboardSetupAlert.classList.add('hidden');
    // Clear stats
    document.getElementById('stat-baseline').textContent = '0.0';
    document.getElementById('stat-savings').textContent = '0.0';
    document.getElementById('stat-net').textContent = '0.0';
    document.getElementById('progress-percentage').textContent = '0%';
    document.getElementById('progress-ring-fill').style.strokeDashoffset = '502.6';
    document.getElementById('category-bars-container').innerHTML = '<div class="empty-state">No profile selected.</div>';
    document.getElementById('dashboard-recent-table').querySelector('tbody').innerHTML = '<tr><td colspan="5" class="text-center text-muted">No profile selected.</td></tr>';
}

// Fetch dashboard analytics, recent logs, and insights
async function refreshUserData() {
    if (!activeUserId) return;
    try {
        const response = await fetch(`/api/analytics/dashboard?user_id=${activeUserId}`);
        if (response.ok) {
            currentDashboard = await response.json();
            renderDashboard(currentDashboard);
            renderInsights(currentDashboard.insights);
            renderLogsTable(currentDashboard.recent_logs);
            
            // Update calculator values if baseline profile exists
            if (currentDashboard.has_profile) {
                loadCalculatorInputs();
            }
        }
    } catch (err) {
        console.error('Failed to refresh dashboard data:', err);
    }
}

// Populate Onboarding Form Inputs if baseline exists
async function loadCalculatorInputs() {
    try {
        const res = await fetch(`/api/profile/baseline?user_id=${activeUserId}`);
        if (res.ok) {
            const data = await res.json();
            document.getElementById('housing_electricity_kwh').value = data.housing_electricity_kwh;
            document.getElementById('housing_gas_kwh').value = data.housing_gas_kwh;
            document.getElementById('transport_car_km').value = data.transport_car_km;
            document.getElementById('transport_car_type').value = data.transport_car_type;
            document.getElementById('transport_public_hours').value = data.transport_public_hours;
            document.getElementById('diet_type').value = data.diet_type;
            document.getElementById('shopping_frequency').value = data.shopping_frequency;
            
            // Set slider value
            if (data.reduction_goal_percentage !== undefined) {
                document.getElementById('reduction_goal_percentage').value = data.reduction_goal_percentage;
                document.getElementById('goal-range-value').textContent = data.reduction_goal_percentage;
            }
        }
    } catch (err) {
        console.log('No existing baseline found to populate.');
    }
}

// Render Dashboard Data (gauges, progress, category bars)
function renderDashboard(data) {
    if (!data.has_profile) {
        dashboardSetupAlert.classList.remove('hidden');
        document.getElementById('stat-baseline').textContent = '0.0';
        document.getElementById('stat-savings').textContent = '0.0';
        document.getElementById('stat-net').textContent = '0.0';
        document.getElementById('progress-percentage').textContent = '0%';
        document.getElementById('progress-ring-fill').style.strokeDashoffset = '502.6';
        
        // Hide chart canvas, show fallback
        const canvas = document.getElementById('emissionsDoughnutChart');
        if (canvas) canvas.style.display = 'none';
        const fallback = document.getElementById('emissions-chart-fallback');
        if (fallback) fallback.style.display = 'block';
        
        // Clear badges
        document.getElementById('achievements-badges-container').innerHTML = '<div class="empty-state">No baseline data found. Please complete the calculator.</div>';
        return;
    }
    
    dashboardSetupAlert.classList.add('hidden');
    
    // 1. Key Statistics
    document.getElementById('stat-baseline').textContent = formatNum(data.baseline_total_co2_kg_monthly);
    document.getElementById('stat-savings').textContent = formatNum(data.logged_savings_co2_kg_monthly);
    document.getElementById('stat-net').textContent = formatNum(data.actual_total_co2_kg_monthly);

    // 2. Progress Ring Calculation (Target: User's custom reduction goal)
    const baseVal = data.baseline_total_co2_kg_monthly;
    const saveVal = data.logged_savings_co2_kg_monthly;
    
    // Calculate percentage reduction achieved
    const percentReduction = baseVal > 0 ? (saveVal / baseVal) * 100 : 0;
    
    // Set custom target percentage in UI
    const targetPercent = data.reduction_goal_percentage || 20.0;
    const targetGoalEl = document.getElementById('dashboard-target-goal');
    if (targetGoalEl) targetGoalEl.textContent = formatNum(targetPercent, 0);
    
    document.getElementById('progress-percentage').textContent = `${formatNum(percentReduction, 1)}%`;
    
    // Progress Ring circle length = 2 * PI * r = 2 * 3.14159 * 80 = 502.65
    const strokeLength = 502.65;
    const strokeOffset = strokeLength - (Math.min(100, percentReduction) / 100) * strokeLength;
    document.getElementById('progress-ring-fill').style.strokeDashoffset = strokeOffset;

    // 3. Category Breakdown Doughnut Chart
    renderEmissionsChart(data.category_baselines);

    // 4. Render unlocked badges
    renderBadges(data.unlocked_badges || []);
}

// Render Recent and History Logs Table
function renderLogsTable(logs) {
    const recentTbody = document.querySelector('#dashboard-recent-table tbody');
    const historyTbody = document.querySelector('#tracker-history-table tbody');
    
    recentTbody.innerHTML = '';
    historyTbody.innerHTML = '';

    if (logs.length === 0) {
        const emptyRow = '<tr><td colspan="5" class="text-center text-muted">No activities logged yet.</td></tr>';
        recentTbody.innerHTML = emptyRow;
        historyTbody.innerHTML = emptyRow;
        return;
    }

    logs.forEach(log => {
        // Formatted Date
        const logDateStr = new Date(log.logged_date).toLocaleDateString(undefined, {month: 'short', day: 'numeric', year: 'numeric'});
        const totalSaved = formatNum(log.quantity * log.action.co2_savings_kg);
        
        // Populate Dashboard Table row
        const rowDash = document.createElement('tr');
        rowDash.innerHTML = `
            <td>${logDateStr}</td>
            <td><strong>${log.action.title}</strong></td>
            <td><span class="category-name">${log.action.category}</span></td>
            <td>${log.quantity}</td>
            <td class="text-muted" style="color:var(--color-primary);font-weight:600">${totalSaved}</td>
        `;
        recentTbody.appendChild(rowDash);

        // Populate Tracker History row (includes delete button)
        const rowHist = document.createElement('tr');
        rowHist.innerHTML = `
            <td>${logDateStr}</td>
            <td>
                <strong>${log.action.title}</strong>
                <div style="font-size:11px;color:var(--color-text-muted)">${log.action.description}</div>
            </td>
            <td>${log.quantity}</td>
            <td style="color:var(--color-primary);font-weight:600">${totalSaved}</td>
            <td>
                <button class="btn btn-danger-outline btn-sm" onclick="deleteLogEntry(${log.id})">Delete</button>
            </td>
        `;
        historyTbody.appendChild(rowHist);
    });
}

// Delete log entry action handler
async function deleteLogEntry(logId) {
    if (!activeUserId || !confirm('Are you sure you want to remove this logged activity?')) return;
    try {
        const response = await fetch(`/api/logs/${logId}?user_id=${activeUserId}`, {
            method: 'DELETE'
        });
        if (response.status === 204) {
            showNotification('Activity successfully removed.');
            refreshUserData();
        } else {
            showNotification('Failed to remove activity log.', 'error');
        }
    } catch (err) {
        console.error('Error deleting activity entry:', err);
    }
}

// Render dynamic AI insights
function renderInsights(insights) {
    const insightsContainer = document.getElementById('insights-container');
    insightsContainer.innerHTML = '';
    
    if (insights.length === 0) {
        insightsContainer.innerHTML = '<div class="empty-state">No dynamic carbon insights calculated. Complete your profile.</div>';
        return;
    }

    insights.forEach(insight => {
        const card = document.createElement('div');
        card.className = 'glass-card insight-card';
        card.innerHTML = `
            <div class="insight-icon" style="color: var(--color-primary)">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
            </div>
            <div class="insight-card-content">
                <p>${insight}</p>
            </div>
        `;
        insightsContainer.appendChild(card);
    });
}

// Setup Application Level Event Listeners
function setupEventListeners() {
    // 1. User Creation Modal Events
    btnCreateProfileModal.addEventListener('click', () => {
        createUserModal.classList.remove('hidden');
    });

    btnCloseModal.addEventListener('click', () => {
        createUserModal.classList.add('hidden');
    });

    createUserForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('new-user-name').value.trim();
        const email = document.getElementById('new-user-email').value.trim();

        try {
            const response = await fetch('/api/users', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email })
            });

            if (response.ok) {
                const newUser = await response.json();
                showNotification(`Profile created successfully for ${newUser.name}!`);
                createUserModal.classList.add('hidden');
                createUserForm.reset();
                
                // Refresh list and select new user
                await loadUsers();
                userSelector.value = newUser.id;
                selectUser(newUser.id);
            } else {
                showNotification('Could not create profile. Try a unique email.', 'error');
            }
        } catch (err) {
            console.error('Error creating user profile:', err);
            showNotification('Network error occurred.', 'error');
        }
    });

    // 2. Onboarding Calculator Submission
    calculatorForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!activeUserId) {
            showNotification('Please select or create a profile first.', 'error');
            return;
        }

        const payload = {
            housing_electricity_kwh: parseFloat(document.getElementById('housing_electricity_kwh').value),
            housing_gas_kwh: parseFloat(document.getElementById('housing_gas_kwh').value),
            transport_car_km: parseFloat(document.getElementById('transport_car_km').value),
            transport_car_type: document.getElementById('transport_car_type').value,
            transport_public_hours: parseFloat(document.getElementById('transport_public_hours').value),
            diet_type: document.getElementById('diet_type').value,
            shopping_frequency: document.getElementById('shopping_frequency').value,
            reduction_goal_percentage: parseFloat(document.getElementById('reduction_goal_percentage').value)
        };

        try {
            const response = await fetch(`/api/profile/baseline?user_id=${activeUserId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                showNotification('Onboarding baseline calculated successfully!');
                await refreshUserData();
                switchTab('dashboard');
            } else {
                showNotification('Failed to update baseline calculator.', 'error');
            }
        } catch (err) {
            console.error('Error submitting baseline calculator:', err);
            showNotification('Network error saving calculator data.', 'error');
        }
    });

    // 3. Logger activity submission
    actionLogForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!activeUserId) {
            showNotification('Please select or create a profile first.', 'error');
            return;
        }

        const actionId = parseInt(logActionSelect.value);
        if (!actionId) {
            showNotification('Please select a valid carbon action item.', 'error');
            return;
        }

        const payload = {
            action_id: actionId,
            logged_date: logDateInput.value,
            quantity: parseFloat(logQuantityInput.value)
        };

        try {
            const response = await fetch(`/api/logs?user_id=${activeUserId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                showNotification('Activity savings successfully tracked!');
                actionLogForm.reset();
                // Maintain current date for convenience
                logDateInput.value = today = new Date().toISOString().split('T')[0];
                logActionSelect.value = '';
                logQuantityInput.value = '1.0';
                logQuantityUnitHelp.textContent = 'Units (meals, kilometers, loads, days)';
                
                await refreshUserData();
            } else {
                showNotification('Failed to log sustainable action.', 'error');
            }
        } catch (err) {
            console.error('Error logging daily action item:', err);
            showNotification('Network error saving action log.', 'error');
        }
    });

    // 4. Download CSV Click handler
    const btnExportCsv = document.getElementById('btn-export-csv');
    if (btnExportCsv) {
        btnExportCsv.addEventListener('click', () => {
            if (!activeUserId) {
                showNotification('Please select or create a profile first.', 'error');
                return;
            }
            window.location.href = `/api/logs/export?user_id=${activeUserId}`;
        });
    }
}

// Render Chart.js Doughnut Chart
function renderEmissionsChart(categoryBaselines) {
    const canvas = document.getElementById('emissionsDoughnutChart');
    const fallbackEl = document.getElementById('emissions-chart-fallback');
    
    if (!canvas) return;
    
    if (categoryBaselines.length === 0) {
        canvas.style.display = 'none';
        if (fallbackEl) fallbackEl.style.display = 'block';
        return;
    }
    
    canvas.style.display = 'block';
    if (fallbackEl) fallbackEl.style.display = 'none';
    
    const labels = categoryBaselines.map(item => item.category);
    const values = categoryBaselines.map(item => item.co2_kg_monthly);
    
    const bgColors = [
        'rgba(59, 130, 246, 0.45)',   // Energy: Blue
        'rgba(234, 179, 8, 0.45)',    // Transport: Yellow
        'rgba(16, 185, 129, 0.45)',   // Food: Green
        'rgba(236, 72, 153, 0.45)'    // Consumption: Pink
    ];
    const borderColors = [
        '#3b82f6',
        '#eab308',
        '#10b981',
        '#ec4899'
    ];
    
    if (emissionsChart) {
        emissionsChart.destroy();
    }
    
    emissionsChart = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: bgColors,
                borderColor: borderColors,
                borderWidth: 1.5,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: '#f3f4f6',
                        font: {
                            family: 'Plus Jakarta Sans',
                            size: 11
                        },
                        padding: 10
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return ` ${context.label}: ${parseFloat(context.raw).toFixed(1)} kg CO2e`;
                        }
                    }
                }
            },
            cutout: '65%'
        }
    });
}

// Render gamified eco-badges
function renderBadges(unlockedList = []) {
    const container = document.getElementById('achievements-badges-container');
    if (!container) return;
    
    container.innerHTML = '';
    
    const badgeCatalog = [
        { name: 'Transit Hero', desc: 'Log 30+ km of biking, walking, or transit.', icon: '🚲' },
        { name: 'Plant-Powered', desc: 'Log 10+ plant-based or vegetarian meals.', icon: '🥗' },
        { name: 'Energy Saver', desc: 'Log 5+ energy-saving daily activities.', icon: '⚡' },
        { name: 'Eco Champion', desc: 'Meet or exceed your custom monthly reduction goal.', icon: '🏆' }
    ];
    
    badgeCatalog.forEach(badge => {
        const isUnlocked = unlockedList.includes(badge.name);
        const card = document.createElement('div');
        card.className = `badge-card ${isUnlocked ? 'unlocked' : ''}`;
        card.innerHTML = `
            <div class="badge-icon-wrapper">
                <span>${badge.icon}</span>
            </div>
            <div class="badge-info">
                <h4>${badge.name}</h4>
                <p>${badge.desc}</p>
                <span style="font-size:9px; font-weight:600; text-transform:uppercase; color:${isUnlocked ? 'var(--color-primary)' : 'var(--color-text-muted)'}">
                    ${isUnlocked ? 'Unlocked 🎉' : 'Locked'}
                </span>
            </div>
        `;
        container.appendChild(card);
    });
}
