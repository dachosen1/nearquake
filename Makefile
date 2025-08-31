up: 
	docker compose up -d --build && docker image prune -f
down: 
	docker compose down
test:
	uv run python -m pytest
coverage:
	uv run python -m pytest --cov=nearquake --cov-report=term --cov-report=html --cov-report=xml
coverage-report:
	open htmlcov/index.html
linter:
	uv run isort . && uv run black .
