#!/usr/bin/env python
from __future__ import absolute_import
from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

install_requires = [
    'sentry>=7.0.0',
    'python-gitlab>=1.5.1',
    'requests<2.19.0,>=2.18.4',
]

tests_require = [
    'flake8>=3.5',
]

setup(
    name='sentry-auth-oidc',
    version='1.0.1',
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
            'sentry_auth_oidc = sentry_auth_oidc',
        ],
    },
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
    ],
)
