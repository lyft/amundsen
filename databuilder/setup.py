# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0
import os

from setuptools import find_packages, setup

__version__ = '5.2.4'

requirements_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'requirements.txt')
with open(requirements_path) as requirements_file:
    requirements = requirements_file.readlines()

requirements_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'requirements-dev.txt')
with open(requirements_path) as requirements_file:
    requirements_dev = requirements_file.readlines()

kafka = ['confluent-kafka==1.0.0']

cassandra = ['cassandra-driver==3.20.1']

glue = ['boto3==1.17.23']

snowflake = [
    'snowflake-connector-python',
    'snowflake-sqlalchemy'
]

athena = ['PyAthena[SQLAlchemy]>=1.0.0, <2.0.0']

# Python API client for google
# License: Apache Software License
# Upstream url: https://github.com/googleapis/google-api-python-client
bigquery = [
    'google-api-python-client>=1.6.0, <2.0.0dev',
    'google-auth-httplib2>=0.0.1',
    'google-auth>=1.0.0, <2.0.0dev'
]

jsonpath = ['jsonpath_rw==1.4.0']

db2 = [
    'ibm_db==3.0.1',
    'ibm-db-sa-py3==0.3.1-1'
]

dremio = [
    'pyodbc==4.0.30'
]

druid = [
    'pydruid'
]

spark = [
    'pyspark == 3.0.1'
]

neptune = [
    'amundsen-gremlin>=0.0.9',
    'Flask==1.0.2',
    'gremlinpython==3.4.3',
    'requests-aws4auth==1.1.0',
    'typing-extensions==3.7.4',
    'overrides==2.5',
    'boto3==1.17.23'
]

feast = [
    'feast==0.8.0'
]

atlas = [
    'pyatlasclient==1.1.2',
    'apache-atlas>=0.0.11'
]

rds = [
    'sqlalchemy>=1.3.6,<1.4',
    'mysqlclient>=1.3.6,<3'
]

salesforce = [
    'simple-salesforce>=1.11.2'
]

all_deps = requirements + requirements_dev + kafka + cassandra + glue + snowflake + athena + \
    bigquery + jsonpath + db2 + dremio + druid + spark + feast + neptune + rds + atlas + salesforce

setup(
    name='amundsen-databuilder',
    version=__version__,
    description='Amundsen Data builder',
    url='https://www.github.com/amundsen-io/amundsen/tree/main/databuilder',
    maintainer='Amundsen TSC',
    maintainer_email='amundsen-tsc@lists.lfai.foundation',
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    dependency_links=[],
    install_requires=requirements,
    python_requires='>=3.6',
    extras_require={
        'all': all_deps,
        'dev': requirements_dev,
        'kafka': kafka,  # To use with Kafka source extractor
        'cassandra': cassandra,
        'glue': glue,
        'snowflake': snowflake,
        'athena': athena,
        'bigquery': bigquery,
        'jsonpath': jsonpath,
        'db2': db2,
        'dremio': dremio,
        'druid': druid,
        'neptune': neptune,
        'delta': spark,
        'feast': feast,
        'atlas': atlas,
        'rds': rds,
        'salesforce': salesforce,
    },
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
