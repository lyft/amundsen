# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import Any
import logging

from flask import Flask, render_template
import jinja2
import os

from amundsen_application.api.healthcheck import run_healthcheck


ENVIRONMENT = os.getenv('APPLICATION_ENV', 'development')
LOGGER = logging.getLogger(__name__)


def init_routes(app: Flask) -> None:
    app.add_url_rule('/healthcheck', 'healthcheck', run_healthcheck)
    app.add_url_rule('/', 'index', index, defaults={'path': ''})  # also functions as catch_all
    app.add_url_rule('/<path:path>', 'index', index)  # catch_all


def index(path: str) -> Any:
    try:
        return render_template("index.html", env=ENVIRONMENT)  # pragma: no cover
    except jinja2.exceptions.TemplateNotFound as e:
        LOGGER.error("index.html template not found, have you built the front-end JS (npm run build in static/?")
        raise e
