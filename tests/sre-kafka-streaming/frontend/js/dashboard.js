/**
 * SRE Agent Dashboard - Main Controller
 * Handles core dashboard functionality, real-time updates, and system status
 */

class SREDashboard {
    constructor() {
        this.isInitialized = false;
        this.updateInterval = null;
        this.systemStartTime = null;
        this.currentMetrics = {
            logsProcessed: 0,
            anomaliesDetected: 0,
            autoResolved: 0,
            pagesSent: 0,
            avgResponseTime: 0,
            successRate: 0
        };
        this.previousMetrics = { ...this.currentMetrics };
        this.chartTimeframe = '6h';
        this.agentChartType = 'accuracy';
        
        this.init();
    }

    async init() {
        try {
            this.showLoading(true);
            
            // Initialize system start time
            this.systemStartTime = new Date();
            
            // Initialize all components
            await this.initializeComponents();
            
            // Start real-time updates
            this.startRealTimeUpdates();
            
            // Update initial display
            this.updateDisplay();
            
            this.isInitialized = true;
            this.showLoading(false);
            
            console.log('SRE Dashboard initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize dashboard:', error);
            this.showNotification('error', 'Initialization Failed', 'Failed to initialize dashboard. Please refresh the page.');
            this.showLoading(false);
        }
    }

    async initializeComponents() {
        // Initialize charts
        await this.initializeCharts();
        
        // Initialize incidents
        await this.initializeIncidents();
        
        // Initialize agent status
        await this.initializeAgentStatus();
        
        // Initialize controls
        this.initializeControls();
        
        // Set up event listeners
        this.setupEventListeners();
    }

    async initializeCharts() {
        try {
            // Initialize charts using the charts manager
            if (window.chartsManager) {
                await window.chartsManager.initializeCharts();
            }
        } catch (error) {
            console.error('Failed to initialize charts:', error);
        }
    }

    async initializeIncidents() {
        try {
            await this.loadIncidents();
        } catch (error) {
            console.error('Failed to initialize incidents:', error);
        }
    }

    async initializeAgentStatus() {
        try {
            await this.loadAgentStatus();
        } catch (error) {
            console.error('Failed to initialize agent status:', error);
        }
    }

    initializeControls() {
        // Initialize slider value display
        const anomalyThreshold = document.getElementById('anomalyThreshold');
        const anomalyThresholdValue = document.getElementById('anomalyThresholdValue');
        
        anomalyThreshold.addEventListener('input', (e) => {
            anomalyThresholdValue.textContent = `${e.target.value}%`;
        });
        
        // Load current settings
        this.loadSettings();
    }

    setupEventListeners() {
        // Window resize handler
        window.addEventListener('resize', this.handleResize.bind(this));
        
        // Keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyboardShortcuts.bind(this));
        
        // Auto-refresh toggle
        document.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this));
    }

    startRealTimeUpdates() {
        // Update metrics every 5 seconds
        this.updateInterval = setInterval(async () => {
            if (!document.hidden) {
                await this.updateMetrics();
                this.updateDisplay();
                this.updateUptime();
            }
        }, 5000);
        
        // Update charts every 30 seconds
        setInterval(async () => {
            if (!document.hidden) {
                await this.updateCharts();
            }
        }, 30000);
        
        // Update incidents every 10 seconds
        setInterval(async () => {
            if (!document.hidden) {
                await this.loadIncidents();
            }
        }, 10000);
        
        // Update agent status every 15 seconds
        setInterval(async () => {
            if (!document.hidden) {
                await this.loadAgentStatus();
            }
        }, 15000);
    }

    async updateMetrics() {
        try {
            const response = await fetch('/api/dashboard/metrics');
            if (response.ok) {
                const data = await response.json();
                this.previousMetrics = { ...this.currentMetrics };
                this.currentMetrics = data;
            }
        } catch (error) {
            console.error('Failed to update metrics:', error);
        }
    }

    updateDisplay() {
        // Update metric cards
        this.updateMetricCard('logsProcessed', this.currentMetrics.logsProcessed);
        this.updateMetricCard('anomaliesDetected', this.currentMetrics.anomaliesDetected);
        this.updateMetricCard('autoResolved', this.currentMetrics.autoResolved);
        this.updateMetricCard('pagesSent', this.currentMetrics.pagesSent);
        this.updateMetricCard('avgResponseTime', `${this.currentMetrics.avgResponseTime}ms`);
        this.updateMetricCard('successRate', `${this.currentMetrics.successRate}%`);
        
        // Update trends
        this.updateTrends();
        
        // Update system status
        this.updateSystemStatus();
        
        // Update timestamp
        this.updateTimestamp();
    }

    updateMetricCard(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    updateTrends() {
        const trends = [
            { id: 'logsTrend', current: this.currentMetrics.logsProcessed, previous: this.previousMetrics.logsProcessed },
            { id: 'anomaliesTrend', current: this.currentMetrics.anomaliesDetected, previous: this.previousMetrics.anomaliesDetected },
            { id: 'autoResolvedTrend', current: this.currentMetrics.autoResolved, previous: this.previousMetrics.autoResolved },
            { id: 'pagesTrend', current: this.currentMetrics.pagesSent, previous: this.previousMetrics.pagesSent },
            { id: 'responseTimeTrend', current: this.currentMetrics.avgResponseTime, previous: this.previousMetrics.avgResponseTime },
            { id: 'successRateTrend', current: this.currentMetrics.successRate, previous: this.previousMetrics.successRate }
        ];
        
        trends.forEach(trend => {
            const element = document.getElementById(trend.id);
            if (element) {
                const change = trend.current - trend.previous;
                const changePercent = trend.previous > 0 ? ((change / trend.previous) * 100) : 0;
                
                const icon = element.querySelector('i');
                const span = element.querySelector('span');
                
                if (change > 0) {
                    icon.className = 'fas fa-arrow-up';
                    element.className = 'metric-trend positive';
                    span.textContent = `+${change > 1000 ? (change / 1000).toFixed(1) + 'k' : change}/min`;
                } else if (change < 0) {
                    icon.className = 'fas fa-arrow-down';
                    element.className = 'metric-trend negative';
                    span.textContent = `${change > -1000 ? (change / 1000).toFixed(1) + 'k' : change}/min`;
                } else {
                    icon.className = 'fas fa-minus';
                    element.className = 'metric-trend neutral';
                    span.textContent = '0/min';
                }
            }
        });
    }

    updateSystemStatus() {
        const statusIndicator = document.getElementById('systemStatus');
        const statusText = document.getElementById('statusText');
        
        // Determine system status based on metrics
        const isHealthy = this.currentMetrics.successRate > 95 && this.currentMetrics.avgResponseTime < 1000;
        const hasWarnings = this.currentMetrics.anomaliesDetected > 10;
        
        if (isHealthy && !hasWarnings) {
            statusIndicator.className = 'status-indicator online';
            statusText.textContent = 'System Healthy';
        } else if (hasWarnings) {
            statusIndicator.className = 'status-indicator warning';
            statusText.textContent = 'Warnings Detected';
        } else {
            statusIndicator.className = 'status-indicator offline';
            statusText.textContent = 'System Issues';
        }
    }

    updateTimestamp() {
        const timestampElement = document.getElementById('currentTime');
        if (timestampElement) {
            timestampElement.textContent = new Date().toLocaleTimeString();
        }
    }

    updateUptime() {
        if (this.systemStartTime) {
            const uptime = Date.now() - this.systemStartTime.getTime();
            const hours = Math.floor(uptime / (1000 * 60 * 60));
            const minutes = Math.floor((uptime % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((uptime % (1000 * 60)) / 1000);
            
            const uptimeElement = document.getElementById('uptime');
            if (uptimeElement) {
                uptimeElement.textContent = `Uptime: ${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }
        }
    }

    async updateCharts() {
        try {
            // Update charts using the charts manager
            if (window.chartsManager) {
                await window.chartsManager.updateCharts();
            }
        } catch (error) {
            console.error('Failed to update charts:', error);
        }
    }

    async getLogProcessingData() {
        try {
            const response = await fetch(`/api/charts/log-processing?timeframe=${this.chartTimeframe}`);
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Failed to get log processing data:', error);
        }
        return { labels: [], datasets: [] };
    }

    async getAgentPerformanceData() {
        try {
            const response = await fetch(`/api/charts/agent-performance?type=${this.agentChartType}`);
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Failed to get agent performance data:', error);
        }
        return { labels: [], datasets: [] };
    }

    updateLogProcessingChart(data) {
        if (this.logProcessingChart && data.labels && data.datasets) {
            this.logProcessingChart.data.labels = data.labels;
            this.logProcessingChart.data.datasets = data.datasets;
            this.logProcessingChart.update('none');
        }
    }

    updateAgentPerformanceChart(data) {
        if (this.agentPerformanceChart && data.labels && data.datasets) {
            this.agentPerformanceChart.data.labels = data.labels;
            this.agentPerformanceChart.data.datasets = data.datasets;
            this.agentPerformanceChart.update('none');
        }
    }

    getLogProcessingChartConfig() {
        return {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Logs Processed',
                    data: [],
                    borderColor: '#00d4ff',
                    backgroundColor: 'rgba(0, 212, 255, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }, {
                    label: 'Anomalies Detected',
                    data: [],
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#f8fafc'
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: '#cbd5e1'
                        },
                        grid: {
                            color: '#334155'
                        }
                    },
                    y: {
                        ticks: {
                            color: '#cbd5e1'
                        },
                        grid: {
                            color: '#334155'
                        }
                    }
                }
            }
        };
    }

    getAgentPerformanceChartConfig() {
        return {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Performance',
                    data: [],
                    backgroundColor: [
                        '#00d4ff',
                        '#7c3aed',
                        '#10b981',
                        '#f59e0b',
                        '#ef4444',
                        '#3b82f6'
                    ],
                    borderWidth: 0,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: '#cbd5e1'
                        },
                        grid: {
                            color: '#334155'
                        }
                    },
                    y: {
                        ticks: {
                            color: '#cbd5e1'
                        },
                        grid: {
                            color: '#334155'
                        }
                    }
                }
            }
        };
    }

    handleResize() {
        // Debounce resize events
        clearTimeout(this.resizeTimeout);
        this.resizeTimeout = setTimeout(() => {
            if (this.logProcessingChart) {
                this.logProcessingChart.resize();
            }
            if (this.agentPerformanceChart) {
                this.agentPerformanceChart.resize();
            }
        }, 250);
    }

    handleKeyboardShortcuts(event) {
        // Ctrl/Cmd + R to refresh
        if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
            event.preventDefault();
            this.refreshAll();
        }
        
        // Ctrl/Cmd + K to focus search
        if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
            event.preventDefault();
            // Focus search if implemented
        }
        
        // Escape to close sidebar
        if (event.key === 'Escape') {
            this.closeSidebar();
        }
    }

    handleVisibilityChange() {
        if (document.hidden) {
            // Pause updates when tab is not visible
            if (this.updateInterval) {
                clearInterval(this.updateInterval);
                this.updateInterval = null;
            }
        } else {
            // Resume updates when tab becomes visible
            if (!this.updateInterval) {
                this.startRealTimeUpdates();
            }
        }
    }

    async refreshAll() {
        this.showLoading(true);
        
        try {
            await Promise.all([
                this.updateMetrics(),
                this.loadIncidents(),
                this.loadAgentStatus(),
                this.updateCharts()
            ]);
            
            this.updateDisplay();
            this.showNotification('success', 'Refresh Complete', 'All data has been refreshed successfully.');
            
        } catch (error) {
            console.error('Failed to refresh data:', error);
            this.showNotification('error', 'Refresh Failed', 'Failed to refresh some data. Please try again.');
        } finally {
            this.showLoading(false);
        }
    }

    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            if (show) {
                overlay.classList.add('show');
            } else {
                overlay.classList.remove('show');
            }
        }
    }

    showNotification(type, title, message) {
        const container = document.getElementById('notificationsContainer');
        if (!container) return;
        
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-header">
                <span class="notification-title">${title}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="notification-message">${message}</div>
        `;
        
        container.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    closeSidebar() {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.classList.remove('open');
        }
    }

    loadSettings() {
        // Load settings from localStorage or API
        const settings = JSON.parse(localStorage.getItem('sreDashboardSettings') || '{}');
        
        if (settings.anomalyThreshold) {
            document.getElementById('anomalyThreshold').value = settings.anomalyThreshold;
            document.getElementById('anomalyThresholdValue').textContent = `${settings.anomalyThreshold}%`;
        }
        
        if (settings.autoResolution !== undefined) {
            document.getElementById('autoResolution').checked = settings.autoResolution;
        }
        
        if (settings.pagingLevel) {
            document.getElementById('pagingLevel').value = settings.pagingLevel;
        }
        
        if (settings.processingRate) {
            document.getElementById('processingRate').value = settings.processingRate;
        }
    }

    saveSettings() {
        const settings = {
            anomalyThreshold: document.getElementById('anomalyThreshold').value,
            autoResolution: document.getElementById('autoResolution').checked,
            pagingLevel: document.getElementById('pagingLevel').value,
            processingRate: document.getElementById('processingRate').value
        };
        
        localStorage.setItem('sreDashboardSettings', JSON.stringify(settings));
    }
}

// Global functions for HTML onclick handlers
function updateChartTimeframe(timeframe) {
    if (window.chartsManager) {
        window.chartsManager.setTimeframe(timeframe);
        
        // Update active button
        document.querySelectorAll('.chart-controls .btn-small').forEach(btn => {
            btn.classList.remove('active');
        });
        event.target.classList.add('active');
    }
}

function updateAgentChart(type) {
    if (window.chartsManager) {
        window.chartsManager.setAgentChartType(type);
        
        // Update active button
        document.querySelectorAll('.chart-controls .btn-small').forEach(btn => {
            btn.classList.remove('active');
        });
        event.target.classList.add('active');
    }
}

function refreshIncidents() {
    if (window.dashboard) {
        window.dashboard.loadIncidents();
    }
}

function refreshAgentStatus() {
    if (window.dashboard) {
        window.dashboard.loadAgentStatus();
    }
}

function toggleIncidentFilters() {
    // Implement incident filtering
    console.log('Toggle incident filters');
}

function applySettings() {
    if (window.dashboard) {
        window.dashboard.saveSettings();
        window.dashboard.showNotification('success', 'Settings Applied', 'System settings have been updated successfully.');
    }
}

function resetSettings() {
    if (window.dashboard) {
        localStorage.removeItem('sreDashboardSettings');
        window.dashboard.loadSettings();
        window.dashboard.showNotification('info', 'Settings Reset', 'Settings have been reset to defaults.');
    }
}

function closeSidebar() {
    if (window.dashboard) {
        window.dashboard.closeSidebar();
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new SREDashboard();
}); 