# VDock Production Deployment Guide

This guide covers deploying VDock to production environments with proper security, monitoring, and maintenance practices.

## Prerequisites

- Docker and Docker Compose installed
- Domain name and SSL certificates (for production)
- Backup strategy in place
- Monitoring solution configured

## Quick Start

### 1. Clone and Configure

```bash
git clone <repository-url>
cd VDock
cp env.example .env
```

### 2. Configure Environment

Edit `.env` file with production values:

```bash
# Security (REQUIRED)
SECRET_KEY=your-very-secure-secret-key-here
AUTH_PASSWORD=your-very-secure-password-here

# Production Settings
DEBUG=False
REQUIRE_AUTH=True
ALLOW_LAN=False
USE_SSL=True

# Spotify Integration (Optional)
SPOTIFY_CLIENT_ID=your-spotify-client-id
SPOTIFY_CLIENT_SECRET=your-spotify-client-secret
```

### 3. Deploy

**Linux/macOS:**
```bash
./deploy.sh
```

**Windows:**
```cmd
deploy.bat
```

## Production Configuration

### Security Checklist

- [ ] Change default `SECRET_KEY` to a secure random string
- [ ] Set strong `AUTH_PASSWORD`
- [ ] Enable `REQUIRE_AUTH=True`
- [ ] Set `ALLOW_LAN=False` for localhost-only access
- [ ] Configure SSL certificates (`USE_SSL=True`)
- [ ] Set up firewall rules
- [ ] Regular security updates

### SSL/TLS Setup

1. Obtain SSL certificates from a trusted CA
2. Place certificates in the project root:
   ```
   cert.pem  # Certificate file
   key.pem   # Private key file
   ```
3. Set `USE_SSL=True` in `.env`
4. Update `CORS_ORIGINS` to use HTTPS URLs

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | Flask secret key | Random | Yes |
| `AUTH_PASSWORD` | Admin password | Empty | Yes |
| `DEBUG` | Debug mode | False | No |
| `REQUIRE_AUTH` | Require authentication | True | No |
| `ALLOW_LAN` | Allow LAN access | False | No |
| `USE_SSL` | Enable SSL/TLS | False | No |
| `HOST` | Server host | 127.0.0.1 | No |
| `PORT` | Server port | 5000 | No |

## Docker Deployment

### Using Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Update services
docker-compose pull
docker-compose up -d
```

### Manual Docker Commands

```bash
# Build backend
docker build -t vdock-backend ./backend

# Build frontend
docker build -t vdock-frontend ./frontend

# Run backend
docker run -d \
  --name vdock-backend \
  -p 5000:5000 \
  -v $(pwd)/backend/data:/app/data \
  -e SECRET_KEY=your-secret-key \
  -e AUTH_PASSWORD=your-password \
  vdock-backend

# Run frontend
docker run -d \
  --name vdock-frontend \
  -p 3000:80 \
  -e VITE_API_BASE_URL=http://localhost:5000 \
  vdock-frontend
```

## Monitoring and Maintenance

### Health Checks

- Backend: `http://localhost:5000/api/health`
- Frontend: `http://localhost:3000`

### Log Management

```bash
# View all logs
docker-compose logs -f

# View backend logs only
docker-compose logs -f vdock-backend

# View frontend logs only
docker-compose logs -f vdock-frontend
```

### Backup Strategy

1. **Profile Data**: Backup `backend/data/profiles/` directory
2. **Uploads**: Backup `backend/data/uploads/` directory
3. **Configuration**: Backup `.env` file
4. **SSL Certificates**: Backup certificate files

```bash
# Create backup
tar -czf vdock-backup-$(date +%Y%m%d).tar.gz \
  backend/data/ \
  .env \
  *.pem

# Restore backup
tar -xzf vdock-backup-YYYYMMDD.tar.gz
```

### Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

## Performance Optimization

### Backend Optimization

- Use production WSGI server (Gunicorn)
- Enable gzip compression
- Configure caching headers
- Use connection pooling for databases

### Frontend Optimization

- Enable gzip compression in nginx
- Set proper cache headers
- Use CDN for static assets
- Minimize bundle size

### Database Optimization

- Use external database for production
- Configure connection pooling
- Set up database backups
- Monitor query performance

## Security Best Practices

### Network Security

- Use reverse proxy (nginx/Apache)
- Configure firewall rules
- Use VPN for remote access
- Enable rate limiting

### Application Security

- Regular dependency updates
- Security headers configuration
- Input validation and sanitization
- SQL injection prevention

### Data Security

- Encrypt sensitive data at rest
- Use secure communication protocols
- Implement proper access controls
- Regular security audits

## Troubleshooting

### Common Issues

**Service won't start:**
```bash
# Check logs
docker-compose logs

# Check configuration
docker-compose config
```

**Backend connection refused:**
- Check if port 5000 is available
- Verify firewall settings
- Check backend logs for errors

**Frontend can't connect to backend:**
- Verify `VITE_API_BASE_URL` setting
- Check CORS configuration
- Ensure backend is running

**SSL certificate issues:**
- Verify certificate files exist
- Check certificate validity
- Ensure proper file permissions

### Performance Issues

**Slow response times:**
- Check server resources (CPU, memory)
- Review application logs
- Monitor database performance
- Optimize queries

**High memory usage:**
- Check for memory leaks
- Monitor application metrics
- Consider scaling resources

## Scaling

### Horizontal Scaling

- Use load balancer
- Multiple backend instances
- Shared storage for data
- Session management

### Vertical Scaling

- Increase server resources
- Optimize application code
- Use faster storage
- Implement caching

## Support

For production support:

1. Check logs first
2. Review this documentation
3. Check GitHub issues
4. Contact support team

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.
