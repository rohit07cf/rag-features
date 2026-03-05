# RAG Assistant Studio - Development Makefile
# ============================================
#
# This Makefile provides convenient commands for managing the RAG Assistant Studio
# development environment using Docker Compose and local development servers.

.PHONY: help up down dev clean logs install

# Default target
help: ## Show this help message
	@echo "RAG Assistant Studio Development Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Docker Compose targets
up: ## Start all services (Temporal, API, Worker, Streamlit UI)
	@echo "🚀 Starting RAG Assistant Studio services..."
	@if [ ! -f .env ]; then \
		echo "❌ .env file not found. Copying from .env.example..."; \
		cp .env.example .env; \
		echo "✅ Created .env file. Please edit it with your API keys."; \
	fi
	docker-compose up --build -d
	@echo "✅ Services starting up..."
	@echo "🌐 API: http://localhost:8000"
	@echo "📊 API Docs: http://localhost:8000/docs"
	@echo "🎨 UI: http://localhost:8501"
	@echo "⏰ Temporal UI: http://localhost:8080"
	@echo "📝 Check logs with: make logs"

down: ## Stop all services and clean up
	@echo "🛑 Stopping RAG Assistant Studio services..."
	docker-compose down -v
	@echo "✅ Services stopped and volumes cleaned up"

# Development targets
dev: ## Start local development server with file watching
	@echo "🔧 Starting local development environment..."
	@if [ ! -f .env ]; then \
		echo "❌ .env file not found. Copying from .env.example..."; \
		cp .env.example .env; \
		echo "✅ Created .env file. Please edit it with your API keys."; \
	fi
	@echo "📦 Installing/updating dependencies..."
	pip install -e ".[dev]"
	@echo "🚀 Starting FastAPI server with file watching..."
	python dev_server.py

# Utility targets
logs: ## Show logs from all services
	docker-compose logs -f

logs-api: ## Show API service logs
	docker-compose logs -f api

logs-temporal: ## Show Temporal service logs
	docker-compose logs -f temporal

clean: ## Clean up Docker resources
	@echo "🧹 Cleaning up Docker resources..."
	docker-compose down -v --remove-orphans
	docker system prune -f
	@echo "✅ Cleanup complete"

install: ## Install Python dependencies
	@echo "📦 Installing Python dependencies..."
	pip install -e ".[dev]"
	@echo "✅ Dependencies installed"

# Development helpers
setup: ## Initial project setup
	@echo "🔧 Setting up RAG Assistant Studio..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Created .env file from template"; \
	fi
	@echo "📦 Installing dependencies..."
	pip install -e ".[dev]"
	@echo "📁 Creating data directory..."
	mkdir -p data
	@echo "✅ Setup complete! Run 'make dev' to start development server"

test: ## Run tests
	@echo "🧪 Running tests..."
	pytest tests/ -v

lint: ## Run code linting
	@echo "🔍 Running linter..."
	ruff check .
	ruff format --check .