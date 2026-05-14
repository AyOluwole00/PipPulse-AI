# PipPulse AI - Operations & Monitoring Guide

## Daily Operations Checklist

### Morning Health Check (8:00 AM)
- [ ] Verify all services are running: `docker-compose ps`
- [ ] Check error rates: `curl http://localhost:8000/health/detailed`
- [ ] Review WebSocket connections: `curl http://localhost:8000/health/websocket/metrics`
- [ ] Verify database connectivity
- [ ] Check disk space and memory usage

### Before Deployment
- [ ] Run test suite: `pytest backend/tests/`
- [ ] Review logs for warnings: `docker-compose logs --tail=100`
- [ ] Verify database backups completed
- [ ] Check external API status (NewsAPI, Twitter, etc.)

### Post-Deployment
- [ ] Monitor error rates for 30 minutes
- [ ] Verify WebSocket connections are stable
- [ ] Test signal generation pipeline
- [ ] Confirm real-time data flows to frontend

## Monitoring Dashboard Setup

### Grafana Dashboard JSON
```json
{
  "dashboard": {
    "title": "PipPulse AI Operations",
    "panels": [
      {
        "title": "Active WebSocket Connections",
        "targets": [
          {
            "expr": "websocket_active_connections"
          }
        ]
      },
      {
        "title": "Average WebSocket Latency (ms)",
        "targets": [
          {
            "expr": "websocket_avg_latency_ms"
          }
        ]
      },
      {
        "title": "Backend Error Rate",
        "targets": [
          {
            "expr": "rate(backend_errors_total[5m])"
          }
        ]
      },
      {
        "title": "Signal Generation Rate",
        "targets": [
          {
            "expr": "rate(signals_generated_total[1m])"
          }
        ]
      },
      {
        "title": "Database Query Latency",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m]))"
          }
        ]
      }
    ]
  }
}
```

## Key Metrics to Monitor

### WebSocket Health
```bash
# Get current WebSocket metrics
curl -s http://localhost:8000/health/websocket/metrics | jq '.'

# Sample output:
{
  "timestamp": "2024-01-15T14:30:00.000Z",
  "websocket": {
    "total_connections": 42,
    "avg_latency_ms": 12.5,
    "total_messages_sent": 12847,
    "total_messages_received": 9234
  }
}

# Alert thresholds:
# - Latency > 50ms: Investigate network/server issues
# - Connections drop > 20%: Check for crashes
# - Error rate > 1%: Review application logs
```

### Database Performance
```bash
# MongoDB query count
docker-compose exec mongodb mongosh --eval "db.serverStatus().opcounters"

# PostgreSQL active connections
docker-compose exec postgres psql -U pippulse -c "SELECT count(*) FROM pg_stat_activity;"

# Redis memory usage
docker-compose exec redis redis-cli INFO memory
```

### Signal Generation
```bash
# Check signal queue depth
docker-compose exec redis redis-cli LLEN signal_queue

# Monitor signal engine logs
docker-compose logs -f signal-engine --tail=50

# Check InfluxDB signal bucket
docker-compose exec influxdb influx bucket list
```

## Common Issues & Solutions

### Issue: WebSocket Connections Dropping

**Symptoms:**
- Clients disconnect unexpectedly
- Real-time signals not reaching frontend
- Connection count fluctuates rapidly

**Diagnosis:**
```bash
# Check connection metrics
curl http://localhost:8000/health/websocket/connections

# Monitor logs
docker-compose logs -f backend | grep -i websocket

# Check for memory issues
docker stats pippulse-backend
```

**Solutions:**
1. Check network connectivity between services
2. Increase message timeouts in `websocket.py`
3. Review Redis connection pool size
4. Scale backend horizontally if CPU/memory maxed

### Issue: High Database Query Latency

**Symptoms:**
- Slow API responses
- Backend logs show `DatabaseConnectionTimeout`
- Frontend shows loading spinners frequently

**Diagnosis:**
```bash
# Check active connections
docker-compose exec postgres psql -U pippulse -c "SELECT count(*) FROM pg_stat_activity;"

# Monitor slow queries
docker-compose exec postgres psql -U pippulse -c "SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Check MongoDB performance
docker-compose exec mongodb mongosh --eval "db.serverStatus().wiredTiger.cache"
```

**Solutions:**
1. Add database indexes: `CREATE INDEX idx_signal_timestamp ON signals(created_at)`
2. Increase connection pool: `pool_size=30` in SQLAlchemy config
3. Optimize slow queries identified by monitoring
4. Enable query result caching in Redis

### Issue: Signal Generation Delays

**Symptoms:**
- Signals generated but arrive late (>5s)
- signal-engine service consuming high CPU
- FinBERT model inference slow

**Diagnosis:**
```bash
# Check signal queue depth
docker-compose exec redis redis-cli LLEN signal_queue

# Monitor signal engine
docker-compose logs -f signal-engine

# Check GPU/CPU utilization
docker stats pippulse-signal-engine

# Verify FinBERT model
docker-compose exec signal-engine python -c "
import torch; 
from transformers import AutoModelForSequenceClassification;
model = AutoModelForSequenceClassification.from_pretrained('ProsusAI/finbert');
print(f'Model loaded. GPU available: {torch.cuda.is_available()}')
"
```

**Solutions:**
1. Use GPU acceleration: Add `--gpus all` to signal-engine in docker-compose
2. Batch process signals: Increase `MAX_BATCH_SIZE`
3. Cache model inference results
4. Scale signal-engine replicas

### Issue: Memory Leaks in Backend

**Symptoms:**
- Memory usage grows steadily over time
- OOMKilled errors after 24-48 hours
- Performance degrades over time

**Diagnosis:**
```bash
# Monitor memory trend
watch -n 10 'docker stats pippulse-backend --no-stream | tail -1'

# Generate memory profile
docker-compose exec backend python -m memory_profiler app/main.py

# Check for dangling database connections
docker-compose exec backend python -c "
from sqlalchemy import event
@event.listens_for(engine, 'connect')
def receive_connect(dbapi_conn, connection_record):
    print(f'Connection opened: {dbapi_conn}')
"
```

**Solutions:**
1. Ensure connections are properly closed
2. Clear caches periodically: `redis-cli FLUSHALL`
3. Monitor Redis memory: `redis-cli INFO memory`
4. Review WebSocket connection cleanup in disconnect handler

## Performance Optimization

### 1. WebSocket Message Batching
```python
# Instead of sending individual signals, batch them
async def batch_signal_broadcast():
    batch = []
    while True:
        try:
            signal = await redis.lpop('signal_queue')
            batch.append(signal)
            
            # Send batch when size threshold reached or timeout
            if len(batch) >= 10:
                await broadcast_signals(batch)
                batch = []
        except asyncio.TimeoutError:
            if batch:
                await broadcast_signals(batch)
                batch = []
```

### 2. Database Query Optimization
```sql
-- Add useful indexes
CREATE INDEX idx_signals_created_at ON signals(created_at DESC);
CREATE INDEX idx_signals_pair_created ON signals(currency_pair, created_at DESC);
CREATE INDEX idx_news_published_at ON news(published_at DESC);
CREATE INDEX idx_news_sentiment ON news(sentiment_score);
```

### 3. Caching Strategy
```python
# Cache expensive computations in Redis
@cache(ttl=300)  # 5 minute cache
async def get_signal_statistics():
    # Expensive calculation
    stats = await calculate_stats()
    return stats

# Cache frontend data
@router.get("/api/dashboard-data")
@cache(ttl=60)  # 1 minute cache
async def get_dashboard_data():
    return await fetch_dashboard_data()
```

### 4. Async Task Processing
```python
# Use background tasks for non-critical operations
from celery import shared_task

@shared_task
def process_historical_analysis(signal_id):
    # Long-running analysis
    perform_analysis(signal_id)

# Call from endpoint
@router.post("/signals/{signal_id}/analyze")
async def analyze_signal(signal_id: str):
    process_historical_analysis.delay(signal_id)
    return {"status": "processing"}
```

## Incident Response

### Alert: High Error Rate (>5%)

**Step 1: Assess Severity**
- Check which errors: `docker-compose logs backend | grep ERROR | tail -20`
- Determine if affecting all users or specific features
- Is frontend operational or completely down?

**Step 2: Investigate Root Cause**
```bash
# Get error distribution
docker-compose logs backend | grep ERROR | awk '{print $(NF-1)}' | sort | uniq -c

# Check database connectivity
docker-compose exec backend python -c "from app.database import get_mongodb; print(get_mongodb().command('ping'))"

# Check external API status
curl -s https://newsapi.org/v2/everything?q=forex | jq '.status'
```

**Step 3: Mitigate**
- Disable problematic features
- Scale up backend replicas
- Clear caches: `docker-compose exec redis redis-cli FLUSHALL`
- Restart affected services

**Step 4: Resolution & Postmortem**
- Apply permanent fix
- Deploy and monitor
- Document incident and prevention

### Alert: WebSocket Connections Critical (>95% capacity)

**Immediate Actions:**
```bash
# Scale backend to 5 replicas
kubectl scale deployment pippulse-backend --replicas=5

# Monitor new connection establishment
watch 'curl -s http://localhost:8000/health/websocket/connections | jq'

# Notify users if necessary
# POST /notifications/broadcast
```

## Maintenance Windows

### Weekly Maintenance (Sunday 2:00 AM - 3:00 AM)
1. Run database maintenance: `ANALYZE` on PostgreSQL, `db.repairDatabase()` on MongoDB
2. Rotate logs: `docker-compose logs --tail=0` after archiving
3. Update Docker images: `docker-compose pull`
4. Run security updates: `docker pull ubuntu:latest && docker build...`

### Monthly Maintenance (First Sunday 3:00 AM - 5:00 AM)
1. Full system backup
2. Test backup restoration
3. Update dependencies
4. Performance analysis and optimization
5. Capacity planning review

### Quarterly Maintenance (January, April, July, October)
1. Major version upgrades
2. Architecture review
3. Security audit
4. Disaster recovery drill

## Key Contacts & Escalation

| Issue | Primary | Secondary | Escalation |
|-------|---------|-----------|-----------|
| WebSocket Issues | DevOps | Backend Lead | VP Engineering |
| Database Issues | DBA | DevOps | CTO |
| Performance Issues | Backend Lead | DevOps | VP Engineering |
| API Integration | API Lead | Backend Lead | Product Manager |
| Security Issues | Security Team | DevOps | CTO |

## Documentation & Knowledge Base

- **Runbooks**: Store in `/docs/runbooks/`
- **Change Log**: Update `CHANGELOG.md` on each deployment
- **Known Issues**: Maintain `KNOWN_ISSUES.md`
- **Architecture Diagrams**: Keep in `/docs/architecture/`
- **Performance Baselines**: Track in `performance.csv`

## Useful Commands Reference

```bash
# Service Management
docker-compose restart backend
docker-compose pause backend  # Pause without stopping
docker-compose unpause backend

# Logs
docker-compose logs -f backend --tail=100
docker-compose logs --since 2024-01-15T10:00:00 backend

# Database Operations
docker-compose exec mongodb mongosh
docker-compose exec postgres psql -U pippulse
docker-compose exec redis redis-cli

# System Diagnostics
docker-compose stats
docker system df
docker network inspect pippulse-network

# Cleanup
docker-compose exec redis redis-cli FLUSHALL
docker-compose system prune -a
```

## Emergency Contacts

- **On-Call DevOps**: Pagerduty rotation
- **Backend Engineer**: Slack #backend-oncall
- **Security Team**: security@pippulse.ai
- **Vendor Support**: See `/docs/vendor-contacts.md`
