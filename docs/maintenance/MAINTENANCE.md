# VDock Maintenance Guide

This guide covers routine maintenance tasks, monitoring, and troubleshooting for VDock production deployments.

## Routine Maintenance

### Daily Tasks

- [ ] Check service health endpoints
- [ ] Review error logs
- [ ] Monitor resource usage
- [ ] Verify backups are running

### Weekly Tasks

- [ ] Review security logs
- [ ] Check for dependency updates
- [ ] Monitor disk space usage
- [ ] Test backup restoration

### Monthly Tasks

- [ ] Update dependencies
- [ ] Security audit
- [ ] Performance review
- [ ] Documentation updates

## Monitoring

### Health Checks

```bash
# Backend health
curl -f http://localhost:5000/api/health

# Frontend health
curl -f http://localhost:3000

# Docker services
docker-compose ps
```

### Log Monitoring

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f vdock-backend
docker-compose logs -f vdock-frontend

# Filter logs by level
docker-compose logs -f vdock-backend | grep ERROR
```

### Resource Monitoring

```bash
# Docker resource usage
docker stats

# System resource usage
htop
df -h
free -h
```

## Backup and Recovery

### Backup Strategy

1. **Profile Data**: Daily automated backups
2. **Configuration**: Weekly backups
3. **SSL Certificates**: Monthly backups
4. **Full System**: Monthly full backups

### Backup Commands

```bash
# Create data backup
tar -czf vdock-data-$(date +%Y%m%d).tar.gz backend/data/

# Create configuration backup
tar -czf vdock-config-$(date +%Y%m%d).tar.gz .env *.pem

# Create full backup
tar -czf vdock-full-$(date +%Y%m%d).tar.gz \
  backend/data/ \
  .env \
  *.pem \
  docker-compose.yml
```

### Recovery Procedures

```bash
# Restore data backup
tar -xzf vdock-data-YYYYMMDD.tar.gz

# Restore configuration
tar -xzf vdock-config-YYYYMMDD.tar.gz

# Restore full backup
tar -xzf vdock-full-YYYYMMDD.tar.gz
```

## Updates and Upgrades

### Dependency Updates

```bash
# Update Docker images
docker-compose pull

# Rebuild with latest dependencies
docker-compose build --no-cache

# Restart services
docker-compose up -d
```

### Application Updates

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

### Database Migrations

```bash
# Backup before migration
./backup.sh

# Run migrations
docker-compose exec vdock-backend python migrate.py

# Verify migration
docker-compose exec vdock-backend python verify.py
```

## Performance Optimization

### Backend Optimization

1. **Database Tuning**
   - Optimize queries
   - Add indexes
   - Configure connection pooling

2. **Caching**
   - Enable Redis caching
   - Configure cache headers
   - Implement query caching

3. **Resource Allocation**
   - Increase memory limits
   - Optimize CPU usage
   - Configure swap space

### Frontend Optimization

1. **Asset Optimization**
   - Enable gzip compression
   - Optimize images
   - Minify CSS/JS

2. **Caching Strategy**
   - Set cache headers
   - Use CDN for static assets
   - Implement service workers

3. **Bundle Optimization**
   - Code splitting
   - Tree shaking
   - Lazy loading

## Troubleshooting

### Common Issues

#### Service Won't Start

```bash
# Check logs
docker-compose logs vdock-backend

# Check configuration
docker-compose config

# Check ports
netstat -tulpn | grep :5000
```

#### High Memory Usage

```bash
# Check memory usage
docker stats

# Check for memory leaks
docker-compose exec vdock-backend python -c "import gc; gc.collect()"

# Restart services
docker-compose restart
```

#### Database Issues

```bash
# Check database logs
docker-compose logs vdock-backend | grep -i database

# Test database connection
docker-compose exec vdock-backend python -c "from models import Profile; print('DB OK')"

# Repair database
docker-compose exec vdock-backend python repair_db.py
```

#### Network Issues

```bash
# Check network connectivity
ping localhost
curl -I http://localhost:5000

# Check firewall
iptables -L
ufw status

# Check DNS
nslookup localhost
```

### Performance Issues

#### Slow Response Times

1. **Check Resource Usage**
   ```bash
   docker stats
   htop
   ```

2. **Review Logs**
   ```bash
   docker-compose logs -f | grep -i slow
   ```

3. **Database Optimization**
   ```bash
   docker-compose exec vdock-backend python optimize_db.py
   ```

#### High CPU Usage

1. **Identify Processes**
   ```bash
   top
   docker stats
   ```

2. **Check for Loops**
   ```bash
   docker-compose logs -f | grep -i loop
   ```

3. **Optimize Code**
   - Review algorithms
   - Add caching
   - Optimize queries

## Security Maintenance

### Security Updates

```bash
# Update system packages
apt update && apt upgrade

# Update Docker images
docker-compose pull

# Scan for vulnerabilities
docker scan vdock-backend
docker scan vdock-frontend
```

### Security Monitoring

```bash
# Check security logs
docker-compose logs -f | grep -i security

# Monitor failed login attempts
docker-compose logs -f | grep -i "failed login"

# Check for suspicious activity
docker-compose logs -f | grep -i "unauthorized"
```

### Access Control Review

```bash
# Review user access
docker-compose exec vdock-backend python list_users.py

# Check file permissions
ls -la backend/data/

# Review configuration
cat .env | grep -E "(AUTH|SECRET)"
```

## Disaster Recovery

### Recovery Procedures

1. **Service Failure**
   ```bash
   # Restart services
   docker-compose restart
   
   # Check health
   curl -f http://localhost:5000/api/health
   ```

2. **Data Loss**
   ```bash
   # Restore from backup
   tar -xzf vdock-data-YYYYMMDD.tar.gz
   
   # Restart services
   docker-compose restart
   ```

3. **Complete System Failure**
   ```bash
   # Restore full backup
   tar -xzf vdock-full-YYYYMMDD.tar.gz
   
   # Rebuild and start
   docker-compose build
   docker-compose up -d
   ```

### Recovery Testing

```bash
# Test backup restoration
./test_backup.sh

# Test failover procedures
./test_failover.sh

# Test disaster recovery
./test_disaster_recovery.sh
```

## Maintenance Scripts

### Automated Backups

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d)
BACKUP_DIR="/backups"

# Create backup
tar -czf $BACKUP_DIR/vdock-$DATE.tar.gz \
  backend/data/ \
  .env \
  *.pem

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "vdock-*.tar.gz" -mtime +30 -delete

echo "Backup completed: vdock-$DATE.tar.gz"
```

### Health Check Script

```bash
#!/bin/bash
# health_check.sh

# Check backend
if ! curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "Backend health check failed"
    exit 1
fi

# Check frontend
if ! curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "Frontend health check failed"
    exit 1
fi

echo "All services healthy"
```

### Update Script

```bash
#!/bin/bash
# update.sh

# Backup before update
./backup.sh

# Pull latest changes
git pull origin main

# Update Docker images
docker-compose pull

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d

# Wait for services to be healthy
sleep 30

# Verify health
./health_check.sh

echo "Update completed successfully"
```

## Documentation Updates

### Keeping Documentation Current

- [ ] Update version numbers
- [ ] Review configuration examples
- [ ] Update troubleshooting steps
- [ ] Add new features documentation

### Documentation Review Schedule

- **Weekly**: Review error logs and update troubleshooting
- **Monthly**: Review configuration examples
- **Quarterly**: Complete documentation audit
- **Annually**: Major documentation overhaul

## Support and Resources

### Internal Resources

- [Production Deployment Guide](PRODUCTION_DEPLOYMENT.md)
- [Security Policy](../security/SECURITY.md)
- [API Documentation](docs/API.md)
- [Developer Guide](docs/DEVELOPER_GUIDE.md)

### External Resources

- [Docker Documentation](https://docs.docker.com/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Vue.js Documentation](https://vuejs.org/)

### Support Channels

- **GitHub Issues**: Bug reports and feature requests
- **Email Support**: support@vdock.app
- **Documentation**: Check this guide first
- **Community**: GitHub Discussions

## Maintenance Checklist

### Daily Checklist

- [ ] Service health checks
- [ ] Error log review
- [ ] Resource monitoring
- [ ] Backup verification

### Weekly Checklist

- [ ] Security log review
- [ ] Dependency update check
- [ ] Disk space monitoring
- [ ] Performance review

### Monthly Checklist

- [ ] Full system backup
- [ ] Security audit
- [ ] Performance optimization
- [ ] Documentation update

### Quarterly Checklist

- [ ] Disaster recovery testing
- [ ] Security penetration testing
- [ ] Capacity planning review
- [ ] Architecture review
