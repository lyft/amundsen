# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import subprocess

from setuptools import setup, find_packages

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PACKAGE_DIR = os.path.join(BASE_DIR, 'amundsen_application', 'static')


def is_npm_installed() -> bool:
    try:
        subprocess.check_call(['npm --version'], shell=True)
        return True
    except subprocess.CalledProcessError:
        return False


def build_js() -> None:
    if not is_npm_installed():
        logging.error('npm must be available')

    try:
        subprocess.check_call(['npm install'], cwd=PACKAGE_DIR, shell=True)
        subprocess.check_call(['npm run build'], cwd=PACKAGE_DIR, shell=True)
    except Exception as e:
        logging.warn('Installation of npm dependencies failed')
        logging.warn(str(e))


build_js()

requirements_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'requirements.txt')
with open(requirements_path) as requirements_file:
    requirements = requirements_file.readlines()

requirements_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'requirements-common.txt')
with open(requirements_path) as requirements_file:
    requirements_common = requirements_file.readlines()

requirements_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'requirements-dev.txt')
with open(requirements_path) as requirements_file:
    requirements_dev = requirements_file.readlines()

__version__ = '3.11.1'

oidc = ['flaskoidc==1.0.0']
pyarrrow = ['pyarrow==3.0.0']
bigquery_preview = ['google-cloud-bigquery>=2.13.1,<3.0.0', 'flatten-dict==0.3.0']
all_deps = requirements + requirements_common + requirements_dev + oidc + pyarrrow + bigquery_preview

setup(
    name='amundsen-frontend',
    version=__version__,
    description='Web UI for Amundsen',
    url='https://www.github.com/amundsen-io/amundsen/tree/main/frontend',
    maintainer='Amundsen TSC',
    maintainer_email='amundsen-tsc@lists.lfai.foundation',
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    dependency_links=[],
    setup_requires=['cython >= 0.29'],
    install_requires=requirements + requirements_common,
    extras_require={
        'oidc': oidc,
        'dev': requirements_dev,
        'pyarrow': pyarrrow,
        'bigquery_preview': bigquery_preview,
        'all': all_deps,
    },
    python_requires=">=3.6",
    entry_points="""
        [action_log.post_exec.plugin]
        logging_action_log=amundsen_application.log.action_log_callback:logging_action_log
    """,
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
