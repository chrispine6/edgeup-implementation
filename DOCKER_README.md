# EdgeUp Docker Deployment Guide

This guide explains how to containerize and deploy the EdgeUp AI document processing application using Docker.

## 🏗️ Architecture

The containerized application consists of:

- **Frontend**: React app served by Nginx with API proxying
- **Backend**: Python FastAPI service for document processing and AI interactions
- **Database**: MongoDB for user data, document chunks, and conversation history (production only)

## 📋 Prerequisites

- Docker (v20.0+)
- Docker Compose (v2.0+)
- At least 4GB RAM available for containers

## 🚀 Quick Start

### Development Environment

```bash
# 1. Clone and navigate to the project
cd edgeup-implementation

# 2. Set up environment variables
cp python/.env.example python/.env
# Edit python/.env with your API keys

# 3. Start the application
./docker-deploy.sh dev
```

### Production Environment (with MongoDB)

```bash
# Start production environment with MongoDB
./docker-deploy.sh prod
```

## ⚙️ Configuration

### Environment Variables

Create `python/.env` with the following variables:

```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# MongoDB Configuration (for production)
MONGODB_URI=mongodb://admin:password123@mongodb:27017/edgeup?authSource=admin

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment_here
PINECONE_INDEX_NAME=your_pinecone_index_name_here

# Application Configuration
DEBUG=False
PORT=8000
HOST=0.0.0.0
```

### Firebase Configuration

Update `client/src/firebase.js` with your Firebase configuration if needed.

## 🐳 Docker Commands

### Using the Deploy Script

```bash
# Development environment
./docker-deploy.sh dev

# Production with MongoDB
./docker-deploy.sh prod

# Build images only
./docker-deploy.sh build

# Stop all services
./docker-deploy.sh stop

# View logs
./docker-deploy.sh logs

# Clean up everything
./docker-deploy.sh clean
```

### Manual Docker Compose

```bash
# Development
docker-compose up --build -d

# Production
docker-compose -f docker-compose.prod.yml up --build -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f [service_name]
```

## 🌐 Access Points

After deployment:

- **Frontend**: http://localhost:80
- **Backend API**: http://localhost:8000
- **API Health Check**: http://localhost:8000/health
- **MongoDB** (prod only): localhost:27017

## 📁 File Structure

```
edgeup-implementation/
├── docker-compose.yml          # Development environment
├── docker-compose.prod.yml     # Production with MongoDB
├── Dockerfile.frontend         # React app container
├── Dockerfile.backend          # Python API container
├── nginx.conf                  # Nginx configuration
├── mongo-init.js              # MongoDB initialization
├── docker-deploy.sh           # Deployment script
├── .dockerignore              # Docker ignore rules
├── client/                    # React frontend
├── python/                    # Python backend
└── uploads/                   # File uploads (mounted volume)
```

## 🔧 Customization

### Nginx Configuration

Edit `nginx.conf` to:
- Add SSL certificates
- Modify proxy settings
- Change port configurations
- Add custom headers

### Resource Limits

Add resource limits to `docker-compose.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          memory: 512M
```

### Environment-Specific Overrides

Create additional compose files:
- `docker-compose.staging.yml`
- `docker-compose.local.yml`

## 🐛 Troubleshooting

### Common Issues

1. **Port conflicts**:
   ```bash
   # Check what's using ports
   sudo lsof -i :80
   sudo lsof -i :8000
   ```

2. **Permission issues**:
   ```bash
   # Fix uploads directory permissions
   sudo chown -R $USER:$USER uploads/
   ```

3. **API connection errors**:
   - Check backend container logs: `docker-compose logs backend`
   - Verify environment variables in `.env`
   - Ensure MongoDB is running (prod environment)

4. **Build failures**:
   ```bash
   # Clean build cache
   docker builder prune
   docker-compose build --no-cache
   ```

### Health Checks

```bash
# Check container status
docker-compose ps

# Test API health
curl http://localhost:8000/health

# Check MongoDB connection (prod)
docker-compose exec mongodb mongo -u admin -p password123
```

### Logs and Debugging

```bash
# Follow all logs
docker-compose logs -f

# Specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Access container shell
docker-compose exec backend sh
docker-compose exec frontend sh
```

## 🔒 Security Considerations

### Production Deployment

1. **Change default passwords** in `docker-compose.prod.yml`
2. **Use environment-specific `.env` files**
3. **Enable HTTPS** by updating nginx configuration
4. **Restrict network access** using Docker networks
5. **Regular security updates** for base images

### Environment Variables

- Never commit `.env` files to version control
- Use Docker secrets for sensitive data in production
- Rotate API keys regularly

## 📈 Scaling

### Horizontal Scaling

```yaml
services:
  backend:
    deploy:
      replicas: 3
    depends_on:
      - mongodb
```

### Load Balancing

Add a load balancer service:

```yaml
  nginx-lb:
    image: nginx:alpine
    volumes:
      - ./nginx-lb.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
    depends_on:
      - backend
```

## 🎯 Performance Optimization

### Image Optimization

- Use multi-stage builds (already implemented)
- Minimize layer count
- Use `.dockerignore` effectively
- Choose appropriate base images

### Runtime Optimization

- Configure resource limits
- Use health checks
- Implement proper logging
- Monitor container metrics

## 📝 Maintenance

### Regular Tasks

```bash
# Update images
docker-compose pull

# Backup MongoDB data
docker-compose exec mongodb mongodump --archive=/data/backup.archive

# Clean up unused resources
docker system prune

# Update application
git pull
./docker-deploy.sh prod
```

### Monitoring

- Set up container monitoring (Prometheus/Grafana)
- Configure log aggregation (ELK stack)
- Implement application health checks
- Monitor resource usage

---

For more information, see the main [README.md](README.md) file.
