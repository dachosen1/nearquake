up: 
	docker compose up -d --build

prune: 
	docker image prune -f

test:
	python -m pytest

coverage:
	python -m pytest --cov=nearquake --cov-report=term --cov-report=html

coverage-report:
	open htmlcov/index.html