/**
 * SRE Agent Dashboard - Charts Management
 * Handles chart initialization, updates, and interactions
 */

class ChartsManager {
    constructor() {
        this.charts = {};
        this.currentTimeframe = '6h';
        this.currentAgentChartType = 'accuracy';
    }

    async initializeCharts() {
        try {
            // Initialize log processing chart
            this.initializeLogProcessingChart();
            
            // Initialize agent performance chart
            this.initializeAgentPerformanceChart();
            
            // Load initial data
            await this.updateCharts();
            
        } catch (error) {
            console.error('Failed to initialize charts:', error);
        }
    }

    initializeLogProcessingChart() {
        const ctx = document.getElementById('logProcessingChart');
        if (!ctx) return;

        this.charts.logProcessing = new Chart(ctx, {
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
        });
    }

    initializeAgentPerformanceChart() {
        const ctx = document.getElementById('agentPerformanceChart');
        if (!ctx) return;

        this.charts.agentPerformance = new Chart(ctx, {
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
        });
    }

    async updateCharts() {
        try {
            await Promise.all([
                this.updateLogProcessingChart(),
                this.updateAgentPerformanceChart()
            ]);
        } catch (error) {
            console.error('Failed to update charts:', error);
        }
    }

    async updateLogProcessingChart() {
        if (!this.charts.logProcessing) return;

        try {
            const data = await this.getLogProcessingData(this.currentTimeframe);
            this.charts.logProcessing.data.labels = data.labels;
            this.charts.logProcessing.data.datasets = data.datasets;
            this.charts.logProcessing.update('none');
        } catch (error) {
            console.error('Failed to update log processing chart:', error);
        }
    }

    async updateAgentPerformanceChart() {
        if (!this.charts.agentPerformance) return;

        try {
            const data = await this.getAgentPerformanceData(this.currentAgentChartType);
            this.charts.agentPerformance.data.labels = data.labels;
            this.charts.agentPerformance.data.datasets = data.datasets;
            this.charts.agentPerformance.update('none');
        } catch (error) {
            console.error('Failed to update agent performance chart:', error);
        }
    }

    async getLogProcessingData(timeframe = '6h') {
        try {
            const response = await fetch(`/api/charts/log-processing?timeframe=${timeframe}`);
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Failed to get log processing data:', error);
        }
        
        // Return mock data if API fails
        return this.getMockLogProcessingData(timeframe);
    }

    async getAgentPerformanceData(type = 'accuracy') {
        try {
            const response = await fetch(`/api/charts/agent-performance?type=${type}`);
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Failed to get agent performance data:', error);
        }
        
        // Return mock data if API fails
        return this.getMockAgentPerformanceData(type);
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

    setTimeframe(timeframe) {
        this.currentTimeframe = timeframe;
        this.updateLogProcessingChart();
    }

    setAgentChartType(type) {
        this.currentAgentChartType = type;
        this.updateAgentPerformanceChart();
    }

    resizeCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.resize) {
                chart.resize();
            }
        });
    }

    destroyCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.destroy) {
                chart.destroy();
            }
        });
        this.charts = {};
    }
}

// Initialize charts manager
window.chartsManager = new ChartsManager(); 