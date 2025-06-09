#!/bin/bash

# EdgeUp Docker Build and Deploy Script
# This script builds and deploys the EdgeUp application using Docker Compose

set -e  # Exit on any error

echo "🚀 EdgeUp Docker Deployment Script"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker Compose is available
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not available. Please install Docker Compose or update Docker."
    exit 1
fi

# Check if .env file exists
if [ ! -f "python/.env" ]; then
    print_warning ".env file not found in python/ directory"
    print_status "Creating .env file from template..."
    cp python/.env.example python/.env
    print_warning "Please edit python/.env with your actual API keys before running the application"
fi

# Create uploads directory if it doesn't exist
mkdir -p uploads

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  dev     - Start development environment (default docker-compose.yml)"
    echo "  prod    - Start production environment with MongoDB (docker-compose.prod.yml)"
    echo "  build   - Build Docker images only"
    echo "  stop    - Stop all services"
    echo "  logs    - Show application logs"
    echo "  clean   - Stop services and remove containers/images"
    echo "  help    - Show this help message"
}

# Parse command line arguments
COMMAND=${1:-dev}

case $COMMAND in
    "dev")
        print_status "Starting development environment..."
        docker compose down --remove-orphans
        docker compose up --build -d
        print_success "Development environment started!"
        print_status "Frontend: http://localhost:80"
        print_status "Backend API: http://localhost:8000"
        print_status "Health Check: http://localhost:8000/health"
        ;;
    
    "prod")
        print_status "Starting production environment with MongoDB..."
        docker compose -f docker-compose.prod.yml down --remove-orphans
        docker compose -f docker-compose.prod.yml up --build -d
        print_success "Production environment started!"
        print_status "Frontend: http://localhost:80"
        print_status "Backend API: http://localhost:8000"
        print_status "MongoDB: localhost:27017"
        print_status "Health Check: http://localhost:8000/health"
        ;;
    
    "build")
        print_status "Building Docker images..."
        docker compose build
        print_success "Docker images built successfully!"
        ;;
    
    "stop")
        print_status "Stopping all services..."
        docker compose down
        docker compose -f docker-compose.prod.yml down
        print_success "All services stopped!"
        ;;
    
    "logs")
        print_status "Showing application logs..."
        docker compose logs -f
        ;;
    
    "clean")
        print_status "Cleaning up containers and images..."
        docker compose down --remove-orphans --volumes
        docker compose -f docker-compose.prod.yml down --remove-orphans --volumes
        docker system prune -f
        print_success "Cleanup completed!"
        ;;
    
    "help"|"-h"|"--help")
        show_usage
        ;;
    
    *)
        print_error "Unknown command: $COMMAND"
        show_usage
        exit 1
        ;;
esac

echo ""
print_status "Useful commands:"
echo "  docker compose logs -f          # Follow logs"
echo "  docker compose ps               # List running containers"
echo "  docker compose exec backend sh  # Access backend container"
echo "  docker compose exec frontend sh # Access frontend container"
