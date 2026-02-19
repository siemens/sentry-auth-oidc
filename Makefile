.PHONY: clean deps

# Upstream no longer tracks its own dependencies in the package as dev extras,
# so we cannot resolve them here as transitive dependencies. Instead we fetch
# their locked development dependencies.
# Likewise, their root-level conftest is not provided as a pytest plugin for
# use outside their own tests, but we need their fixtures. We fetch them into
# our own namespace here.
deps:
	git submodule update --init
	cd deps/sentry && uv export --format requirements.txt --output-file ../../.sentry-requirements.txt --no-editable --no-hashes --no-emit-project
	uv pip install -r .sentry-requirements.txt
	uv run python -c "import sysconfig, pathlib; pathlib.Path(sysconfig.get_path('purelib'), 'sentry.pth').write_text('$(shell pwd)/deps/sentry/src\n')"
	cp -f deps/sentry/tests/conftest.py tests/conftest.py

clean:
	rm -rf *.egg-info src/*.egg-info
	rm -rf dist build
