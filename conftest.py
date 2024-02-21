import os
import sys

os.environ.setdefault("DB", "postgres")

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

pytest_plugins = ["sentry.testutils.pytest"]
