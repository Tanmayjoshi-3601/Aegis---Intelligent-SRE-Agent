/**
 * SRE Agent Dashboard - Agents Management
 * Handles agent status display and monitoring
 */

class AgentsManager {
    constructor() {
        this.agents = [];
        this.agentStats = {};
        this.updateInterval = null;
    }

    async loadAgentStatus() {
        try {
            const response = await fetch('/api/agents/status');
            if (response.ok) {
                const data = await response.json();
                this.agents = data.agents || [];
                this.agentStats = data.stats || {};
                this.renderAgentStatus();
            }
        } catch (error) {
            console.error('Failed to load agent status:', error);
            // Use mock data for demonstration
            this.loadMockAgentData();
        }
    }

    loadMockAgentData() {
        this.agents = [
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
            },
            {
                name: 'RAG Agent',
                status: 'online',
                icon: 'fas fa-book',
                description: 'Knowledge-based resolution',
                metrics: {
                    throughput: 156,
                    accuracy: 91.5,
                    latency: 120
                },
                lastSeen: new Date().toISOString(),
                version: '1.0.9',
                uptime: '3d 2h 47m'
            },
            {
                name: 'Advanced LLM',
                status: 'warning',
                icon: 'fas fa-robot',
                description: 'Advanced problem solving',
                metrics: {
                    throughput: 23,
                    accuracy: 88.9,
                    latency: 850
                },
                lastSeen: new Date(Date.now() - 300000).toISOString(),
                version: '2.1.0',
                uptime: '5h 12m'
            },
            {
                name: 'Database Agent',
                status: 'online',
                icon: 'fas fa-database',
                description: 'Log storage and retrieval',
                metrics: {
                    throughput: 2100,
                    accuracy: 99.9,
                    latency: 12
                },
                lastSeen: new Date().toISOString(),
                version: '1.3.1',
                uptime: '7d 3h 28m'
            },
            {
                name: 'Paging Agent',
                status: 'offline',
                icon: 'fas fa-bell',
                description: 'Human notification system',
                metrics: {
                    throughput: 0,
                    accuracy: 0,
                    latency: 0
                },
                lastSeen: new Date(Date.now() - 1800000).toISOString(),
                version: '1.0.5',
                uptime: '0h 0m'
            }
        ];

        this.agentStats = {
            total_agents: 6,
            online_agents: 4,
            offline_agents: 1,
            warning_agents: 1,
            total_throughput: 4319,
            avg_accuracy: 94.4,
            avg_latency: 175
        };

        this.renderAgentStatus();
    }

    renderAgentStatus() {
        const container = document.getElementById('agentGrid');
        if (!container) return;

        container.innerHTML = this.agents.map(agent => this.renderAgentCard(agent)).join('');
    }

    renderAgentCard(agent) {
        const statusClass = agent.status;
        const lastSeen = this.getTimeAgo(agent.lastSeen);
        
        return `
            <div class="agent-card ${statusClass}" onclick="window.agentsManager.showAgentDetails('${agent.name}')">
                <div class="agent-icon">
                    <i class="${agent.icon}"></i>
                </div>
                <div class="agent-name">${agent.name}</div>
                <div class="agent-status">${agent.status.toUpperCase()}</div>
                <div class="agent-metrics">
                    <div class="metric">
                        <span class="metric-label">Throughput:</span>
                        <span class="metric-value">${agent.metrics.throughput}/min</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Accuracy:</span>
                        <span class="metric-value">${agent.metrics.accuracy}%</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Latency:</span>
                        <span class="metric-value">${agent.metrics.latency}ms</span>
                    </div>
                </div>
                <div class="agent-footer">
                    <div class="agent-uptime">
                        <i class="fas fa-clock"></i>
                        <span>${agent.uptime}</span>
                    </div>
                    <div class="agent-version">
                        <i class="fas fa-tag"></i>
                        <span>v${agent.version}</span>
                    </div>
                </div>
            </div>
        `;
    }

    showAgentDetails(agentName) {
        const agent = this.agents.find(a => a.name === agentName);
        if (!agent) return;

        this.openSidebar('agent-details');
        this.renderAgentDetails(agent);
    }

    renderAgentDetails(agent) {
        const sidebar = document.getElementById('sidebar');
        const sidebarTitle = document.getElementById('sidebarTitle');
        const sidebarContent = document.getElementById('sidebarContent');

        if (!sidebar || !sidebarTitle || !sidebarContent) return;

        sidebarTitle.textContent = 'Agent Details';
        sidebar.classList.add('open');

        const lastSeen = this.getTimeAgo(agent.lastSeen);
        const formattedLastSeen = new Date(agent.lastSeen).toLocaleString();

        sidebarContent.innerHTML = `
            <div class="agent-detail-header">
                <div class="agent-detail-icon">
                    <i class="${agent.icon}"></i>
                </div>
                <div class="agent-detail-info">
                    <div class="agent-detail-name">${agent.name}</div>
                    <div class="agent-detail-status ${agent.status}">${agent.status.toUpperCase()}</div>
                </div>
            </div>

            <div class="agent-detail-section">
                <h4><i class="fas fa-info-circle"></i> Overview</h4>
                <p>${agent.description}</p>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Version:</label>
                        <span>v${agent.version}</span>
                    </div>
                    <div class="detail-item">
                        <label>Uptime:</label>
                        <span>${agent.uptime}</span>
                    </div>
                    <div class="detail-item">
                        <label>Last Seen:</label>
                        <span>${formattedLastSeen} (${lastSeen})</span>
                    </div>
                </div>
            </div>

            <div class="agent-detail-section">
                <h4><i class="fas fa-chart-line"></i> Performance Metrics</h4>
                <div class="metrics-grid">
                    <div class="metric-item">
                        <label>Throughput:</label>
                        <span class="metric-value">${agent.metrics.throughput} requests/min</span>
                        <div class="metric-bar">
                            <div class="metric-fill" style="width: ${Math.min(agent.metrics.throughput / 20, 100)}%"></div>
                        </div>
                    </div>
                    <div class="metric-item">
                        <label>Accuracy:</label>
                        <span class="metric-value">${agent.metrics.accuracy}%</span>
                        <div class="metric-bar">
                            <div class="metric-fill" style="width: ${agent.metrics.accuracy}%"></div>
                        </div>
                    </div>
                    <div class="metric-item">
                        <label>Latency:</label>
                        <span class="metric-value">${agent.metrics.latency}ms</span>
                        <div class="metric-bar">
                            <div class="metric-fill" style="width: ${Math.max(100 - (agent.metrics.latency / 10), 0)}%"></div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="agent-detail-section">
                <h4><i class="fas fa-history"></i> Recent Activity</h4>
                <div class="activity-timeline">
                    ${this.generateActivityTimeline(agent)}
                </div>
            </div>

            <div class="agent-detail-section">
                <h4><i class="fas fa-cogs"></i> Configuration</h4>
                <div class="config-grid">
                    <div class="config-item">
                        <label>Model Path:</label>
                        <span>/models/${agent.name.toLowerCase().replace(' ', '_')}</span>
                    </div>
                    <div class="config-item">
                        <label>Confidence Threshold:</label>
                        <span>${this.getConfidenceThreshold(agent.name)}%</span>
                    </div>
                    <div class="config-item">
                        <label>Max Retries:</label>
                        <span>3</span>
                    </div>
                    <div class="config-item">
                        <label>Timeout:</label>
                        <span>30s</span>
                    </div>
                </div>
            </div>

            <div class="agent-detail-actions">
                <button class="btn-primary" onclick="window.agentsManager.restartAgent('${agent.name}')">
                    <i class="fas fa-redo"></i>
                    Restart
                </button>
                <button class="btn-secondary" onclick="window.agentsManager.viewLogs('${agent.name}')">
                    <i class="fas fa-file-alt"></i>
                    View Logs
                </button>
                <button class="btn-secondary" onclick="window.agentsManager.updateAgent('${agent.name}')">
                    <i class="fas fa-download"></i>
                    Update
                </button>
            </div>
        `;
    }

    generateActivityTimeline(agent) {
        const activities = [
            {
                time: new Date(Date.now() - 30000).toLocaleTimeString(),
                event: 'Processed log batch',
                details: 'Handled 45 log entries'
            },
            {
                time: new Date(Date.now() - 120000).toLocaleTimeString(),
                event: 'Anomaly detected',
                details: 'High confidence (94.2%)'
            },
            {
                time: new Date(Date.now() - 300000).toLocaleTimeString(),
                event: 'Health check',
                details: 'Status: Healthy'
            },
            {
                time: new Date(Date.now() - 600000).toLocaleTimeString(),
                event: 'Configuration reload',
                details: 'Updated threshold values'
            }
        ];

        return activities.map(activity => `
            <div class="activity-item">
                <div class="activity-time">${activity.time}</div>
                <div class="activity-content">
                    <div class="activity-event">${activity.event}</div>
                    <div class="activity-details">${activity.details}</div>
                </div>
            </div>
        `).join('');
    }

    getConfidenceThreshold(agentName) {
        const thresholds = {
            'Anomaly Detector': 70,
            'Mitigation Agent': 80,
            'RAG Agent': 75,
            'Advanced LLM': 85,
            'Database Agent': 99,
            'Paging Agent': 90
        };
        return thresholds[agentName] || 80;
    }

    async restartAgent(agentName) {
        try {
            const response = await fetch(`/api/agents/${agentName}/restart`, {
                method: 'POST'
            });
            
            if (response.ok) {
                this.showNotification('success', 'Agent Restarted', `${agentName} has been restarted successfully.`);
                await this.loadAgentStatus();
            }
        } catch (error) {
            console.error('Failed to restart agent:', error);
            this.showNotification('error', 'Restart Failed', `Failed to restart ${agentName}.`);
        }
    }

    async viewLogs(agentName) {
        try {
            const response = await fetch(`/api/agents/${agentName}/logs`);
            if (response.ok) {
                const logs = await response.json();
                this.showLogsModal(agentName, logs);
            }
        } catch (error) {
            console.error('Failed to fetch logs:', error);
            this.showNotification('error', 'Logs Unavailable', `Failed to fetch logs for ${agentName}.`);
        }
    }

    async updateAgent(agentName) {
        try {
            const response = await fetch(`/api/agents/${agentName}/update`, {
                method: 'POST'
            });
            
            if (response.ok) {
                this.showNotification('success', 'Update Started', `Update for ${agentName} has been initiated.`);
                await this.loadAgentStatus();
            }
        } catch (error) {
            console.error('Failed to update agent:', error);
            this.showNotification('error', 'Update Failed', `Failed to update ${agentName}.`);
        }
    }

    showLogsModal(agentName, logs) {
        // Create modal for logs display
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${agentName} Logs</h3>
                    <button class="modal-close" onclick="this.parentElement.parentElement.parentElement.remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="logs-container">
                        ${logs.slice(-50).map(log => `
                            <div class="log-entry">
                                <span class="log-timestamp">${new Date(log.timestamp).toLocaleString()}</span>
                                <span class="log-level ${log.level}">${log.level}</span>
                                <span class="log-message">${log.message}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (modal.parentElement) {
                modal.remove();
            }
        }, 10000);
    }

    openSidebar(type) {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.classList.add('open');
        }
    }

    closeSidebar() {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.classList.remove('open');
        }
    }

    getTimeAgo(timestamp) {
        const now = new Date();
        const time = new Date(timestamp);
        const diffMs = now - time;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        return `${diffDays}d ago`;
    }

    showNotification(type, title, message) {
        if (window.dashboard && window.dashboard.showNotification) {
            window.dashboard.showNotification(type, title, message);
        }
    }

    getAgentStats() {
        return this.agentStats;
    }

    getAgentByName(name) {
        return this.agents.find(agent => agent.name === name);
    }

    getOnlineAgents() {
        return this.agents.filter(agent => agent.status === 'online');
    }

    getOfflineAgents() {
        return this.agents.filter(agent => agent.status === 'offline');
    }

    getWarningAgents() {
        return this.agents.filter(agent => agent.status === 'warning');
    }
}

// Initialize agents manager
window.agentsManager = new AgentsManager(); 