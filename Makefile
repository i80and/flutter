.PHONY: lint test

lint:
	mypy --strict flutter test.py
	flake8 --max-line-length=100 flutter test.py

test:
	coverage run test.py
	coverage report
