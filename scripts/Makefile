.PHONY: help install test clean lint format docs start-dashboard start-agent start-streaming docker-build docker-run

help: ## Show this help message
	@echo "Aegis SRE Agent - Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r ../config/requirements.txt
	pip install -e ../scripts/setup.py

install-dev: ## Install development dependencies
	pip install -r ../config/requirements.txt
	pip install -e ../scripts/setup.py[dev]

test: ## Run tests
	pytest tests/ -v --cov=agents --cov=orchestration --cov=ml_pipeline

test-watch: ## Run tests in watch mode
	pytest tests/ -v --cov=agents --cov=orchestration --cov=ml_pipeline -f

lint: ## Run linting
	flake8 agents/ orchestration/ ml_pipeline/ tests/
	mypy agents/ orchestration/ ml_pipeline/

format: ## Format code
	black agents/ orchestration/ ml_pipeline/ tests/
	isort agents/ orchestration/ ml_pipeline/ tests/

clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/

docs: ## Generate documentation
	mkdir -p docs/_build
	sphinx-build -b html docs/ docs/_build/html

start-infrastructure: ## Start Docker infrastructure
	docker-compose -f ../config/docker-compose.yml up -d
	@echo "Waiting for services to be ready..."
	sleep 30

stop-infrastructure: ## Stop Docker infrastructure
	docker-compose -f ../config/docker-compose.yml down

start-dashboard: ## Start the dashboard server
	python ../orchestration/dashboard_server_simple.py

start-agent: ## Start the SRE agent
	python ../orchestration/sre_agent_orchestrator.py

start-streaming: ## Start log streaming
	python ../orchestration/streaming_integration.py

generate-data: ## Generate synthetic data
	python ../orchestration/synthetic_data_generator.py --training
	python ../orchestration/synthetic_data_generator.py --streaming

train-models: ## Train ML models
	python ../ml_pipeline/anomaly_detector.py --train

setup: ## Complete setup (install, generate data, train models)
	$(MAKE) install
	$(MAKE) start-infrastructure
	$(MAKE) generate-data
	$(MAKE) train-models

docker-build: ## Build Docker image
	docker build -t aegis-sre-agent ..

docker-run: ## Run Docker container
	docker run -d -p 8082:8082 --name aegis-sre-agent aegis-sre-agent

docker-stop: ## Stop Docker container
	docker stop aegis-sre-agent
	docker rm aegis-sre-agent

logs: ## View application logs
	tail -f logs/dashboard.log

logs-docker: ## View Docker logs
	docker-compose -f ../config/docker-compose.yml logs -f

status: ## Check system status
	@echo "=== Docker Services ==="
	docker-compose -f ../config/docker-compose.yml ps
	@echo ""
	@echo "=== Python Processes ==="
	ps aux | grep python | grep -v grep || echo "No Python processes running"
	@echo ""
	@echo "=== Port Usage ==="
	lsof -i :8082 || echo "Port 8082 not in use"

reset: ## Reset everything (clean, reinstall, restart)
	$(MAKE) clean
	$(MAKE) stop-infrastructure
	$(MAKE) install
	$(MAKE) start-infrastructure
	$(MAKE) generate-data
	$(MAKE) train-models

# Development shortcuts
dev: ## Start development environment
	$(MAKE) start-infrastructure
	$(MAKE) start-dashboard

quick-test: ## Quick test of the system
	python tests/test_complete_system.py

# Production deployment
deploy: ## Deploy to production
	$(MAKE) docker-build
	$(MAKE) docker-run

undeploy: ## Undeploy from production
	$(MAKE) docker-stop 