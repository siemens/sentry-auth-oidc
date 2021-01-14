.PHONY: clean develop install-tests lint publish test

develop:
	pip3 install -U "pip>=7"
	pip3 install -e git+https://github.com/getsentry/sentry.git#egg=sentry[dev]
	pip3 install -e .
	make install-tests

install-tests:
	pip3 install .[tests]

lint:
	@echo "--> Linting python"
	flake8
	@echo ""

test:
	@echo "--> Running Python tests"
	py.test tests || exit 1
	@echo ""

publish:
	python3 setup.py sdist bdist_wheel upload

clean:
	rm -rf *.egg-info src/*.egg-info
	rm -rf dist build
