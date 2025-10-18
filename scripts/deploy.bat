@echo off
REM VDock Production Deployment Script for Windows

echo 🚀 Starting VDock production deployment...

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo ⚠️  .env file not found. Creating from template...
    copy env.example .env
    echo 📝 Please edit .env file with your configuration before running deployment.
    echo    Especially set SECRET_KEY and AUTH_PASSWORD!
    pause
    exit /b 1
)

echo ✅ Environment validation passed.

REM Create necessary directories
echo 📁 Creating data directories...
if not exist backend\data mkdir backend\data
if not exist backend\data\profiles mkdir backend\data\profiles
if not exist backend\data\uploads mkdir backend\data\uploads
if not exist backend\data\plugins mkdir backend\data\plugins
if not exist backend\data\themes mkdir backend\data\themes

echo ✅ Directories created.

REM Build and start services
echo 🔨 Building Docker images...
docker-compose build

echo 🚀 Starting services...
docker-compose up -d

REM Wait for services to be healthy
echo ⏳ Waiting for services to be healthy...
timeout /t 10 /nobreak >nul

REM Check service health
echo 🔍 Checking service health...

REM Check backend health
curl -f http://localhost:5000/api/health >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Backend health check failed
    docker-compose logs vdock-backend
    pause
    exit /b 1
) else (
    echo ✅ Backend is healthy
)

REM Check frontend health
curl -f http://localhost:3000 >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Frontend health check failed
    docker-compose logs vdock-frontend
    pause
    exit /b 1
) else (
    echo ✅ Frontend is healthy
)

echo.
echo 🎉 VDock deployment completed successfully!
echo.
echo 📋 Service Information:
echo    Frontend: http://localhost:3000
echo    Backend API: http://localhost:5000
echo    Health Check: http://localhost:5000/api/health
echo.
echo 📊 Management Commands:
echo    View logs: docker-compose logs -f
echo    Stop services: docker-compose down
echo    Restart services: docker-compose restart
echo    Update services: docker-compose pull ^&^& docker-compose up -d
echo.
echo ⚠️  Security Notes:
echo    - Change the default password immediately
echo    - Use HTTPS in production
echo    - Regularly update dependencies
echo    - Monitor logs for security issues
echo.
pause
