# Performance Optimization Guide

This guide covers performance optimization strategies for Ouroboros v2, including hardware configuration, attack optimization, and system tuning.

---

## Table of Contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=3 --minlevel=1 -->

- [Performance Optimization Guide](#performance-optimization-guide)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Hardware Optimization](#hardware-optimization)
    - [1. GPU Configuration](#1-gpu-configuration)
    - [2. System Configuration](#2-system-configuration)
  - [Attack Optimization](#attack-optimization)
    - [1. Attack Strategy](#1-attack-strategy)
    - [2. Resource Selection](#2-resource-selection)
    - [3. Campaign Configuration](#3-campaign-configuration)
  - [Agent Performance Tuning](#agent-performance-tuning)
    - [1. Workload Configuration](#1-workload-configuration)
    - [2. Performance Monitoring](#2-performance-monitoring)
    - [3. Troubleshooting Performance Issues](#3-troubleshooting-performance-issues)
  - [Resource Optimization](#resource-optimization)
    - [1. Caching Strategy](#1-caching-strategy)
    - [2. Resource Distribution](#2-resource-distribution)
  - [System-Level Optimization](#system-level-optimization)
    - [1. Database Performance](#1-database-performance)
    - [2. Application Performance](#2-application-performance)
    - [3. Network Optimization](#3-network-optimization)
  - [Monitoring and Analytics](#monitoring-and-analytics)
    - [1. Performance Metrics](#1-performance-metrics)
    - [2. Capacity Planning](#2-capacity-planning)
  - [Best Practices Summary](#best-practices-summary)
    - [1. Hardware Best Practices](#1-hardware-best-practices)
    - [2. Attack Best Practices](#2-attack-best-practices)
    - [3. Resource Best Practices](#3-resource-best-practices)
    - [4. System Best Practices](#4-system-best-practices)

<!-- mdformat-toc end -->

---

## Overview

Ouroboros v2 introduces several performance enhancements:

- **Complexity Scoring**: Intelligent attack prioritization
- **Keyspace Estimation**: Real-time performance predictions
- **Enhanced Monitoring**: Detailed performance metrics and analytics
- **Resource Optimization**: Improved caching and distribution
- **Agent Management**: Advanced hardware configuration and tuning

## Hardware Optimization

### 1. GPU Configuration

#### GPU Selection

Choose GPUs based on your workload:

Recommended GPUs:

- High-End:

  - NVIDIA RTX 4090: 24GB VRAM, excellent for large keyspaces
  - NVIDIA RTX 4080: 16GB VRAM, good balance of performance/cost
  - NVIDIA A100: 40/80GB VRAM, enterprise-grade performance

- Mid-Range:

  - NVIDIA RTX 3080: 10GB VRAM, solid performance for most tasks
  - NVIDIA RTX 3070: 8GB VRAM, good for smaller keyspaces

- Budget:

  - NVIDIA GTX 1660 Ti: 6GB VRAM, entry-level cracking

#### GPU Memory Optimization

Configure GPU memory usage:

```yaml
# Agent configuration
performance:
  gpu_memory_limit: 95    # Use 95% of available GPU memory
  max_tasks: 2            # Reduce concurrent tasks for memory-intensive attacks
hashcat:
  workload: 4             # Maximum GPU utilization
  optimize: true          # Enable hashcat optimizations
```

#### Temperature Management

Maintain optimal temperatures:

```yaml
# Temperature settings
hashcat:
  temp_abort: 90          # Abort at 90°C
  gpu_temp_retain: 80     # Target temperature
# Monitoring
monitoring:
  interval: 30            # Check every 30 seconds
  thermal_throttling_alert: true
```

### 2. System Configuration

#### Memory Optimization

```bash
# System memory recommendations
Minimum: 16GB RAM
Recommended: 32GB+ RAM for large campaigns
Optimal: 64GB+ RAM for enterprise deployments

# Memory settings
echo 'vm.swappiness=10' >> /etc/sysctl.conf
echo 'vm.dirty_ratio=5' >> /etc/sysctl.conf
```

#### Storage Optimization

```bash
# Use SSD for cache and temporary files
cache_dir: /ssd/cache/ouroboros
temp_dir: /ssd/tmp/ouroboros

# Storage recommendations
Cache: 100GB+ SSD for resource caching
Temp: 50GB+ SSD for temporary files
Database: SSD for optimal query performance
```

#### Network Configuration

```yaml
# Network optimization
resources:
  download_timeout: 300
  retry_attempts: 3
  parallel_downloads: 4
  bandwidth_limit: 100MB    # Optional bandwidth limiting
```

## Attack Optimization

### 1. Attack Strategy

#### Complexity-Based Prioritization

Ouroboros v2 uses complexity scoring to optimize attack order:

```yaml
Attack Complexity Levels:
  1: Very Low    - Simple dictionary attacks
  2: Low         - Dictionary with basic rules
  3: Medium      - Mask attacks, hybrid attacks
  4: High        - Complex masks, extensive rules
  5: Very High   - Brute force, large keyspaces

Strategy:
  - Start with complexity 1-2 attacks
  - Progress to higher complexity based on results
  - Use previous passwords for targeted attacks
```

#### Keyspace Estimation

Use real-time keyspace estimation for planning:

```text
Example keyspace estimates:
Dictionary Attack: 14M words × 64 rules = 896M combinations
Mask Attack: ?u?l?l?l?l?d?d = 26 × 26^4 × 10^2 = 45.7M combinations
Brute Force: ?a^8 = 95^8 = 6.6 × 10^15 combinations

Time estimates based on agent performance:
RTX 4090: ~50 GH/s for NTLM
Estimated time: 6.6 × 10^15 ÷ 50 × 10^9 = 132,000 seconds = 36.7 hours
```

### 2. Resource Selection

#### Wordlist Optimization

Choose appropriate wordlists:

```yaml
Targeted Wordlists:
  - Previous passwords (highest priority)
  - Industry-specific wordlists
  - Geographic/cultural wordlists
  - Common passwords (rockyou.txt)

Size Considerations:
  - Small wordlists (< 1M): Fast iteration, good for testing
  - Medium wordlists (1-10M): Balanced performance
  - Large wordlists (> 10M): Comprehensive but slower
```

#### Rule Selection

Optimize rule usage:

```yaml
Rule Strategies:
  Basic Rules:
    - best64.rule: 64 high-quality rules
    - OneRuleToRuleThemAll.rule: 52,000 rules (use carefully)

  Custom Rules:
    - Target-specific transformations
    - Year/date appending rules
    - Common substitutions (@ for a, 3 for e)

Performance Impact:
  - More rules = longer processing time
  - Quality over quantity approach recommended
```

#### Mask Optimization

Design efficient masks:

```yaml
Efficient Mask Patterns:
  Common Formats:
    - ?u?l?l?l?l?d?d: Capitalized word + 2 digits
    - ?l?l?l?l?d?d?d?d: Word + 4 digits
    - ?u?l?l?l?l?s: Word + special character

  Optimization Tips:
    - Use specific character classes when possible
    - Avoid overly broad masks (?a^12)
    - Consider known password policies
```

### 3. Campaign Configuration

#### Attack Ordering

Optimize attack sequence:
Recommended Order:

1. Previous passwords (if available)
2. Small targeted wordlists
3. Dictionary + basic rules
4. Mask attacks (known patterns)
5. Dictionary + extensive rules
6. Hybrid attacks
7. Brute force (last resort)

#### Parallel Execution

Configure concurrent attacks:

```yaml
# Campaign settings
max_concurrent_attacks: 3  # Run multiple attacks simultaneously
attack_priority: complexity_score  # Prioritize by complexity

# Agent distribution
agent_allocation: balanced  # Distribute agents across attacks
min_agents_per_attack: 1   # Minimum agents per attack
```

## Agent Performance Tuning

### 1. Workload Configuration

#### Workload Levels

Configure appropriate workload:

```text
Workload Settings (1-4):
  1: Low      - 25% GPU utilization, stable but slow
  2: Medium   - 50% GPU utilization, balanced
  3: High     - 75% GPU utilization, good performance
  4: Maximum  - 100% GPU utilization, maximum speed

Recommendations:
  - Start with workload 3
  - Increase to 4 if temperatures are stable
  - Reduce if experiencing thermal throttling
```

#### Device Selection

Optimize device usage:

```yaml
# Enable specific devices
backend_devices: 1,2    # Use GPUs 1 and 2
backend_ignore:
  cuda: false           # Enable CUDA
  opencl: true          # Disable OpenCL (avoid conflicts)
  hip: true             # Disable HIP
  metal: true           # Disable Metal
```

### 2. Performance Monitoring

#### Real-time Metrics

Monitor key performance indicators:

```text
Key Metrics:
  - Hash rate (H/s, KH/s, MH/s, GH/s)
  - GPU utilization (target: 90%+)
  - GPU temperature (keep under 80°C)
  - Memory usage (GPU and system)
  - Task completion rate

Monitoring Tools:
  - Ouroboros dashboard
  - Agent performance charts
  - System monitoring (nvidia-smi, htop)
```

#### Performance Baselines

Establish performance baselines:

```bash
# Benchmark agent performance
ouroboros-agent benchmark
```

```text
# Expected performance ranges (NTLM)
RTX 4090: 45-55 GH/s
RTX 4080: 35-45 GH/s
RTX 3080: 25-35 GH/s
RTX 3070: 20-30 GH/s

# Monitor for performance degradation
# Investigate if performance drops below 80% of baseline
```

### 3. Troubleshooting Performance Issues

#### Common Performance Problems

##### Low Hash Rates

- Causes:

  - Thermal throttling
  - Insufficient power supply
  - Driver issues
  - Memory limitations

- Solutions:

  - Improve cooling
  - Upgrade power supply
  - Update GPU drivers
  - Reduce concurrent tasks

##### High Temperatures

- Causes:

  - Poor ventilation
  - Dust accumulation
  - High ambient temperature
  - Overclocking

- Solutions:

  - Improve case airflow
  - Clean GPU fans and heatsinks
  - Reduce workload setting
  - Lower temperature limits

##### Memory Issues

- Causes:

  - Large keyspaces
  - Multiple concurrent attacks
  - Insufficient GPU memory

- Solutions:

  - Reduce attack complexity
  - Limit concurrent tasks
  - Use agents with more memory

## Resource Optimization

### 1. Caching Strategy

#### Agent-Side Caching

Optimize resource caching:

```yaml
# Cache configuration
resources:
  cache_dir: /ssd/cache/ouroboros
  max_cache: 100GB
  cleanup_interval: 3600    # Clean every hour
    # Cache policies
  wordlist_cache_ttl: 86400      # 24 hours
  rule_cache_ttl: 604800         # 7 days
  mask_cache_ttl: 604800         # 7 days
```

#### Server-Side Optimization

```yaml
# MinIO optimization
minio:
  cache_drives: [/ssd1, /ssd2]
  cache_quota: 80    # Use 80% of cache drives
# CDN integration (optional)
cdn:
  enabled: true
  provider: cloudflare
  cache_ttl: 3600
```

### 2. Resource Distribution

#### Load Balancing

Distribute resources efficiently:

```yaml
# Resource distribution strategy
distribution:
  method: geographic      # or "round_robin", "least_loaded"
  replication_factor: 2    # Replicate popular resources
# Bandwidth management
bandwidth:
  per_agent_limit: 100MB/s
  total_limit: 1GB/s
  priority_queue: true    # Prioritize active campaigns
```

#### Prefetching

Implement intelligent prefetching:

```yaml
# Prefetch strategy
prefetch:
  enabled: true
  popular_resources: true      # Cache frequently used resources
  campaign_resources: true     # Prefetch campaign resources
  prediction_window: 3600      # Look ahead 1 hour
```

## System-Level Optimization

### 1. Database Performance

#### Query Optimization

```sql
-- Index optimization for common queries
CREATE INDEX idx_tasks_agent_status ON tasks(agent_id, status);
CREATE INDEX idx_campaigns_project_status ON campaigns(project_id, status);
CREATE INDEX idx_hash_items_list_status ON hash_items(hash_list_id, is_cracked);

-- Partition large tables
PARTITION TABLE hash_items BY RANGE (hash_list_id);
PARTITION TABLE tasks BY RANGE (created_at);
```

#### Connection Pooling

```yaml
# Database configuration
database:
  pool_size: 20
  max_overflow: 30
  pool_timeout: 30
  pool_recycle: 3600
```

### 2. Application Performance

#### Caching Configuration

```yaml
# Application caching
cache:
  backend: redis      # or "memory" for development
  ttl: 300           # 5 minutes default
    # Specific cache settings
  dashboard_cache_ttl: 60        # Dashboard data
  agent_status_cache_ttl: 30     # Agent status
  resource_metadata_ttl: 3600    # Resource metadata
```

#### Background Tasks

```yaml
# Celery configuration
celery:
  worker_concurrency: 4
  task_routes:
    app.tasks.keyspace_estimation: {queue: estimation}
    app.tasks.resource_processing: {queue: resources}
    app.tasks.cleanup: {queue: maintenance}
```

### 3. Network Optimization

#### Load Balancing

```nginx
# Nginx configuration
upstream cipherswarm_backend {
    server app1:8000 weight=3;
    server app2:8000 weight=2;
    server app3:8000 weight=1;
}

# Connection limits
limit_conn_zone $binary_remote_addr zone=agents:10m;
limit_conn agents 10;
```

#### SSL/TLS Optimization

```nginx
# SSL optimization
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
ssl_prefer_server_ciphers off;
```

## Monitoring and Analytics

### 1. Performance Metrics

#### Key Performance Indicators

System KPIs:

- Total hash rate across all agents
- Agent utilization percentage
- Campaign completion rate
- Resource cache hit ratio
- API response times

Campaign KPIs:

- Hashes cracked per hour
- Time to first crack
- Attack efficiency ratio
- Resource utilization
- Agent participation rate

#### Alerting

```yaml
# Performance alerts
alerts:
  low_hash_rate:
    threshold: 80%  # Alert if below 80% of baseline
    duration: 300   # For 5 minutes
  high_temperature:
    threshold: 85   # Alert at 85°C
    duration: 60    # For 1 minute
  agent_offline:
    threshold: 1    # Alert immediately
    duration: 0
```

### 2. Capacity Planning

#### Resource Forecasting

```yaml
# Capacity planning metrics
planning:
  agent_growth_rate: 20%      # Expected monthly growth
  storage_growth_rate: 15%    # Storage needs growth
  bandwidth_growth_rate: 25%  # Bandwidth requirements
# Scaling thresholds
scaling:
  cpu_threshold: 80%          # Scale at 80% CPU
  memory_threshold: 85%       # Scale at 85% memory
  storage_threshold: 90%      # Scale at 90% storage
```

## Best Practices Summary

### 1. Hardware Best Practices

- **GPU Selection**: Prioritize VRAM capacity for large keyspaces
- **Cooling**: Maintain temperatures below 80°C for optimal performance
- **Power**: Ensure adequate power supply for maximum GPU utilization
- **Memory**: Use 32GB+ system RAM for large-scale deployments

### 2. Attack Best Practices

- **Start Simple**: Begin with low-complexity attacks
- **Use Intelligence**: Leverage previous passwords and targeted wordlists
- **Monitor Progress**: Use real-time metrics to adjust strategy
- **Optimize Order**: Sequence attacks by complexity and likelihood

### 3. Resource Best Practices

- **Cache Strategically**: Cache frequently used resources locally
- **Size Appropriately**: Balance resource size with performance needs
- **Validate Quality**: Ensure resource quality over quantity
- **Monitor Usage**: Track resource effectiveness and usage patterns

### 4. System Best Practices

- **Monitor Continuously**: Use comprehensive monitoring and alerting
- **Scale Proactively**: Plan for growth and scale before bottlenecks
- **Optimize Regularly**: Regular performance tuning and optimization
- **Document Changes**: Track configuration changes and their impact

For additional optimization guidance:

- [Agent Setup Guide](agent-setup.md) - Agent configuration and tuning
- [Attack Configuration Guide](attack-configuration.md) - Attack optimization strategies
- [Resource Management Guide](resource-management.md) - Resource optimization
- [Troubleshooting Guide](troubleshooting.md) - Performance troubleshooting
