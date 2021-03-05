.PHONY: clean develop test

develop:
	pip3 install -e git+https://github.com/getsentry/sentry.git#egg=sentry[dev]
	poetry install -n --no-dev
	poetry build
	pip3 install -U dist/*.whl
	pip3 install codecov

test:
	@echo "--> Running Python tests"
	pytest tests || exit 1
	@echo ""

clean:
	rm -rf *.egg-info src/*.egg-info
	rm -rf dist build
