.PHONY: lint test coverage

lint:
	mypy --strict flutter.py test.py
	flake8 --max-line-length=100 flutter.py test.py

test:
	python3 test.py

coverage:
	coverage run test.py
	coverage report
	coverage html
	-rm .coverage
