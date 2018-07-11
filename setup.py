#!/usr/bin/env python
"""
sentry-auth-google
==================

:copyright: (c) 2016 Functional Software, Inc
"""
from setuptools import setup, find_packages


install_requires = [
    'sentry>=7.0.0',
]

tests_require = [
    'flake8>=2.0,<2.1',
]

setup(
    name='sentry-auth-oidc',
    version='1.0.0',
    author='Sentry',
    author_email='support@getsentry.com',
    url='https://www.getsentry.com',
    description='OpenID Connect authentication provider for Sentry',
    long_description=__doc__,
    license='Apache 2.0',
    packages=find_packages(exclude=['tests']),
    zip_safe=False,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={'tests': tests_require},
    include_package_data=True,
    entry_points={
        'sentry.apps': [
            'sentry_auth_oidc = sentry_auth_oidc',
        ],
    },
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
)
