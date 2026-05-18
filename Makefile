.PHONY: run test install format

install:
	pip install -r requirements.txt -r requirements-dev.txt

run:
	uvicorn solver:app --host 0.0.0.0 --port 8080 --reload

test:
	pytest test_solver.py

format:
	pre-commit run --all-files
