.PHONY: format lint test fetch-tessdata precommit

format:
	python -m black .
	python -m ruff --fix .

lint:
	python -m ruff .

test:
	python -m pytest -q

fetch-tessdata:
	powershell -ExecutionPolicy Bypass -File scripts/fetch_tessdata.ps1

precommit: format lint test
