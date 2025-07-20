// Cache DOM elements
const domElements = {
    systemInfo: document.getElementById('systemInfo')
};

// Health check caching
const healthCache = new Map();
const HEALTH_CHECK_INTERVAL = 60000;  // Check health every 60s

// Add loading state management
const loadingOverlay = document.getElementById('loading-overlay');

function showLoading() {
    if (loadingOverlay) loadingOverlay.style.display = 'block';
}

function hideLoading() {
    if (loadingOverlay) loadingOverlay.style.display = 'none';
}

// Optimized health check function
async function fetchWithRetry(url, options = {}, retries = 3) {
    for (let i = 0; i < retries; i++) {
        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response;
        } catch (error) {
            if (i === retries - 1) throw error;
            await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
        }
    }
}

let connectionStatus = true;

function updateConnectionStatus(isConnected) {
    const statusElement = document.getElementById('connectionStatus');
    const statusDot = statusElement?.previousElementSibling;
    
    if (statusElement) {
        statusElement.textContent = isConnected ? 'SYSTEM ONLINE' : 'CONNECTION ERROR';
        if (statusDot) {
            statusDot.className = `status-dot${isConnected ? ' active' : ''}`;
        }
    }
    connectionStatus = isConnected;
}

async function checkHealth(service) {
    try {
        console.log(`Checking health for service: ${service}`);  // Debug log
        const response = await fetchWithRetry(`/health/${service}`);
        const health = await response.json();
        console.log(`Health response for ${service}:`, health);  // Debug log
        updateHealthIndicator(service, health.status);
        if (!connectionStatus) updateConnectionStatus(true);
    } catch (error) {
        console.error(`Error checking ${service} health:`, error);
        updateHealthIndicator(service, 'down');
        updateConnectionStatus(false);
    }
}

function updateHealthIndicator(service, status) {
    console.log(`Updating health indicator for ${service} to ${status}`);  // Debug log
    const indicator = document.getElementById(`${service}Health`);
    console.log(`Found indicator element:`, indicator);  // Debug log
    if (indicator) {
        const newClass = `health-indicator ${status === 'up' ? 'health-up' : 'health-down'}`;
        console.log(`Setting class to: ${newClass}`);  // Debug log
        indicator.className = newClass;
    }
}

// Update system metrics
async function updateSystemMetrics() {
    try {
        const response = await fetchWithRetry('/system-stats');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const stats = await response.json();
        
        // Debug log
        console.log('Received stats:', stats);
        
        // Update CPU stat
        const cpuStat = document.getElementById('cpuStat');
        if (cpuStat && stats.cpu_percent !== undefined) {
            cpuStat.textContent = `[cpu: ${stats.cpu_percent.toFixed(1)}%]`;
        }
        
        // Update Memory stat
        const memStat = document.getElementById('memStat');
        if (memStat && stats.memory_percent !== undefined) {
            memStat.textContent = `[mem: ${stats.memory_percent.toFixed(1)}%]`;
        }
        
        // Update Disk stat
        const diskStat = document.getElementById('diskStat');
        if (diskStat && stats.disk_percent !== undefined) {
            diskStat.textContent = `[disk: ${stats.disk_percent.toFixed(1)}%]`;
        }
    } catch (error) {
        console.error('Error updating system metrics:', error);
    }
}

// Add polling for system metrics
setInterval(updateSystemMetrics, 2000);  // Update every 2 seconds

// Initial update
updateSystemMetrics();

// Update the updateSystemStats function
async function updateSystemStats() {
    try {
        const [statsResponse, uptimeResponse] = await Promise.all([
            fetch('/system-stats'),
            fetch('/uptime')
        ]);
        
        if (!statsResponse.ok || !uptimeResponse.ok) {
            throw new Error('Failed to fetch system stats');
        }
        
        const stats = await statsResponse.json();
        const uptime = await uptimeResponse.json();
        
        updateSystemMetrics(stats);
    } catch (error) {
        console.error('Error updating system stats:', error);
    }
}

// Update initialization
async function initializeDashboard() {
    try {
        showLoading();
        const [configResponse, systemInfoResponse] = await Promise.all([
            fetch('/dashboard-config'),
            fetch('/system-info')
        ]);

        if (!configResponse.ok || !systemInfoResponse.ok) {
            throw new Error('Failed to fetch initial data');
        }

        const [config, systemInfo] = await Promise.all([
            configResponse.json(),
            systemInfoResponse.json()
        ]);

        updateConfig(config);
        updateSystemInfo(systemInfo);
        checkAllHealth();
    } catch (error) {
        console.error('Error initializing dashboard:', error);
        // Show error state to user
        if (domElements.systemInfo) {
            domElements.systemInfo.textContent = 'Error loading dashboard';
        }
    } finally {
        hideLoading();
    }
}

// Update system information
function updateSystemInfo(systemInfo) {
    if (domElements.systemInfo) {
        domElements.systemInfo.textContent = `${systemInfo.hostname} (${systemInfo.ipAddress})`;
    }
}

// Check health of all services
function checkAllHealth() {
    const services = [
        'grafana', 'influx', 'portainer', 'redis', 
        'telegraf', 'vscode', 'ecat', 'controls'
    ];
    
    console.log('Checking health for services:', services);  // Debug log
    services.forEach(service => {
        checkHealth(service).catch(error => {
            console.error(`Failed to check ${service} health:`, error);
            updateHealthIndicator(service, 'down');
        });
    });
}

// Update configuration
function updateConfig(config) {
    const links = {
        'grafanaLink': config.urls.grafana,
        'vscodeLink': config.urls.vscode,
        'influxLink': config.urls.influxdb,
        'portainerLink': config.urls.portainer,
        'redisLink': config.urls.redis,
        'telegrafLink': config.urls.telegraf,
        'ecatLink': config.urls.ecat,
        'controlsLink': config.urls.controls
    };
    
    for (const [id, url] of Object.entries(links)) {
        const element = document.getElementById(id);
        if (element && url) {
            element.href = url;
        }
    }
}

// Add stats polling interval
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    setInterval(checkAllHealth, HEALTH_CHECK_INTERVAL);
    setInterval(updateSystemStats, 60000);  // Update stats every minute
}); 