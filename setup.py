#!/usr/bin/env python
from __future__ import absolute_import

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
    'flake8<3.6.0,>=3.5.0',
]

setup(
    name='sentry-auth-google',
    version='0.2.0.dev0',
    author='Sentry',
    author_email='support@getsentry.com',
    url='https://www.getsentry.com',
    description='Google authentication provider for Sentry',
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
            'auth_google = sentry_auth_google',
        ],
    },
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
)
