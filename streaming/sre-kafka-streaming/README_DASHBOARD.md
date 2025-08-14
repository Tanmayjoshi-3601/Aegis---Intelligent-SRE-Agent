# SRE Agent Dashboard

A modern, real-time dashboard for monitoring and managing the Intelligent SRE Agent system. This dashboard provides comprehensive visibility into system performance, incident management, and agent orchestration.

## 🎯 Features

### 📊 **Real-time Monitoring**
- Live metrics dashboard with key performance indicators
- Real-time log processing visualization
- Agent performance tracking and analytics
- System health monitoring with status indicators

### 🚨 **Incident Management**
- Active incident tracking and visualization
- Incident severity classification (Critical, High, Medium, Low)
- Incident timeline and resolution tracking
- Automated vs manual resolution statistics

### 🤖 **Agent Management**
- Real-time agent status monitoring
- Individual agent performance metrics
- Agent restart and update capabilities
- Agent log viewing and debugging

### 📈 **Advanced Analytics**
- Interactive charts with multiple timeframes (1H, 6H, 24H)
- Agent performance comparison (Throughput, Accuracy, Latency)
- Anomaly detection trends
- System response time analysis

### ⚙️ **System Controls**
- Anomaly detection threshold adjustment
- Auto-resolution toggle
- Paging level configuration
- Processing rate control

### 🎨 **Modern UI/UX**
- Dark theme optimized for SRE operations
- Responsive design for all screen sizes
- Real-time notifications and alerts
- Keyboard shortcuts for power users

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   SRE Agents    │
│   Dashboard     │◄──►│   Flask API     │◄──►│   System        │
│   (React/Vanilla)│    │   Server        │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Real-time     │    │   Mock Data     │    │   Kafka         │
│   Updates       │    │   Generation    │    │   Integration   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.7+
- pip3
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd sre-kafka-streaming
   ```

2. **Check prerequisites:**
   ```bash
   ./start_dashboard.sh check
   ```

3. **Install dependencies:**
   ```bash
   ./start_dashboard.sh install
   ```

4. **Start the dashboard:**
   ```bash
   ./start_dashboard.sh start
   ```

5. **Access the dashboard:**
   Open your browser and navigate to: `http://localhost:8081`

### Alternative Manual Start

If you prefer to start manually:

```bash
# Install dependencies
pip3 install -r requirements-dashboard.txt

# Start the server
python3 dashboard_server.py
```

## 📋 Dashboard Components

### 1. **Header Section**
- **System Status**: Real-time health indicator
- **Current Time**: Live timestamp
- **Uptime**: System uptime display

### 2. **Metrics Row**
- **Logs Processed**: Total logs handled by the system
- **Anomalies Detected**: Number of anomalies identified
- **Auto-Resolved**: Incidents resolved automatically
- **Pages Sent**: Human notifications sent
- **Avg Response Time**: Average system response time
- **Success Rate**: Overall system success percentage

### 3. **Charts Section**
- **Real-time Log Processing**: Line chart showing log volume and anomalies over time
- **Agent Performance**: Bar chart comparing agent metrics (throughput, accuracy, latency)

### 4. **Bottom Section**
- **Active Incidents**: List of current incidents with severity indicators
- **Agent Status**: Grid showing all agents and their current status
- **System Controls**: Interactive controls for system configuration

## 🔧 API Endpoints

The dashboard server provides the following API endpoints:

### Dashboard Metrics
- `GET /api/dashboard/metrics` - Get current dashboard metrics
- `GET /api/dashboard/status` - Get system status

### Charts Data
- `GET /api/charts/log-processing?timeframe=6h` - Get log processing chart data
- `GET /api/charts/agent-performance?type=accuracy` - Get agent performance data

### Incidents
- `GET /api/incidents` - Get all incidents
- `GET /api/incidents/{id}` - Get specific incident details
- `POST /api/incidents/{id}/acknowledge` - Acknowledge incident
- `POST /api/incidents/{id}/resolve` - Resolve incident
- `POST /api/incidents/{id}/escalate` - Escalate incident

### Agents
- `GET /api/agents/status` - Get all agent statuses
- `GET /api/agents/{name}` - Get specific agent details
- `POST /api/agents/{name}/restart` - Restart agent
- `POST /api/agents/{name}/update` - Update agent
- `GET /api/agents/{name}/logs` - Get agent logs

### Configuration
- `GET /api/config` - Get system configuration
- `PUT /api/config` - Update system configuration
- `POST /api/settings` - Apply system settings

### System
- `GET /api/stats` - Get system statistics
- `GET /api/health` - Health check endpoint

## 🎮 Usage Guide

### Navigating the Dashboard

1. **View Real-time Metrics**: The top row shows live system metrics with trend indicators
2. **Analyze Charts**: Use the chart controls to switch between timeframes and metrics
3. **Monitor Incidents**: Click on incidents to view detailed information
4. **Manage Agents**: Click on agent cards to view details and perform actions
5. **Adjust Settings**: Use the system controls to modify configuration

### Keyboard Shortcuts

- `Ctrl/Cmd + R`: Refresh all data
- `Ctrl/Cmd + K`: Focus search (when implemented)
- `Escape`: Close sidebar

### Incident Management

1. **View Incidents**: All active incidents are displayed in the incidents panel
2. **Incident Details**: Click on any incident to view comprehensive details
3. **Take Action**: Use the action buttons to acknowledge, resolve, or escalate incidents
4. **Monitor Progress**: Track incident resolution through the timeline

### Agent Management

1. **Monitor Status**: Agent cards show real-time status and metrics
2. **View Details**: Click on agent cards to see detailed performance data
3. **Perform Actions**: Restart, update, or view logs for individual agents
4. **Track Performance**: Monitor throughput, accuracy, and latency metrics

## 🛠️ Configuration

### Dashboard Configuration

The dashboard can be configured through the `dashboard_server.py` file:

```python
DASHBOARD_CONFIG = {
    'port': 8081,           # Dashboard port
    'debug': True,          # Debug mode
    'host': '0.0.0.0'       # Host binding
}
```

### System Controls

The dashboard provides interactive controls for:

- **Anomaly Detection Threshold**: Adjust sensitivity (0-100%)
- **Auto-Resolution**: Enable/disable automatic incident resolution
- **Paging Level**: Set escalation thresholds (Critical, High, Medium, All)
- **Processing Rate**: Control log processing speed (Low, Medium, High, Maximum)

## 📊 Data Sources

### Mock Data

For demonstration purposes, the dashboard uses mock data that simulates:

- Real-time log processing metrics
- Agent performance data
- Incident generation and resolution
- System health indicators

### Real Integration

To integrate with the actual SRE Agent system:

1. **Replace mock endpoints** in `dashboard_server.py` with real API calls
2. **Connect to SRE Agent databases** for live data
3. **Integrate with Kafka** for real-time log streaming
4. **Connect to agent APIs** for live status updates

## 🔍 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   lsof -i :8081
   
   # Kill the process or change the port
   ./start_dashboard.sh stop
   ```

2. **Dependencies Not Installed**
   ```bash
   # Reinstall dependencies
   ./start_dashboard.sh install
   ```

3. **Dashboard Not Loading**
   ```bash
   # Check logs
   ./start_dashboard.sh logs
   
   # Check status
   ./start_dashboard.sh status
   ```

4. **API Endpoints Not Responding**
   ```bash
   # Test health endpoint
   curl http://localhost:8081/api/health
   
   # Check server logs
   tail -f dashboard.log
   ```

### Debug Mode

Enable debug mode for detailed logging:

```python
DASHBOARD_CONFIG = {
    'debug': True,
    # ... other config
}
```

## 🚀 Deployment

### Production Deployment

For production deployment:

1. **Set debug to False**:
   ```python
   DASHBOARD_CONFIG = {
       'debug': False,
       'host': '0.0.0.0',
       'port': 8080
   }
   ```

2. **Use a production WSGI server**:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8081 dashboard_server:app
   ```

3. **Set up reverse proxy** (nginx/apache) for SSL termination

4. **Configure environment variables** for sensitive data

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements-dashboard.txt .
RUN pip install -r requirements-dashboard.txt

COPY . .
EXPOSE 8081

CMD ["python", "dashboard_server.py"]
```

Build and run:

```bash
docker build -t sre-dashboard .
docker run -p 8081:8081 sre-dashboard
```

## 🔐 Security Considerations

- **Authentication**: Implement user authentication for production use
- **Authorization**: Add role-based access control
- **HTTPS**: Use SSL/TLS in production
- **Input Validation**: Validate all API inputs
- **Rate Limiting**: Implement API rate limiting
- **Audit Logging**: Log all dashboard actions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is part of the SRE Agent system and follows the same licensing terms.

## 🆘 Support

For support and questions:

1. Check the troubleshooting section
2. Review the logs: `./start_dashboard.sh logs`
3. Check system status: `./start_dashboard.sh status`
4. Open an issue in the repository

## 🔄 Integration with SRE Agent System

The dashboard is designed to integrate seamlessly with the SRE Agent system:

1. **Real-time Data**: Connect to the SRE Agent orchestrator for live metrics
2. **Incident Management**: Integrate with the incident tracking system
3. **Agent Control**: Connect to individual agent APIs for management
4. **Configuration**: Sync with the SRE Agent configuration system

For full integration, replace the mock data generation in `dashboard_server.py` with actual API calls to the SRE Agent system components. 