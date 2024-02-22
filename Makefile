SENTRY_VERSION := 24.2.0

.PHONY: clean deps

# Upstream no longer tracks its own dependencies in the package as dev extras,
# so we cannot resolve them here as transitive dependencies. Instead we fetch
# their locked development dependencies.
# Likewise, their root-level conftest is not provided as a pytest plugin for
# use outside their own tests, but we need their fixtures. We fetch them into
# our own namespace here.
deps:
	curl -L -o requirements-sentry.txt https://github.com/getsentry/sentry/raw/$(SENTRY_VERSION)/requirements-dev-frozen.txt
	curl -L -o tests/conftest.py https://github.com/getsentry/sentry/raw/$(SENTRY_VERSION)/tests/conftest.py
	poetry run pip install -r requirements-sentry.txt

clean:
	rm -rf *.egg-info src/*.egg-info
	rm -rf dist build
