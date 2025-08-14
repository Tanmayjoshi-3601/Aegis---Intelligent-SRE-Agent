/**
 * SRE Agent Dashboard - API Client
 * Handles all backend communication and data fetching
 */

class APIClient {
    constructor() {
        this.baseURL = '/api';
        this.timeout = 10000;
        this.retries = 3;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            timeout: this.timeout,
            ...options
        };

        for (let attempt = 1; attempt <= this.retries; attempt++) {
            try {
                const response = await fetch(url, config);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                return await response.json();
            } catch (error) {
                if (attempt === this.retries) {
                    throw error;
                }
                
                // Wait before retrying (exponential backoff)
                await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
            }
        }
    }

    // Dashboard Metrics
    async getDashboardMetrics() {
        return this.request('/dashboard/metrics');
    }

    async getSystemStatus() {
        return this.request('/dashboard/status');
    }

    // Charts Data
    async getLogProcessingData(timeframe = '6h') {
        return this.request(`/charts/log-processing?timeframe=${timeframe}`);
    }

    async getAgentPerformanceData(type = 'accuracy') {
        return this.request(`/charts/agent-performance?type=${type}`);
    }

    async getAnomalyTrends(timeframe = '24h') {
        return this.request(`/charts/anomaly-trends?timeframe=${timeframe}`);
    }

    // Incidents
    async getIncidents(filters = {}) {
        const params = new URLSearchParams(filters);
        return this.request(`/incidents?${params}`);
    }

    async getIncident(incidentId) {
        return this.request(`/incidents/${incidentId}`);
    }

    async acknowledgeIncident(incidentId) {
        return this.request(`/incidents/${incidentId}/acknowledge`, {
            method: 'POST'
        });
    }

    async resolveIncident(incidentId, resolutionNotes = '') {
        return this.request(`/incidents/${incidentId}/resolve`, {
            method: 'POST',
            body: JSON.stringify({ resolution_notes: resolutionNotes })
        });
    }

    async escalateIncident(incidentId) {
        return this.request(`/incidents/${incidentId}/escalate`, {
            method: 'POST'
        });
    }

    // Agents
    async getAgentStatus() {
        return this.request('/agents/status');
    }

    async getAgentDetails(agentName) {
        return this.request(`/agents/${agentName}`);
    }

    async restartAgent(agentName) {
        return this.request(`/agents/${agentName}/restart`, {
            method: 'POST'
        });
    }

    async updateAgent(agentName) {
        return this.request(`/agents/${agentName}/update`, {
            method: 'POST'
        });
    }

    async getAgentLogs(agentName, lines = 100) {
        return this.request(`/agents/${agentName}/logs?lines=${lines}`);
    }

    // Configuration
    async getConfiguration() {
        return this.request('/config');
    }

    async updateConfiguration(config) {
        return this.request('/config', {
            method: 'PUT',
            body: JSON.stringify(config)
        });
    }

    // System Controls
    async applySettings(settings) {
        return this.request('/settings', {
            method: 'POST',
            body: JSON.stringify(settings)
        });
    }

    async getSystemStats() {
        return this.request('/stats');
    }

    // Health Checks
    async healthCheck() {
        return this.request('/health');
    }

    // Mock Data for Development
    getMockDashboardMetrics() {
        return {
            logsProcessed: 15420,
            anomaliesDetected: 23,
            autoResolved: 18,
            pagesSent: 5,
            avgResponseTime: 245,
            successRate: 96.8
        };
    }

    getMockLogProcessingData(timeframe = '6h') {
        const now = new Date();
        const labels = [];
        const logsData = [];
        const anomaliesData = [];

        // Generate mock data points
        for (let i = 23; i >= 0; i--) {
            const time = new Date(now.getTime() - i * 15 * 60 * 1000);
            labels.push(time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
            
            // Generate realistic log processing data
            const baseLogs = 600 + Math.random() * 200;
            logsData.push(Math.round(baseLogs));
            
            // Generate anomaly data (spikes)
            const baseAnomalies = 0.5 + Math.random() * 2;
            const spike = Math.random() > 0.9 ? Math.random() * 5 : 0;
            anomaliesData.push(Math.round(baseAnomalies + spike));
        }

        return {
            labels,
            datasets: [
                {
                    label: 'Logs Processed',
                    data: logsData,
                    borderColor: '#00d4ff',
                    backgroundColor: 'rgba(0, 212, 255, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Anomalies Detected',
                    data: anomaliesData,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }
            ]
        };
    }

    getMockAgentPerformanceData(type = 'accuracy') {
        const agents = ['Anomaly Detector', 'Mitigation Agent', 'RAG Agent', 'Advanced LLM', 'Database Agent', 'Paging Agent'];
        
        let data;
        switch (type) {
            case 'throughput':
                data = [1250, 890, 156, 23, 2100, 0];
                break;
            case 'accuracy':
                data = [94.2, 97.8, 91.5, 88.9, 99.9, 0];
                break;
            case 'latency':
                data = [45, 23, 120, 850, 12, 0];
                break;
            default:
                data = [94.2, 97.8, 91.5, 88.9, 99.9, 0];
        }

        return {
            labels: agents,
            datasets: [{
                label: type.charAt(0).toUpperCase() + type.slice(1),
                data: data,
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
        };
    }

    getMockIncidents() {
        return {
            incidents: [
                {
                    id: 'inc-001',
                    title: 'High CPU Usage Detected',
                    severity: 'high',
                    service: 'web-service',
                    status: 'active',
                    timestamp: new Date(Date.now() - 300000).toISOString(),
                    description: 'CPU usage exceeded 90% threshold for more than 5 minutes',
                    metrics: {
                        cpu_usage: 95,
                        memory_usage: 78,
                        response_time: 1200
                    },
                    agent_analysis: {
                        anomaly_confidence: 0.92,
                        mitigation_attempted: true,
                        auto_resolved: false
                    }
                },
                {
                    id: 'inc-002',
                    title: 'Database Connection Pool Exhausted',
                    severity: 'critical',
                    service: 'database-service',
                    status: 'active',
                    timestamp: new Date(Date.now() - 600000).toISOString(),
                    description: 'All database connections are in use, new requests are being queued',
                    metrics: {
                        connection_pool_usage: 100,
                        query_queue_length: 150,
                        response_time: 5000
                    },
                    agent_analysis: {
                        anomaly_confidence: 0.98,
                        mitigation_attempted: true,
                        auto_resolved: false
                    }
                }
            ]
        };
    }

    getMockAgentStatus() {
        return {
            agents: [
                {
                    name: 'Anomaly Detector',
                    status: 'online',
                    icon: 'fas fa-brain',
                    description: 'ML-based anomaly detection',
                    metrics: {
                        throughput: 1250,
                        accuracy: 94.2,
                        latency: 45
                    },
                    lastSeen: new Date().toISOString(),
                    version: '1.2.3',
                    uptime: '2d 14h 32m'
                },
                {
                    name: 'Mitigation Agent',
                    status: 'online',
                    icon: 'fas fa-tools',
                    description: 'Error classification and routing',
                    metrics: {
                        throughput: 890,
                        accuracy: 97.8,
                        latency: 23
                    },
                    lastSeen: new Date().toISOString(),
                    version: '1.1.7',
                    uptime: '1d 8h 15m'
                }
            ],
            stats: {
                total_agents: 6,
                online_agents: 4,
                offline_agents: 1,
                warning_agents: 1,
                total_throughput: 4319,
                avg_accuracy: 94.4,
                avg_latency: 175
            }
        };
    }

    // Error handling
    handleError(error) {
        console.error('API Error:', error);
        
        // Show user-friendly error message
        const message = this.getErrorMessage(error);
        
        if (window.dashboard && window.dashboard.showNotification) {
            window.dashboard.showNotification('error', 'API Error', message);
        }
        
        return null;
    }

    getErrorMessage(error) {
        if (error.message.includes('Failed to fetch')) {
            return 'Unable to connect to the server. Please check your connection.';
        }
        
        if (error.message.includes('HTTP 404')) {
            return 'The requested resource was not found.';
        }
        
        if (error.message.includes('HTTP 500')) {
            return 'Internal server error. Please try again later.';
        }
        
        if (error.message.includes('HTTP 403')) {
            return 'Access denied. You may not have permission to perform this action.';
        }
        
        return 'An unexpected error occurred. Please try again.';
    }

    // Utility methods
    formatTimestamp(timestamp) {
        return new Date(timestamp).toLocaleString();
    }

    formatDuration(ms) {
        const seconds = Math.floor(ms / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (days > 0) return `${days}d ${hours % 24}h ${minutes % 60}m`;
        if (hours > 0) return `${hours}h ${minutes % 60}m`;
        if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
        return `${seconds}s`;
    }

    formatBytes(bytes) {
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        if (bytes === 0) return '0 Bytes';
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    }

    formatPercentage(value, total) {
        return total > 0 ? Math.round((value / total) * 100 * 100) / 100 : 0;
    }
}

// Initialize API client
window.apiClient = new APIClient(); 