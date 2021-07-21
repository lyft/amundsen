# Amundsen Metadata Service
[![PyPI version](https://badge.fury.io/py/amundsen-metadata.svg)](https://badge.fury.io/py/amundsen-metadata)
[![Build Status](https://api.travis-ci.com/lyft/amundsenmetadatalibrary.svg?branch=master)](https://travis-ci.com/lyft/amundsenmetadatalibrary)
[![Coverage Status](https://img.shields.io/codecov/c/github/lyft/amundsenmetadatalibrary/master.svg)](https://codecov.io/github/lyft/amundsenmetadatalibrary?branch=master)
[![License](https://img.shields.io/:license-Apache%202-blue.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#developer-guide)
[![Slack Status](https://img.shields.io/badge/slack-join_chat-white.svg?logo=slack&style=social)](https://amundsenworkspace.slack.com/join/shared_invite/enQtNTk2ODQ1NDU1NDI0LTc3MzQyZmM0ZGFjNzg5MzY1MzJlZTg4YjQ4YTU0ZmMxYWU2MmVlMzhhY2MzMTc1MDg0MzRjNTA4MzRkMGE0Nzk)

Amundsen Metadata service serves Restful API and is responsible for providing and also updating metadata, such as table & column description, and tags. Metadata service can use Neo4j, Apache Atlas, AWS Neptune Or Mysql RDS as a persistent layer.

For information about Amundsen and our other services, refer to this [README.md](./../README.md). Please also see our instructions for a [quick start](./../docs/installation.md#bootstrap-a-default-version-of-amundsen-using-docker) setup  of Amundsen with dummy data, and an [overview of the architecture](./../docs/architecture.md#architecture).

## Requirements
- Python >= 3.7

## Doc
- https://www.amundsen.io/amundsen/

## Instructions to start the Metadata service from distribution
```bash
$ venv_path=[path_for_virtual_environment]
$ python3 -m venv $venv_path
$ source $venv_path/bin/activate
$ pip3 install amundsen-metadata
$ python3 metadata_service/metadata_wsgi.py

-- In a different terminal, verify getting HTTP/1.0 200 OK
$ curl -v http://localhost:5002/healthcheck
```

## Instructions to start the Metadata service from the source
```bash
$ git clone https://github.com/amundsen-io/amundsenmetadatalibrary.git
$ cd amundsenmetadatalibrary
$ python3 -m venv venv
$ source venv/bin/activate
$ pip3 install -e ".[all]" .
$ python3 metadata_service/metadata_wsgi.py

-- In a different terminal, verify getting HTTP/1.0 200 OK
$ curl -v http://localhost:5002/healthcheck
```

## Instructions to start the service from Docker

```bash
$ docker pull amundsendev/amundsen-metadata:latest
$ docker run -p 5002:5002 amundsendev/amundsen-metadata
# - alternative, for production environment with Gunicorn (see its homepage link below)
$ ## docker run -p 5002:5002 amundsendev/amundsen-metadata gunicorn --bind 0.0.0.0:5002 metadata_service.metadata_wsgi

-- In a different terminal, verify getting HTTP/1.0 200 OK
$ curl -v http://localhost:5002/healthcheck
```


## Production environment
By default, Flask comes with Werkzeug webserver, which is for development. For production environment use production grade web server such as [Gunicorn](https://gunicorn.org/ "Gunicorn").

```bash
$ pip install gunicorn
$ gunicorn metadata_service.metadata_wsgi
```
Here is [documentation](https://docs.gunicorn.org/en/latest/run.html "documentation") of gunicorn configuration.

### Configuration outside local environment
By default, Metadata service uses [LocalConfig](./../metadata/metadata_service/config.py "LocalConfig") that looks for Neo4j running in localhost.
In order to use different end point, you need to create [Config](./../metadata/metadata_service/config.py "Config") suitable for your use case. Once config class has been created, it can be referenced by [environment variable](./../metadata/metadata_service/metadata_wsgi.py "environment variable"): `METADATA_SVC_CONFIG_MODULE_CLASS`

For example, in order to have different config for production, you can inherit Config class, create Production config and passing production config class into environment variable. Let's say class name is ProdConfig and it's in metadata_service.config module. then you can set as below:

`METADATA_SVC_CONFIG_MODULE_CLASS=metadata_service.config.ProdConfig`

This way Metadata service will use production config in production environment. For more information on how the configuration is being loaded and used, here's reference from Flask [doc](http://flask.pocoo.org/docs/1.0/config/#development-production "doc").

# Apache Atlas
Amundsen Metadata service can use Apache Atlas as a backend. Some of the benefits of using Apache Atlas instead of Neo4j is that Apache Atlas offers plugins to several services (e.g. Apache Hive, Apache Spark) that allow for push based updates. It also allows to set policies on what metadata is accessible and editable by means of Apache Ranger.

Apache Atlas is a data governance service meaning you also get Apache Atlas UI for easy access to your metadata. It is, however, aimed for administrators rather then end-users, which we suggest to direct towards Amundsen UI.

Apache Atlas is so far the only proxy in Amundsen supporting both push and pull for collecting metadata:
- `Push` method by leveraging Apache Atlas Hive Hook. It's an event listener running alongside Hive Metastore, translating Hive Metastore events into Apache Atlas entities and `pushing` them to Kafka topic, from which Apache Atlas ingests the data by internal processes.
- `Pull` method by leveraging Amundsen Databuilder integration with Apache Atlas. It means that extractors available in Databuilder can be used to collect metadata about external systems (like PostgresMetadataExtractor) and sending them to Apache Atlas in a shape consumable by Amundsen.

If you would like to use Apache Atlas as a backend for Metadata service you will need to create a [Config](./../metadata/metadata_service/config.py "Config") as mentioned above. Make sure to include the following:

```python
PROXY_CLIENT = PROXY_CLIENTS['ATLAS'] # or env PROXY_CLIENT='ATLAS'
PROXY_PORT = 21000          # or env PROXY_PORT
PROXY_USER = 'atlasuser'    # or env CREDENTIALS_PROXY_USER
PROXY_PASSWORD = 'password' # or env CREDENTIALS_PROXY_PASSWORD
```

To start the service with Atlas from Docker. Make sure you have `atlasserver` configured in DNS (or docker-compose)

```bash
$ docker run -p 5002:5002 --env PROXY_CLIENT=ATLAS --env PROXY_PORT=21000 --env PROXY_HOST=atlasserver --env CREDENTIALS_PROXY_USER=atlasuser --env CREDENTIALS_PROXY_PASSWORD=password amundsen-metadata:latest
```

---
**NOTE**

While Apache Atlas supports fine grained access, Amundsen does not support this yet.

# Developer guide
## Code style
- PEP 8: Amundsen Metadata service follows [PEP8 - Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/ "PEP8 - Style Guide for Python Code").
- Typing hints: Amundsen Metadata service also utilizes [Typing hint](https://docs.python.org/3/library/typing.html "Typing hint") for better readability.

## API documentation

We have Swagger documentation setup with OpenApi 3.0.2. This documentation is generated via Flasgger. When adding or updating an API please make sure to update the documentation. To see the documentation run the application locally and go to localhost:5002/apidocs/. Currently the documentation only works with local configuration.

## Code structure
Please visit [Code Structure](docs/structure.md) to read how different modules are structured in Amundsen Metadata service.

## Roundtrip tests
Roundtrip tests are a new feature - by implementing the abstract_proxy_tests and some test setup endpoints in the base_proxy, you can validate your proxy code against the actual data store. These tests do not run by default, but can be run by passing the `--roundtrip-[proxy]` argument. Note this requires
a fully-configured backend to test against.
```bash
$ python -m pytest --roundtrip-neptune .
```
