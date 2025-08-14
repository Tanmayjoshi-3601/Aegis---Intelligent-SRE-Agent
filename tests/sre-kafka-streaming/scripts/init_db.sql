-- SRE Agent Database Initialization Script
-- Creates tables for storing log data and metrics

-- Create logs table
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    service VARCHAR(100) NOT NULL,
    level VARCHAR(20) NOT NULL,
    host VARCHAR(100),
    message TEXT,
    cpu_usage DECIMAL(5,2),
    memory_usage DECIMAL(5,2),
    error_rate DECIMAL(8,6),
    request_latency_ms INTEGER,
    active_connections INTEGER,
    is_anomaly BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_logs_service ON system_logs(service);
CREATE INDEX IF NOT EXISTS idx_system_logs_anomaly ON system_logs(is_anomaly);

-- Create metrics table for aggregated data
CREATE TABLE IF NOT EXISTS service_metrics (
    id SERIAL PRIMARY KEY,
    service VARCHAR(100) NOT NULL,
    metric_date DATE NOT NULL,
    avg_cpu_usage DECIMAL(5,2),
    avg_memory_usage DECIMAL(5,2),
    avg_error_rate DECIMAL(8,6),
    avg_latency_ms INTEGER,
    total_logs INTEGER DEFAULT 0,
    anomaly_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(service, metric_date)
);

-- Create alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    service VARCHAR(100) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    metrics JSONB,
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for alerts
CREATE INDEX IF NOT EXISTS idx_alerts_service ON alerts(service);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON alerts(is_resolved);

-- Insert some sample data for testing
INSERT INTO system_logs (timestamp, service, level, host, message, cpu_usage, memory_usage, error_rate, is_anomaly)
VALUES 
    (NOW() - INTERVAL '1 hour', 'api-gateway', 'INFO', 'host-1', 'Normal operation', 45.2, 52.1, 0.002, FALSE),
    (NOW() - INTERVAL '30 minutes', 'database-primary', 'ERROR', 'host-2', 'High CPU usage detected', 92.5, 88.1, 0.08, TRUE),
    (NOW() - INTERVAL '15 minutes', 'cache-service', 'WARN', 'host-3', 'Memory usage high', 78.3, 89.2, 0.015, TRUE)
ON CONFLICT DO NOTHING;

-- Grant permissions to the sre_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sre_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sre_user; 