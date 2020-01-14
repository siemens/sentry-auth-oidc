#!/usr/bin/env python
from __future__ import absolute_import
from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

install_requires = [
    'requests<3.0.0'
]

tests_require = [
    'flake8<3.6.0,>=3.5.0',
]

setup(
    name='sentry-auth-oidc',
    version='3.0.0',
    author='Max Wittig',
    author_email='max.wittig@siemens.com',
    url='https://www.getsentry.com',
    description='OpenID Connect authentication provider for Sentry',
    long_description=readme,
    license='Apache 2.0',
    packages=find_packages(exclude=['tests']),
    zip_safe=False,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={'tests': tests_require},
    include_package_data=True,
    entry_points={
        'sentry.apps': [
            'oidc = oidc.apps.Config',
        ],
    },
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
    ],
)
