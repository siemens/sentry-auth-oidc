from __future__ import absolute_import

import sys
import os

# Run tests against sqlite for simplicity
os.environ.setdefault('DB', 'postgres')

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

pytest_plugins = [
    'sentry.utils.pytest'
]
