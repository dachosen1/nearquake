up: 
	docker compose up -d --build && docker image prune -f
down: 
	docker compose down
test:
	python -m pytest

coverage-report:
	open htmlcov/index.html
linter:
	isort . && black .
