.PHONY: clean deps

# Upstream no longer tracks its own dependencies in the package as dev extras,
# so we cannot resolve them here as transitive dependencies. Instead we fetch
# their locked development dependencies.
# Likewise, their root-level conftest is not provided as a pytest plugin for
# use outside their own tests, but we need their fixtures. We fetch them into
# our own namespace here.
# We also sync the Python version from upstream to ensure compatibility.
deps:
	git submodule update --init
	poetry run pip install -r deps/sentry/requirements-dev-frozen.txt -e deps/sentry
	cp -f deps/sentry/tests/conftest.py tests/conftest.py
	cp -f deps/sentry/.python-version .python-version

clean:
	rm -rf *.egg-info src/*.egg-info
	rm -rf dist build
