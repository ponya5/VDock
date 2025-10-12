#!/bin/bash

# VDock Production Deployment Script

set -e

echo "🚀 Starting VDock production deployment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp env.example .env
    echo "📝 Please edit .env file with your configuration before running deployment."
    echo "   Especially set SECRET_KEY and AUTH_PASSWORD!"
    exit 1
fi

# Load environment variables
source .env

# Validate required environment variables
if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "your-secret-key-here" ]; then
    echo "❌ SECRET_KEY is not set or is using default value."
    echo "   Please set a secure SECRET_KEY in .env file."
    exit 1
fi

if [ -z "$AUTH_PASSWORD" ] || [ "$AUTH_PASSWORD" = "your-secure-password-here" ]; then
    echo "❌ AUTH_PASSWORD is not set or is using default value."
    echo "   Please set a secure AUTH_PASSWORD in .env file."
    exit 1
fi

echo "✅ Environment validation passed."

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p backend/data/profiles
mkdir -p backend/data/uploads
mkdir -p backend/data/plugins
mkdir -p backend/data/themes

# Set proper permissions
chmod 755 backend/data
chmod 755 backend/data/profiles
chmod 755 backend/data/uploads
chmod 755 backend/data/plugins
chmod 755 backend/data/themes

echo "✅ Directories created with proper permissions."

# Build and start services
echo "🔨 Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check backend health
if curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    docker-compose logs vdock-backend
    exit 1
fi

# Check frontend health
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is healthy"
else
    echo "❌ Frontend health check failed"
    docker-compose logs vdock-frontend
    exit 1
fi

echo ""
echo "🎉 VDock deployment completed successfully!"
echo ""
echo "📋 Service Information:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:5000"
echo "   Health Check: http://localhost:5000/api/health"
echo ""
echo "🔐 Login Information:"
echo "   Password: $AUTH_PASSWORD"
echo ""
echo "📊 Management Commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart services: docker-compose restart"
echo "   Update services: docker-compose pull && docker-compose up -d"
echo ""
echo "⚠️  Security Notes:"
echo "   - Change the default password immediately"
echo "   - Use HTTPS in production"
echo "   - Regularly update dependencies"
echo "   - Monitor logs for security issues"
