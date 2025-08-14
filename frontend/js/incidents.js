/**
 * SRE Agent Dashboard - Incidents Management
 * Handles incident display, filtering, and interaction
 */

class IncidentsManager {
    constructor() {
        this.incidents = [];
        this.filteredIncidents = [];
        this.filters = {
            severity: 'all',
            service: 'all',
            status: 'all'
        };
        this.currentIncident = null;
    }

    async loadIncidents() {
        try {
            const response = await fetch('/api/incidents');
            if (response.ok) {
                const data = await response.json();
                this.incidents = data.incidents || [];
                this.applyFilters();
                this.renderIncidents();
            }
        } catch (error) {
            console.error('Failed to load incidents:', error);
            // Use mock data for demonstration
            this.loadMockIncidents();
        }
    }

    loadMockIncidents() {
        this.incidents = [
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
            },
            {
                id: 'inc-003',
                title: 'Memory Leak Detected',
                severity: 'medium',
                service: 'api-service',
                status: 'resolved',
                timestamp: new Date(Date.now() - 1800000).toISOString(),
                description: 'Gradual increase in memory usage detected over the last hour',
                metrics: {
                    memory_usage: 85,
                    gc_frequency: 0.1,
                    heap_size: 2048
                },
                agent_analysis: {
                    anomaly_confidence: 0.87,
                    mitigation_attempted: true,
                    auto_resolved: true
                }
            },
            {
                id: 'inc-004',
                title: 'Network Latency Spike',
                severity: 'low',
                service: 'load-balancer',
                status: 'resolved',
                timestamp: new Date(Date.now() - 3600000).toISOString(),
                description: 'Network latency increased by 200ms for external requests',
                metrics: {
                    latency: 450,
                    packet_loss: 0.1,
                    bandwidth_usage: 65
                },
                agent_analysis: {
                    anomaly_confidence: 0.75,
                    mitigation_attempted: false,
                    auto_resolved: true
                }
            },
            {
                id: 'inc-005',
                title: 'Service Unavailable',
                severity: 'critical',
                service: 'payment-service',
                status: 'active',
                timestamp: new Date(Date.now() - 120000).toISOString(),
                description: 'Payment service is not responding to health checks',
                metrics: {
                    health_check_status: 'failed',
                    error_rate: 100,
                    response_time: 0
                },
                agent_analysis: {
                    anomaly_confidence: 1.0,
                    mitigation_attempted: true,
                    auto_resolved: false
                }
            }
        ];
        this.applyFilters();
        this.renderIncidents();
    }

    applyFilters() {
        this.filteredIncidents = this.incidents.filter(incident => {
            const severityMatch = this.filters.severity === 'all' || incident.severity === this.filters.severity;
            const serviceMatch = this.filters.service === 'all' || incident.service === this.filters.service;
            const statusMatch = this.filters.status === 'all' || incident.status === this.filters.status;
            
            return severityMatch && serviceMatch && statusMatch;
        });
    }

    renderIncidents() {
        const container = document.getElementById('incidentsList');
        if (!container) return;

        if (this.filteredIncidents.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-check-circle"></i>
                    <h4>No Active Incidents</h4>
                    <p>All systems are operating normally</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.filteredIncidents
            .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
            .map(incident => this.renderIncidentCard(incident))
            .join('');
    }

    renderIncidentCard(incident) {
        const timeAgo = this.getTimeAgo(incident.timestamp);
        const severityClass = incident.severity;
        const statusClass = incident.status;
        
        return `
            <div class="incident-item ${severityClass} ${statusClass}" 
                 onclick="window.incidentsManager.showIncidentDetails('${incident.id}')">
                <div class="incident-header">
                    <div class="incident-title">${incident.title}</div>
                    <div class="incident-severity ${severityClass}">${incident.severity}</div>
                </div>
                <div class="incident-details">
                    <div class="incident-service">
                        <i class="fas fa-server"></i>
                        <span>${this.formatServiceName(incident.service)}</span>
                    </div>
                    <div class="incident-description">${incident.description}</div>
                </div>
                <div class="incident-metrics">
                    <div class="metric">
                        <i class="fas fa-clock"></i>
                        <span>${timeAgo}</span>
                    </div>
                    <div class="metric">
                        <i class="fas fa-brain"></i>
                        <span>${Math.round(incident.agent_analysis.anomaly_confidence * 100)}% confidence</span>
                    </div>
                    <div class="metric">
                        <i class="fas fa-robot"></i>
                        <span>${incident.agent_analysis.auto_resolved ? 'Auto-resolved' : 'Manual intervention'}</span>
                    </div>
                </div>
                <div class="incident-actions">
                    <button class="btn-action" onclick="event.stopPropagation(); window.incidentsManager.acknowledgeIncident('${incident.id}')">
                        <i class="fas fa-check"></i>
                        Acknowledge
                    </button>
                    <button class="btn-action" onclick="event.stopPropagation(); window.incidentsManager.resolveIncident('${incident.id}')">
                        <i class="fas fa-flag-checkered"></i>
                        Resolve
                    </button>
                </div>
            </div>
        `;
    }

    showIncidentDetails(incidentId) {
        const incident = this.incidents.find(inc => inc.id === incidentId);
        if (!incident) return;

        this.currentIncident = incident;
        this.openSidebar('incident-details');
        this.renderIncidentDetails(incident);
    }

    renderIncidentDetails(incident) {
        const sidebar = document.getElementById('sidebar');
        const sidebarTitle = document.getElementById('sidebarTitle');
        const sidebarContent = document.getElementById('sidebarContent');

        if (!sidebar || !sidebarTitle || !sidebarContent) return;

        sidebarTitle.textContent = 'Incident Details';
        sidebar.classList.add('open');

        const timeAgo = this.getTimeAgo(incident.timestamp);
        const formattedTime = new Date(incident.timestamp).toLocaleString();

        sidebarContent.innerHTML = `
            <div class="incident-detail-header">
                <div class="incident-detail-title">${incident.title}</div>
                <div class="incident-detail-severity ${incident.severity}">${incident.severity.toUpperCase()}</div>
            </div>
            
            <div class="incident-detail-section">
                <h4><i class="fas fa-info-circle"></i> Overview</h4>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Service:</label>
                        <span>${this.formatServiceName(incident.service)}</span>
                    </div>
                    <div class="detail-item">
                        <label>Status:</label>
                        <span class="status-${incident.status}">${incident.status}</span>
                    </div>
                    <div class="detail-item">
                        <label>Detected:</label>
                        <span>${formattedTime} (${timeAgo})</span>
                    </div>
                    <div class="detail-item">
                        <label>Confidence:</label>
                        <span>${Math.round(incident.agent_analysis.anomaly_confidence * 100)}%</span>
                    </div>
                </div>
            </div>

            <div class="incident-detail-section">
                <h4><i class="fas fa-exclamation-triangle"></i> Description</h4>
                <p>${incident.description}</p>
            </div>

            <div class="incident-detail-section">
                <h4><i class="fas fa-chart-line"></i> Metrics</h4>
                <div class="metrics-grid">
                    ${Object.entries(incident.metrics).map(([key, value]) => `
                        <div class="metric-item">
                            <label>${this.formatMetricName(key)}:</label>
                            <span class="metric-value">${this.formatMetricValue(key, value)}</span>
                        </div>
                    `).join('')}
                </div>
            </div>

            <div class="incident-detail-section">
                <h4><i class="fas fa-robot"></i> Agent Analysis</h4>
                <div class="analysis-grid">
                    <div class="analysis-item">
                        <label>Anomaly Confidence:</label>
                        <span>${Math.round(incident.agent_analysis.anomaly_confidence * 100)}%</span>
                    </div>
                    <div class="analysis-item">
                        <label>Mitigation Attempted:</label>
                        <span>${incident.agent_analysis.mitigation_attempted ? 'Yes' : 'No'}</span>
                    </div>
                    <div class="analysis-item">
                        <label>Auto-Resolved:</label>
                        <span>${incident.agent_analysis.auto_resolved ? 'Yes' : 'No'}</span>
                    </div>
                </div>
            </div>

            <div class="incident-detail-section">
                <h4><i class="fas fa-history"></i> Timeline</h4>
                <div class="timeline">
                    <div class="timeline-item">
                        <div class="timeline-marker"></div>
                        <div class="timeline-content">
                            <div class="timeline-time">${formattedTime}</div>
                            <div class="timeline-event">Incident detected by anomaly detection agent</div>
                        </div>
                    </div>
                    ${incident.agent_analysis.mitigation_attempted ? `
                        <div class="timeline-item">
                            <div class="timeline-marker"></div>
                            <div class="timeline-content">
                                <div class="timeline-time">${new Date(Date.now() - 60000).toLocaleTimeString()}</div>
                                <div class="timeline-event">Mitigation agent attempted resolution</div>
                            </div>
                        </div>
                    ` : ''}
                    ${incident.status === 'resolved' ? `
                        <div class="timeline-item">
                            <div class="timeline-marker resolved"></div>
                            <div class="timeline-content">
                                <div class="timeline-time">${new Date(Date.now() - 30000).toLocaleTimeString()}</div>
                                <div class="timeline-event">Incident resolved</div>
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>

            <div class="incident-detail-actions">
                <button class="btn-primary" onclick="window.incidentsManager.acknowledgeIncident('${incident.id}')">
                    <i class="fas fa-check"></i>
                    Acknowledge
                </button>
                <button class="btn-secondary" onclick="window.incidentsManager.resolveIncident('${incident.id}')">
                    <i class="fas fa-flag-checkered"></i>
                    Resolve
                </button>
                <button class="btn-secondary" onclick="window.incidentsManager.escalateIncident('${incident.id}')">
                    <i class="fas fa-arrow-up"></i>
                    Escalate
                </button>
            </div>
        `;
    }

    async acknowledgeIncident(incidentId) {
        try {
            const response = await fetch(`/api/incidents/${incidentId}/acknowledge`, {
                method: 'POST'
            });
            
            if (response.ok) {
                this.showNotification('success', 'Incident Acknowledged', 'The incident has been acknowledged.');
                await this.loadIncidents();
            }
        } catch (error) {
            console.error('Failed to acknowledge incident:', error);
            this.showNotification('error', 'Acknowledgment Failed', 'Failed to acknowledge the incident.');
        }
    }

    async resolveIncident(incidentId) {
        try {
            const response = await fetch(`/api/incidents/${incidentId}/resolve`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    resolution_notes: 'Resolved via dashboard'
                })
            });
            
            if (response.ok) {
                this.showNotification('success', 'Incident Resolved', 'The incident has been marked as resolved.');
                await this.loadIncidents();
                this.closeSidebar();
            }
        } catch (error) {
            console.error('Failed to resolve incident:', error);
            this.showNotification('error', 'Resolution Failed', 'Failed to resolve the incident.');
        }
    }

    async escalateIncident(incidentId) {
        try {
            const response = await fetch(`/api/incidents/${incidentId}/escalate`, {
                method: 'POST'
            });
            
            if (response.ok) {
                this.showNotification('success', 'Incident Escalated', 'The incident has been escalated to the on-call team.');
                await this.loadIncidents();
            }
        } catch (error) {
            console.error('Failed to escalate incident:', error);
            this.showNotification('error', 'Escalation Failed', 'Failed to escalate the incident.');
        }
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

    formatServiceName(service) {
        return service.split('-').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }

    formatMetricName(metric) {
        return metric.split('_').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }

    formatMetricValue(metric, value) {
        if (metric.includes('usage') || metric.includes('rate')) {
            return `${value}%`;
        }
        if (metric.includes('time') || metric.includes('latency')) {
            return `${value}ms`;
        }
        if (metric.includes('size')) {
            return `${value}MB`;
        }
        if (metric === 'health_check_status') {
            return value === 'failed' ? 'Failed' : 'Healthy';
        }
        return value;
    }

    showNotification(type, title, message) {
        if (window.dashboard && window.dashboard.showNotification) {
            window.dashboard.showNotification(type, title, message);
        }
    }

    setFilter(type, value) {
        this.filters[type] = value;
        this.applyFilters();
        this.renderIncidents();
    }

    clearFilters() {
        this.filters = {
            severity: 'all',
            service: 'all',
            status: 'all'
        };
        this.applyFilters();
        this.renderIncidents();
    }
}

// Initialize incidents manager
window.incidentsManager = new IncidentsManager(); 