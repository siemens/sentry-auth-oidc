.PHONY: clean deps

# Upstream no longer tracks its own dependencies in the package as dev extras,
# so we cannot resolve them here as transitive dependencies. Instead we fetch
# their locked development dependencies.
# Since Sentry v26, uv is used for dependency management instead of pip.
# We export the uv.lock to requirements.txt format and install it, then
# manually add sentry to the Python path since it can't be installed editable.
# Likewise, their root-level conftest is not provided as a pytest plugin for
# use outside their own tests, but we need their fixtures. We fetch them into
# our own namespace here.
deps:
	git submodule update --init
	cd deps/sentry && uv export --format requirements.txt --output-file ../../.sentry-requirements.txt --no-editable --no-hashes --no-emit-project
	poetry run pip install -r .sentry-requirements.txt
	poetry run python -c "import sysconfig, pathlib; pathlib.Path(sysconfig.get_path('purelib'), 'sentry.pth').write_text('$(shell pwd)/deps/sentry/src\n')"
	cp -f deps/sentry/tests/conftest.py tests/conftest.py

clean:
	rm -rf *.egg-info src/*.egg-info
	rm -rf dist build
