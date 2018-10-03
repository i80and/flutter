.PHONY: lint test

lint:
	mypy --strict flutter.py
	flake8 --max-line-length=100 flutter.py

test:
