#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 ELUXRAJ Backend${NC}"
echo "================================"

case "$1" in
    "dev")
        echo -e "${YELLOW}Starting development server...${NC}"
        docker-compose up -d db redis
        sleep 3
        echo -e "${GREEN}Running migrations...${NC}"
        alembic upgrade head 2>/dev/null || echo "Migrations skipped (run manually if needed)"
        echo -e "${GREEN}Starting API on http://localhost:8000${NC}"
        echo -e "${GREEN}Docs at http://localhost:8000/docs${NC}"
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
        ;;
    
    "docker")
        echo -e "${YELLOW}Starting with Docker...${NC}"
        docker-compose up --build
        ;;
    
    "test")
        echo -e "${YELLOW}Running tests...${NC}"
        pytest tests/ -v --tb=short
        ;;
    
    "migrate")
        echo -e "${YELLOW}Running migrations...${NC}"
        alembic upgrade head
        echo -e "${GREEN}Migrations complete!${NC}"
        ;;
    
    "makemigration")
        echo -e "${YELLOW}Creating new migration...${NC}"
        read -p "Migration message: " msg
        alembic revision --autogenerate -m "$msg"
        echo -e "${GREEN}Migration created!${NC}"
        ;;
    
    "lint")
        echo -e "${YELLOW}Running linter...${NC}"
        ruff check app/ tests/
        ;;
    
    "format")
        echo -e "${YELLOW}Formatting code...${NC}"
        ruff format app/ tests/
        ;;
    
    "db")
        echo -e "${YELLOW}Starting database only...${NC}"
        docker-compose up -d db redis
        echo -e "${GREEN}PostgreSQL: localhost:5432${NC}"
        echo -e "${GREEN}Redis: localhost:6379${NC}"
        ;;
    
    "stop")
        echo -e "${YELLOW}Stopping services...${NC}"
        docker-compose down
        echo -e "${GREEN}Stopped!${NC}"
        ;;
    
    "clean")
        echo -e "${RED}Cleaning up (removing volumes)...${NC}"
        docker-compose down -v
        rm -rf logs/*.log
        rm -f test.db
        echo -e "${GREEN}Cleaned!${NC}"
        ;;
    
    "install")
        echo -e "${YELLOW}Installing dependencies...${NC}"
        pip install -r requirements.txt
        echo -e "${GREEN}Dependencies installed!${NC}"
        ;;
    
    *)
        echo "Usage: ./run.sh [command]"
        echo ""
        echo "Commands:"
        echo "  dev           Start development server"
        echo "  docker        Start with Docker Compose"
        echo "  test          Run test suite"
        echo "  migrate       Run database migrations"
        echo "  makemigration Create new migration"
        echo "  lint          Run code linter"
        echo "  format        Format code"
        echo "  db            Start database only"
        echo "  stop          Stop all services"
        echo "  clean         Remove all data and volumes"
        echo "  install       Install Python dependencies"
        ;;
esac
