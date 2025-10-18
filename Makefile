.PHONY: dev down logs ingest-once embed-cache test clean

dev:
	@echo "Building and starting Truth Layer MVP..."
	docker-compose up --build -d
	@echo "✅ Backend API: http://localhost:8000"
	@echo "✅ Frontend UI: http://localhost:3000"
	@echo "✅ Health Check: http://localhost:8000/health"

down:
	@echo "Stopping all services..."
	docker-compose down

logs:
	docker-compose logs -f

ingest-once:
	@echo "Running single ingestion pipeline..."
	docker-compose exec worker python -m app.workers.run_once

embed-cache:
	@echo "Pre-downloading sentence-transformers model..."
	docker-compose exec worker python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

test:
	@echo "Running backend tests..."
	docker-compose exec backend pytest tests/ -v
	@echo "Running frontend tests..."
	docker-compose exec frontend npm test

clean:
	@echo "Cleaning up containers and volumes..."
	docker-compose down -v
	rm -rf data/app.db

help:
	@echo "Truth Layer MVP - Available Commands:"
	@echo "  make dev          - Build and start all services"
	@echo "  make down         - Stop all services"
	@echo "  make logs         - Tail logs from all services"
	@echo "  make ingest-once  - Run single ingestion pipeline"
	@echo "  make embed-cache  - Pre-download ML model"
	@echo "  make test         - Run all tests"
	@echo "  make clean        - Clean up containers and database"
