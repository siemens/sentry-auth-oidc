.PHONY: clean deps

# Upstream no longer tracks its own dependencies in the package as dev extras,
# so we cannot resolve them here as transitive dependencies. Instead we fetch
# their locked development dependencies.
# Likewise, their root-level conftest is not provided as a pytest plugin for
# use outside their own tests, but we need their fixtures. We fetch them into
# our own namespace here.
deps:
	git submodule update --init
	uv pip install --index-url https://pypi.org/simple -r deps/sentry/requirements-dev-frozen.txt -e deps/sentry
	cp -f deps/sentry/tests/conftest.py tests/conftest.py

clean:
	rm -rf *.egg-info src/*.egg-info
	rm -rf dist build
