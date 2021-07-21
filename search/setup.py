# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import os

from setuptools import find_packages, setup

__version__ = '2.11.0'

oidc = ['flaskoidc==1.0.0']

requirements_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'requirements.txt')
with open(requirements_path) as requirements_file:
    requirements = requirements_file.readlines()

requirements_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'requirements-common.txt')
with open(requirements_path) as requirements_file:
    requirements_common = requirements_file.readlines()

requirements_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'requirements-dev.txt')
with open(requirements_path) as requirements_file:
    requirements_dev = requirements_file.readlines()

all_deps = requirements + requirements_common + requirements_dev + oidc

setup(
    name='amundsen-search',
    version=__version__,
    description='Search Service for Amundsen',
    url='https://github.com/amundsen-io/amundsen/tree/main/search',
    maintainer='Amundsen TSC',
    maintainer_email='amundsen-tsc@lists.lfai.foundation',
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    zip_safe=False,
    dependency_links=[],
    install_requires=requirements + requirements_common,
    extras_require={
        'all': all_deps,
        'dev': requirements_dev,
        'oidc': oidc
    },
    python_requires=">=3.6"
)
