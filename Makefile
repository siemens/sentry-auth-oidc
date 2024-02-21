SENTRY_VERSION := 24.2.0

.PHONY: clean develop test

develop:
	pip3 install -e git+https://github.com/getsentry/sentry.git@$(SENTRY_VERSION)#egg=sentry[dev]
	poetry install -n --no-dev
	poetry build && pip3 install -U dist/*.whl
	pip3 install -U codecov pytest freezegun fixtures

test:
	@echo "--> Running Python tests"
	python -m pytest tests || exit 1
	@echo ""

clean:
	rm -rf *.egg-info src/*.egg-info
	rm -rf dist build
