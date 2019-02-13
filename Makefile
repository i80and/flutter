.PHONY: lint test

lint:
	mypy --strict flutter test_flutter.py
	flake8 --max-line-length=100 flutter test_flutter.py

test:
	pytest --cov=flutter
	coverage report
