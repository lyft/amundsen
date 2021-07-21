# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging

import click
from flask import current_app
from flask.cli import AppGroup

from metadata_service import config
from metadata_service.client.rds_client import RDSClient

LOGGER = logging.getLogger(__name__)

rds_cli = AppGroup('rds')


@rds_cli.command('initdb')
def init_db() -> None:
    """
    Initialize/upgrade the metadata database
    according to the latest rds schema version.
    """
    client = RDSClient(current_app.config['SQLALCHEMY_DATABASE_URI'],
                       current_app.config[config.PROXY_CLIENT_KWARGS])
    client.init_db()
    click.echo('DB is initialized successfully.')


@rds_cli.command('resetdb')
@click.option('--yes', 'confirmed', is_flag=True)
def reset_db(confirmed: str) -> None:
    """
    Reset the metadata database.
    """
    if confirmed or input("This will drop all the existing tables. Proceed? (y/n)").upper() == 'Y':
        client = RDSClient(current_app.config['SQLALCHEMY_DATABASE_URI'],
                           current_app.config[config.PROXY_CLIENT_KWARGS])
        client.reset_db()
        click.echo('DB is reset successfully.')
    else:
        click.echo('Cancelled.')
