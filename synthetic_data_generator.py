#!/usr/bin/env python3
"""
SRE Agent MVP - Synthetic Data Generator
=========================================
Generates two datasets:
1. Training Dataset: 7,000 logs for ML model training
2. Streaming Dataset: 3,000 logs for real-time Kafka testing

Author: SRE Agent Team
Date: 2024
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os
from pathlib import Path

# Create directories if they don't exist
Path("data/synthetic/training").mkdir(parents=True, exist_ok=True)
Path("data/synthetic/streaming").mkdir(parents=True, exist_ok=True)
Path("data/playbooks").mkdir(parents=True, exist_ok=True)

# ============================================
# Configuration
# ============================================

# Services in our mock microservices architecture
SERVICES = [
    "api-gateway", "auth-service", "user-service", "payment-service",
    "inventory-service", "notification-service", "analytics-service",
    "cache-service", "database-primary", "database-replica"
]

# Log levels
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Error messages for different scenarios
ERROR_MESSAGES = {
    "timeout": [
        "Connection timeout after 30000ms",
        "Request timeout: upstream service not responding",
        "Gateway timeout: 504",
        "Read timeout on socket"
    ],
    "memory": [
        "OutOfMemoryError: Java heap space",
        "Memory limit exceeded: 2048MB",
        "Cannot allocate memory",
        "Memory pressure: high"
    ],
    "database": [
        "Connection pool exhausted",
        "Deadlock detected",
        "Too many connections",
        "Query timeout after 60s",
        "Connection refused to database"
    ],
    "rate_limit": [
        "Rate limit exceeded: 429",
        "Too many requests from IP",
        "API quota exceeded",
        "Throttling activated"
    ],
    "auth": [
        "Invalid authentication token",
        "Token expired",
        "Unauthorized access attempt",
        "Permission denied: insufficient privileges"
    ],
    "disk": [
        "Disk space critical: 95% used",
        "No space left on device",
        "Write failed: disk full",
        "Inode limit reached"
    ],
    "network": [
        "Network unreachable",
        "Connection reset by peer",
        "No route to host",
        "DNS resolution failed"
    ]
}

# ============================================
# Helper Functions
# ============================================

def generate_timestamp(base_time: datetime, offset_minutes: int) -> str:
    """Generate ISO format timestamp"""
    return (base_time + timedelta(minutes=offset_minutes)).isoformat()

def generate_request_id() -> str:
    """Generate unique request ID"""
    return f"req_{uuid.uuid4().hex[:12]}"

def generate_normal_metrics() -> Dict[str, Any]:
    """Generate normal system metrics"""
    return {
        "cpu_usage": random.uniform(20, 60),
        "memory_usage": random.uniform(30, 70),
        "disk_usage": random.uniform(40, 75),
        "network_in_mbps": random.uniform(10, 100),
        "network_out_mbps": random.uniform(10, 100),
        "active_connections": random.randint(50, 500),
        "request_latency_ms": random.randint(50, 200),
        "requests_per_second": random.randint(100, 1000),
        "error_rate": random.uniform(0, 0.01)  # 0-1% error rate is normal
    }

def generate_anomaly_metrics(anomaly_type: str) -> Dict[str, Any]:
    """Generate anomalous system metrics based on type"""
    metrics = generate_normal_metrics()
    
    if anomaly_type == "high_cpu":
        metrics["cpu_usage"] = random.uniform(85, 99)
        metrics["request_latency_ms"] = random.randint(500, 2000)
    elif anomaly_type == "high_memory":
        metrics["memory_usage"] = random.uniform(85, 99)
        metrics["error_rate"] = random.uniform(0.02, 0.05)
    elif anomaly_type == "high_latency":
        metrics["request_latency_ms"] = random.randint(1000, 5000)
        metrics["error_rate"] = random.uniform(0.05, 0.15)
    elif anomaly_type == "high_error_rate":
        metrics["error_rate"] = random.uniform(0.1, 0.3)
        metrics["requests_per_second"] = random.randint(10, 50)
    elif anomaly_type == "disk_issue":
        metrics["disk_usage"] = random.uniform(90, 99)
        metrics["request_latency_ms"] = random.randint(300, 1000)
    elif anomaly_type == "network_issue":
        metrics["network_in_mbps"] = random.uniform(0, 5)
        metrics["network_out_mbps"] = random.uniform(0, 5)
        metrics["active_connections"] = random.randint(5, 20)
    elif anomaly_type == "connection_pool":
        metrics["active_connections"] = random.randint(900, 1000)
        metrics["request_latency_ms"] = random.randint(2000, 10000)
    
    return metrics

def generate_log_entry(
    timestamp: str,
    service: str,
    level: str,
    is_anomaly: bool = False,
    anomaly_type: str = None,
    scenario_id: str = None
) -> Dict[str, Any]:
    """Generate a single log entry"""
    
    log_entry = {
        "timestamp": timestamp,
        "service": service,
        "level": level,
        "request_id": generate_request_id(),
        "host": f"{service}-{random.randint(1, 5)}.prod.internal",
        "environment": "production"
    }
    
    # Add metrics
    if is_anomaly and anomaly_type:
        log_entry["metrics"] = generate_anomaly_metrics(anomaly_type)
        log_entry["anomaly"] = True
        log_entry["anomaly_type"] = anomaly_type
        
        # Add appropriate error message
        if anomaly_type in ["high_latency", "network_issue"]:
            log_entry["message"] = random.choice(ERROR_MESSAGES["timeout"])
        elif anomaly_type == "high_memory":
            log_entry["message"] = random.choice(ERROR_MESSAGES["memory"])
        elif anomaly_type == "connection_pool":
            log_entry["message"] = random.choice(ERROR_MESSAGES["database"])
        elif anomaly_type == "high_error_rate":
            error_type = random.choice(["auth", "rate_limit"])
            log_entry["message"] = random.choice(ERROR_MESSAGES[error_type])
        elif anomaly_type == "disk_issue":
            log_entry["message"] = random.choice(ERROR_MESSAGES["disk"])
        else:
            log_entry["message"] = "Anomalous behavior detected"
            
        # Add stack trace for errors
        if level in ["ERROR", "CRITICAL"]:
            log_entry["stack_trace"] = generate_stack_trace(service, anomaly_type)
    else:
        log_entry["metrics"] = generate_normal_metrics()
        log_entry["anomaly"] = False
        log_entry["message"] = generate_normal_message(service, level)
    
    # Add scenario ID if part of a scenario
    if scenario_id:
        log_entry["scenario_id"] = scenario_id
    
    # Add additional context
    log_entry["user_id"] = f"user_{random.randint(1000, 9999)}" if random.random() > 0.3 else None
    log_entry["transaction_id"] = f"tx_{uuid.uuid4().hex[:8]}" if random.random() > 0.5 else None
    
    return log_entry

def generate_normal_message(service: str, level: str) -> str:
    """Generate normal log message"""
    messages = {
        "INFO": [
            f"Request processed successfully",
            f"Health check passed",
            f"Cache hit ratio: {random.uniform(70, 95):.2f}%",
            f"Service {service} responding normally",
            f"Database connection pool healthy"
        ],
        "DEBUG": [
            f"Entering method processRequest",
            f"Query executed in {random.randint(10, 100)}ms",
            f"Cache key generated: {uuid.uuid4().hex[:8]}",
            f"Request payload size: {random.randint(100, 5000)} bytes"
        ],
        "WARNING": [
            f"Deprecation warning: Method will be removed in v3.0",
            f"Slow query detected: {random.randint(500, 1000)}ms",
            f"Memory usage above 70%: monitoring",
            f"Retry attempt 1 of 3"
        ]
    }
    return random.choice(messages.get(level, ["Standard log message"]))

def generate_stack_trace(service: str, anomaly_type: str) -> List[str]:
    """Generate a realistic stack trace"""
    traces = {
        "high_memory": [
            f"at {service}.handlers.RequestHandler.processRequest(RequestHandler.java:142)",
            f"at {service}.cache.CacheManager.allocate(CacheManager.java:89)",
            "at java.lang.OutOfMemoryError.<init>(OutOfMemoryError.java:48)"
        ],
        "connection_pool": [
            f"at {service}.db.ConnectionPool.getConnection(ConnectionPool.java:234)",
            f"at {service}.dao.UserDAO.findById(UserDAO.java:67)",
            "at com.zaxxer.hikari.pool.HikariPool.getConnection(HikariPool.java:184)"
        ],
        "high_latency": [
            f"at {service}.client.HTTPClient.executeRequest(HTTPClient.java:445)",
            f"at {service}.service.ExternalService.call(ExternalService.java:123)",
            "at java.net.SocketTimeoutException.<init>(SocketTimeoutException.java:30)"
        ]
    }
    return traces.get(anomaly_type, [f"at {service}.UnknownError"])

# ============================================
# Scenario Generators
# ============================================

def generate_cascading_failure_scenario(base_time: datetime, start_offset: int) -> List[Dict]:
    """Generate logs for a cascading failure scenario"""
    logs = []
    scenario_id = f"cascade_{uuid.uuid4().hex[:8]}"
    
    # Phase 1: Initial database issues
    for i in range(5):
        logs.append(generate_log_entry(
            timestamp=generate_timestamp(base_time, start_offset + i),
            service="database-primary",
            level="ERROR",
            is_anomaly=True,
            anomaly_type="connection_pool",
            scenario_id=scenario_id
        ))
    
    # Phase 2: Services start experiencing timeouts
    affected_services = ["user-service", "payment-service", "inventory-service"]
    for i in range(5, 15):
        for service in affected_services:
            if random.random() > 0.3:
                logs.append(generate_log_entry(
                    timestamp=generate_timestamp(base_time, start_offset + i),
                    service=service,
                    level="ERROR" if random.random() > 0.5 else "WARNING",
                    is_anomaly=True,
                    anomaly_type="high_latency",
                    scenario_id=scenario_id
                ))
    
    # Phase 3: API Gateway starts failing
    for i in range(15, 20):
        logs.append(generate_log_entry(
            timestamp=generate_timestamp(base_time, start_offset + i),
            service="api-gateway",
            level="CRITICAL",
            is_anomaly=True,
            anomaly_type="high_error_rate",
            scenario_id=scenario_id
        ))
    
    return logs

def generate_memory_leak_scenario(base_time: datetime, start_offset: int) -> List[Dict]:
    """Generate logs for a gradual memory leak"""
    logs = []
    scenario_id = f"memleak_{uuid.uuid4().hex[:8]}"
    service = random.choice(SERVICES)
    
    # Gradual increase in memory usage over 30 minutes
    for i in range(30):
        # Memory increases gradually
        if i < 10:
            level = "INFO"
        elif i < 20:
            level = "WARNING"
        else:
            level = "ERROR"
        
        logs.append(generate_log_entry(
            timestamp=generate_timestamp(base_time, start_offset + i * 2),
            service=service,
            level=level,
            is_anomaly=(i > 10),
            anomaly_type="high_memory" if i > 10 else None,
            scenario_id=scenario_id
        ))
    
    # Final crash
    logs.append(generate_log_entry(
        timestamp=generate_timestamp(base_time, start_offset + 61),
        service=service,
        level="CRITICAL",
        is_anomaly=True,
        anomaly_type="high_memory",
        scenario_id=scenario_id
    ))
    
    return logs

def generate_ddos_scenario(base_time: datetime, start_offset: int) -> List[Dict]:
    """Generate logs for a DDoS attack scenario"""
    logs = []
    scenario_id = f"ddos_{uuid.uuid4().hex[:8]}"
    
    # Sudden spike in traffic
    for i in range(15):
        # Multiple services affected
        for service in ["api-gateway", "auth-service", "cache-service"]:
            for _ in range(random.randint(3, 8)):  # Multiple logs per minute
                logs.append(generate_log_entry(
                    timestamp=generate_timestamp(base_time, start_offset + i),
                    service=service,
                    level=random.choice(["WARNING", "ERROR", "CRITICAL"]),
                    is_anomaly=True,
                    anomaly_type="high_error_rate",
                    scenario_id=scenario_id
                ))
    
    return logs

# ============================================
# Main Dataset Generation
# ============================================

def generate_training_dataset() -> Dict[str, Any]:
    """Generate 7,000 logs for ML training"""
    print("Generating training dataset (7,000 logs)...")
    
    logs = []
    base_time = datetime.now() - timedelta(days=7)
    
    # Generate normal logs (70% = 4,900 logs)
    print("  - Generating 4,900 normal logs...")
    for i in range(4900):
        logs.append(generate_log_entry(
            timestamp=generate_timestamp(base_time, i * 2),
            service=random.choice(SERVICES),
            level=random.choices(
                ["DEBUG", "INFO", "WARNING"],
                weights=[0.2, 0.7, 0.1]
            )[0],
            is_anomaly=False
        ))
    
    # Generate known anomalies (20% = 1,400 logs)
    print("  - Generating 1,400 anomaly logs...")
    anomaly_types = ["high_cpu", "high_memory", "high_latency", 
                     "high_error_rate", "disk_issue", "network_issue", 
                     "connection_pool"]
    
    for i in range(1400):
        logs.append(generate_log_entry(
            timestamp=generate_timestamp(base_time, 5000 + i * 2),
            service=random.choice(SERVICES),
            level=random.choices(
                ["WARNING", "ERROR", "CRITICAL"],
                weights=[0.3, 0.5, 0.2]
            )[0],
            is_anomaly=True,
            anomaly_type=random.choice(anomaly_types)
        ))
    
    # Generate edge cases (10% = 700 logs)
    print("  - Generating 700 edge case logs...")
    offset = 7500
    
    # Add cascading failures
    for _ in range(5):
        cascade_logs = generate_cascading_failure_scenario(base_time, offset)
        logs.extend(cascade_logs)
        offset += 100
    
    # Add memory leak scenarios
    for _ in range(3):
        memleak_logs = generate_memory_leak_scenario(base_time, offset)
        logs.extend(memleak_logs)
        offset += 100
    
    # Add remaining as DDoS
    remaining = 700 - (len(logs) - 6300)
    if remaining > 0:
        ddos_logs = generate_ddos_scenario(base_time, offset)[:remaining]
        logs.extend(ddos_logs)
    
    # Shuffle to mix timestamps
    random.shuffle(logs)
    
    # Sort by timestamp for realistic ordering
    logs.sort(key=lambda x: x["timestamp"])
    
    # Generate metadata
    metadata = {
        "total_logs": len(logs),
        "normal_logs": sum(1 for log in logs if not log["anomaly"]),
        "anomaly_logs": sum(1 for log in logs if log["anomaly"]),
        "services": list(set(log["service"] for log in logs)),
        "anomaly_types": list(set(log.get("anomaly_type", "") for log in logs if log.get("anomaly_type"))),
        "time_range": {
            "start": logs[0]["timestamp"],
            "end": logs[-1]["timestamp"]
        },
        "log_levels": {
            level: sum(1 for log in logs if log["level"] == level)
            for level in LOG_LEVELS
        }
    }
    
    return {
        "logs": logs,
        "metadata": metadata
    }

def generate_streaming_dataset() -> Dict[str, Any]:
    """Generate 3,000 logs for streaming/testing"""
    print("Generating streaming dataset (3,000 logs)...")
    
    logs = []
    base_time = datetime.now()
    
    # Scenario-based logs (50% = 1,500 logs)
    print("  - Generating 1,500 scenario-based logs...")
    scenarios = []
    offset = 0
    
    # Generate 10 cascading failures
    for i in range(10):
        scenario_logs = generate_cascading_failure_scenario(base_time, offset)
        logs.extend(scenario_logs)
        scenarios.append({
            "type": "cascading_failure",
            "id": scenario_logs[0]["scenario_id"],
            "log_count": len(scenario_logs),
            "start_time": scenario_logs[0]["timestamp"],
            "end_time": scenario_logs[-1]["timestamp"]
        })
        offset += 30
    
    # Generate 5 memory leaks
    for i in range(5):
        scenario_logs = generate_memory_leak_scenario(base_time, offset)
        logs.extend(scenario_logs)
        scenarios.append({
            "type": "memory_leak",
            "id": scenario_logs[0]["scenario_id"],
            "log_count": len(scenario_logs),
            "start_time": scenario_logs[0]["timestamp"],
            "end_time": scenario_logs[-1]["timestamp"]
        })
        offset += 70
    
    # Generate 3 DDoS attacks
    for i in range(3):
        scenario_logs = generate_ddos_scenario(base_time, offset)
        logs.extend(scenario_logs)
        scenarios.append({
            "type": "ddos_attack",
            "id": scenario_logs[0]["scenario_id"],
            "log_count": len(scenario_logs),
            "start_time": scenario_logs[0]["timestamp"],
            "end_time": scenario_logs[-1]["timestamp"]
        })
        offset += 20
    
    # Mixed patterns (33% = 1,000 logs)
    print("  - Generating 1,000 mixed pattern logs...")
    for i in range(1000):
        is_anomaly = random.random() > 0.7  # 30% anomaly rate
        logs.append(generate_log_entry(
            timestamp=generate_timestamp(base_time, offset + i),
            service=random.choice(SERVICES),
            level=random.choice(LOG_LEVELS),
            is_anomaly=is_anomaly,
            anomaly_type=random.choice(["high_cpu", "high_memory", "high_latency"]) if is_anomaly else None
        ))
    
    # Normal baseline (17% = 500 logs)
    print("  - Generating 500 baseline logs...")
    for i in range(500):
        logs.append(generate_log_entry(
            timestamp=generate_timestamp(base_time, offset + 1000 + i),
            service=random.choice(SERVICES),
            level=random.choices(["DEBUG", "INFO", "WARNING"], weights=[0.2, 0.7, 0.1])[0],
            is_anomaly=False
        ))
    
    # Sort by timestamp
    logs.sort(key=lambda x: x["timestamp"])
    
    # Generate metadata
    metadata = {
        "total_logs": len(logs),
        "normal_logs": sum(1 for log in logs if not log["anomaly"]),
        "anomaly_logs": sum(1 for log in logs if log["anomaly"]),
        "scenarios": scenarios,
        "services": list(set(log["service"] for log in logs)),
        "anomaly_types": list(set(log.get("anomaly_type", "") for log in logs if log.get("anomaly_type"))),
        "time_range": {
            "start": logs[0]["timestamp"],
            "end": logs[-1]["timestamp"]
        },
        "streaming_info": {
            "recommended_rate": "10 logs/second",
            "total_duration_minutes": 5,
            "burst_scenarios": len([s for s in scenarios if s["type"] in ["ddos_attack", "cascading_failure"]])
        }
    }
    
    return {
        "logs": logs,
        "metadata": metadata
    }

def generate_mitigation_playbooks():
    """Generate RAG mitigation playbooks"""
    print("Generating mitigation playbooks...")
    
    playbooks = [
        {
            "id": "pb_001",
            "issue_type": "high_memory",
            "title": "High Memory Usage Mitigation",
            "symptoms": [
                "memory_usage > 85%",
                "OutOfMemoryError in logs",
                "Increasing memory trend over 30 minutes",
                "Garbage collection frequency increased"
            ],
            "root_causes": [
                "Memory leak in application",
                "Cache size unbounded",
                "Large result sets from database",
                "Thread leak creating objects"
            ],
            "mitigation_steps": [
                {
                    "priority": 1,
                    "action": "restart_service",
                    "description": "Restart the affected service to clear memory",
                    "risk": "low",
                    "expected_result": "Immediate memory reduction"
                },
                {
                    "priority": 2,
                    "action": "scale_horizontally",
                    "description": "Add more instances to distribute load",
                    "risk": "low",
                    "expected_result": "Load distribution reduces memory pressure"
                },
                {
                    "priority": 3,
                    "action": "clear_cache",
                    "description": "Clear application cache if applicable",
                    "risk": "medium",
                    "expected_result": "Temporary performance impact, memory recovery"
                }
            ],
            "verification": [
                "Check memory_usage < 70% after 5 minutes",
                "Verify no OutOfMemoryError in logs",
                "Confirm garbage collection normalized"
            ],
            "preventive_measures": [
                "Set JVM heap size limits",
                "Implement cache eviction policies",
                "Add memory monitoring alerts at 70% threshold"
            ]
        },
        {
            "id": "pb_002",
            "issue_type": "high_latency",
            "title": "High Latency Response Mitigation",
            "symptoms": [
                "request_latency_ms > 1000",
                "Timeout errors increasing",
                "Queue depth increasing",
                "User complaints about slow response"
            ],
            "root_causes": [
                "Database slow queries",
                "Network congestion",
                "Insufficient compute resources",
                "External service degradation"
            ],
            "mitigation_steps": [
                {
                    "priority": 1,
                    "action": "enable_circuit_breaker",
                    "description": "Activate circuit breaker for failing dependencies",
                    "risk": "medium",
                    "expected_result": "Fail fast, prevent cascade"
                },
                {
                    "priority": 2,
                    "action": "increase_connection_pool",
                    "description": "Increase database connection pool size",
                    "risk": "low",
                    "expected_result": "More concurrent connections available"
                },
                {
                    "priority": 3,
                    "action": "enable_cache",
                    "description": "Enable response caching for frequent queries",
                    "risk": "low",
                    "expected_result": "Reduced database load"
                }
            ],
            "verification": [
                "Check request_latency_ms < 500",
                "Verify error rate decreased",
                "Confirm queue depth normalizing"
            ]
        },
        {
            "id": "pb_003",
            "issue_type": "connection_pool_exhausted",
            "title": "Database Connection Pool Exhaustion",
            "symptoms": [
                "Connection pool exhausted errors",
                "active_connections > 900",
                "Database timeout errors",
                "Service unable to connect to database"
            ],
            "root_causes": [
                "Connection leak in application",
                "Sudden traffic spike",
                "Long-running queries holding connections",
                "Database performance degradation"
            ],
            "mitigation_steps": [
                {
                    "priority": 1,
                    "action": "kill_long_queries",
                    "description": "Terminate queries running > 60 seconds",
                    "risk": "medium",
                    "expected_result": "Free up held connections"
                },
                {
                    "priority": 2,
                    "action": "restart_connection_pool",
                    "description": "Force connection pool restart",
                    "risk": "high",
                    "expected_result": "All connections reset"
                },
                {
                    "priority": 3,
                    "action": "scale_database_read_replicas",
                    "description": "Add read replicas to distribute load",
                    "risk": "low",
                    "expected_result": "Read traffic distributed"
                }
            ],
            "verification": [
                "Check active_connections < 700",
                "No connection pool errors in last 5 minutes",
                "Database response time < 100ms"
            ]
        },
        {
            "id": "pb_004",
            "issue_type": "cascading_failure",
            "title": "Cascading Failure Mitigation",
            "symptoms": [
                "Multiple services reporting errors",
                "Error rate > 10% across services",
                "Dependency chain failures",
                "System-wide degradation"
            ],
            "root_causes": [
                "Core service failure",
                "Database unavailable",
                "Message queue backup",
                "Network partition"
            ],
            "mitigation_steps": [
                {
                    "priority": 1,
                    "action": "activate_degraded_mode",
                    "description": "Switch to degraded mode with limited features",
                    "risk": "low",
                    "expected_result": "Core functionality preserved"
                },
                {
                    "priority": 2,
                    "action": "isolate_failing_service",
                    "description": "Remove failing service from load balancer",
                    "risk": "medium",
                    "expected_result": "Prevent spread of failures"
                },
                {
                    "priority": 3,
                    "action": "increase_timeout_limits",
                    "description": "Temporarily increase timeout thresholds",
                    "risk": "low",
                    "expected_result": "Reduce timeout-induced failures"
                }
            ],
            "verification": [
                "Error rate < 2% across all services",
                "No new timeout errors",
                "All critical paths operational"
            ]
        },
        {
            "id": "pb_005",
            "issue_type": "high_cpu",
            "title": "High CPU Usage Mitigation",
            "symptoms": [
                "cpu_usage > 85%",
                "System load average high",
                "Response time degradation",
                "Thread pool saturation"
            ],
            "root_causes": [
                "Inefficient algorithm",
                "Infinite loop",
                "Excessive logging",
                "Crypto mining malware"
            ],
            "mitigation_steps": [
                {
                    "priority": 1,
                    "action": "scale_horizontally",
                    "description": "Add more instances immediately",
                    "risk": "low",
                    "expected_result": "Load distributed across instances"
                },
                {
                    "priority": 2,
                    "action": "throttle_requests",
                    "description": "Enable rate limiting",
                    "risk": "medium",
                    "expected_result": "Reduced incoming load"
                },
                {
                    "priority": 3,
                    "action": "profile_and_optimize",
                    "description": "Run CPU profiler and optimize hot paths",
                    "risk": "low",
                    "expected_result": "Long-term CPU reduction"
                }
            ],
            "verification": [
                "CPU usage < 70%",
                "Response times normalized",
                "No thread pool exhaustion"
            ]
        }
    ]
    
    return playbooks

# ============================================
# Main Execution
# ============================================

def main():
    """Generate all datasets and save to files"""
    
    print("="*60)
    print("SRE Agent MVP - Synthetic Data Generation")
    print("="*60)
    
    # Generate training dataset
    training_data = generate_training_dataset()
    
    # Save training data
    with open("data/synthetic/training/logs.json", "w") as f:
        json.dump(training_data["logs"], f, indent=2)
    
    with open("data/synthetic/training/metadata.json", "w") as f:
        json.dump(training_data["metadata"], f, indent=2)
    
    print(f"✅ Training dataset saved: {len(training_data['logs'])} logs")
    print(f"   - Normal: {training_data['metadata']['normal_logs']}")
    print(f"   - Anomalies: {training_data['metadata']['anomaly_logs']}")
    
    # Generate streaming dataset
    streaming_data = generate_streaming_dataset()
    
    # Save streaming data
    with open("data/synthetic/streaming/logs.json", "w") as f:
        json.dump(streaming_data["logs"], f, indent=2)
    
    with open("data/synthetic/streaming/metadata.json", "w") as f:
        json.dump(streaming_data["metadata"], f, indent=2)
    
    print(f"✅ Streaming dataset saved: {len(streaming_data['logs'])} logs")
    print(f"   - Scenarios: {len(streaming_data['metadata']['scenarios'])}")
    print(f"   - Normal: {streaming_data['metadata']['normal_logs']}")
    print(f"   - Anomalies: {streaming_data['metadata']['anomaly_logs']}")
    
    # Generate mitigation playbooks
    playbooks = generate_mitigation_playbooks()
    
    with open("data/playbooks/mitigations.json", "w") as f:
        json.dump(playbooks, f, indent=2)
    
    print(f"✅ Mitigation playbooks saved: {len(playbooks)} playbooks")
    
    # Generate sample configuration for testing
    sample_config = {
        "training_config": {
            "data_path": "data/synthetic/training/logs.json",
            "test_split": 0.2,
            "anomaly_threshold": 0.7,
            "models": ["isolation_forest", "lstm_autoencoder"]
        },
        "streaming_config": {
            "data_path": "data/synthetic/streaming/logs.json",
            "kafka_topic": "system-logs",
            "batch_size": 10,
            "interval_ms": 100
        },
        "services": SERVICES,
        "anomaly_types": list(set(
            log.get("anomaly_type", "") 
            for log in training_data["logs"] + streaming_data["logs"] 
            if log.get("anomaly_type")
        ))
    }
    
    with open("data/config.json", "w") as f:
        json.dump(sample_config, f, indent=2)
    
    print(f"✅ Configuration saved: data/config.json")
    
    print("\n" + "="*60)
    print("Data generation complete! Summary:")
    print("="*60)
    print(f"📁 Training Dataset:")
    print(f"   - Location: data/synthetic/training/")
    print(f"   - Total logs: {len(training_data['logs'])}")
    print(f"   - Anomaly rate: {(training_data['metadata']['anomaly_logs']/len(training_data['logs'])*100):.1f}%")
    
    print(f"\n📁 Streaming Dataset:")
    print(f"   - Location: data/synthetic/streaming/")
    print(f"   - Total logs: {len(streaming_data['logs'])}")
    print(f"   - Scenarios: {len(streaming_data['metadata']['scenarios'])}")
    print(f"   - Anomaly rate: {(streaming_data['metadata']['anomaly_logs']/len(streaming_data['logs'])*100):.1f}%")
    
    print(f"\n📁 Mitigation Playbooks:")
    print(f"   - Location: data/playbooks/")
    print(f"   - Total playbooks: {len(playbooks)}")
    
    print("\n" + "="*60)
    print("Next steps:")
    print("1. Use training/logs.json to train your ML models")
    print("2. Use streaming/logs.json for Kafka streaming tests")
    print("3. Use playbooks/mitigations.json for RAG system")
    print("="*60)

if __name__ == "__main__":
    main()