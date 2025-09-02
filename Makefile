.PHONY: help validate lint test deploy-infra build-and-push update-secrets clean up down coverage coverage-report linter format

# Variables
STACK_NAME ?= nearquake-infrastructure
AWS_REGION ?= us-east-1
TEMPLATE_FILE ?= aws-infrastructure.yml

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Legacy Docker Compose commands (kept for local dev)
up: ## Start local development with Docker Compose
	docker compose up -d --build && docker image prune -f

down: ## Stop local development 
	docker compose down

# Testing and linting
test: ## Run tests
	uv run python -m pytest

live: 
	uv run main.py -l 

daily: 
	uv run main.py -d
	
weekly: 
	uv run main.py -w


monthly: 
	uv run main.py -m 

coverage: ## Run tests with coverage
	uv run python -m pytest --cov=nearquake --cov-report=term --cov-report=html --cov-report=xml

coverage-report: ## Open coverage report
	open htmlcov/index.html

linter: ## Run linter and formatter
	uv run isort . && uv run black .

validate: ## Validate CloudFormation template
	@echo "Validating CloudFormation template..."
	@aws cloudformation validate-template --template-body file://$(TEMPLATE_FILE) --region $(AWS_REGION) --output text > /dev/null
	@echo "✅ Template is valid"

lint: ## Lint Python code (check only)
	@echo "Linting Python code..."
	uv run black --check .
	uv run isort --check-only .
	@echo "✅ Code formatting is correct"

format: ## Format Python code
	@echo "Formatting Python code..."
	uv run black .
	uv run isort .
	@echo "✅ Code formatted"

# AWS Infrastructure commands
build-and-push: ## Build and push Docker image to ECR
	@echo "Building and pushing Docker image to ECR..."
	@echo "Logging into ECR..."
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(shell aws sts get-caller-identity --query Account --output text).dkr.ecr.$(AWS_REGION).amazonaws.com
	@echo "Building Docker image..."
	docker build --platform linux/amd64 -t nearquake .
	@echo "Tagging and pushing image..."
	docker tag nearquake:latest $(shell aws sts get-caller-identity --query Account --output text).dkr.ecr.$(AWS_REGION).amazonaws.com/nearquake:latest
	docker tag nearquake:latest $(shell aws sts get-caller-identity --query Account --output text).dkr.ecr.$(AWS_REGION).amazonaws.com/nearquake:$(shell git rev-parse --short HEAD)
	docker push $(shell aws sts get-caller-identity --query Account --output text).dkr.ecr.$(AWS_REGION).amazonaws.com/nearquake:latest
	docker push $(shell aws sts get-caller-identity --query Account --output text).dkr.ecr.$(AWS_REGION).amazonaws.com/nearquake:$(shell git rev-parse --short HEAD)
	@echo "✅ Image pushed to ECR successfully"

deploy-infra: validate build-and-push ## Deploy AWS infrastructure
	@echo "Deploying infrastructure stack: $(STACK_NAME)"
	aws cloudformation deploy \
		--template-file $(TEMPLATE_FILE) \
		--stack-name $(STACK_NAME) \
		--capabilities CAPABILITY_NAMED_IAM \
		--region $(AWS_REGION) \
		--no-fail-on-empty-changeset
	@echo "✅ Infrastructure deployed successfully"


stack-status: ## Show CloudFormation stack status
	aws cloudformation describe-stacks \
		--stack-name $(STACK_NAME) \
		--region $(AWS_REGION) \
		--query 'Stacks[0].StackStatus' \
		--output text

stack-outputs: ## Show CloudFormation stack outputs
	aws cloudformation describe-stacks \
		--stack-name $(STACK_NAME) \
		--region $(AWS_REGION) \
		--query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
		--output table

clean: ## Delete CloudFormation stack
	@echo "⚠️  This will delete the entire infrastructure stack!"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ]
	aws cloudformation delete-stack \
		--stack-name $(STACK_NAME) \
		--region $(AWS_REGION)
	@echo "🗑️  Stack deletion initiated"

# Logging commands
logs-live: ## Show logs for live task
	aws logs tail /aws/ecs/nearquake --filter-pattern "live" --follow

logs-daily: ## Show logs for daily task  
	aws logs tail /aws/ecs/nearquake --filter-pattern "daily" --follow

logs-weekly: ## Show logs for weekly task
	aws logs tail /aws/ecs/nearquake --filter-pattern "weekly" --follow

logs-monthly: ## Show logs for monthly task
	aws logs tail /aws/ecs/nearquake --filter-pattern "monthly" --follow

logs-fun: ## Show logs for fun task
	aws logs tail /aws/ecs/nearquake --filter-pattern "fun" --follow
