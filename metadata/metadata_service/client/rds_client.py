# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import contextlib
import logging
import os
from typing import Dict

import amundsen_rds
from alembic import command, script
from alembic.config import Config
from alembic.runtime import migration
from alembic.runtime.migration import MigrationContext
from amundsen_rds.models.base import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

LOGGER = logging.getLogger(__name__)


class RDSClient:
    """
    Client used by mysql proxy and rds commands
    """
    def __init__(self, sql_alchemy_url: str, client_kwargs: Dict = dict()) -> None:
        self.sql_alchemy_url = sql_alchemy_url
        self.engine = create_engine(sql_alchemy_url, **client_kwargs)
        self.session_factory = sessionmaker(bind=self.engine)

    def init_db(self) -> None:
        """
        Initialize a relational database
        """
        LOGGER.info('Initializing the metadata database')

        config = self._get_alembic_config()
        config.set_main_option('sqlalchemy.url', self.sql_alchemy_url.replace('%', '%%'))

        command.upgrade(config, 'heads')

    def reset_db(self) -> None:
        """
        Reset schema
        """
        LOGGER.info('Resetting the metadata database')

        self.drop_models()
        self.init_db()

    def drop_models(self) -> None:
        """
        Drop rds models
        """
        LOGGER.info('Dropping rds models')

        Base.metadata.drop_all(self.engine)

        with self.engine.connect() as connection:
            migration_ctx = MigrationContext.configure(connection)
            version = migration_ctx._version
            if version.exists(connection):
                version.drop(connection)

    def validate_schema_version(self) -> bool:
        """
        Check if the schema from the given connection is the latest one
        """
        LOGGER.info('Validating schema version.')

        config = self._get_alembic_config()
        script_directory = script.ScriptDirectory.from_config(config)

        with self.engine.begin() as conn:
            context = migration.MigrationContext.configure(conn)
            current_version = context.get_current_revision()
            current_head = script_directory.get_current_head()

            LOGGER.info(f'current_version: {current_version}, current_head: {current_head}')

        return current_version == current_head

    @staticmethod
    def _get_alembic_config() -> Config:
        """
        Get alembic config
        """
        amundsen_rds_dir = os.path.dirname(os.path.abspath(amundsen_rds.__file__))
        migration_path = os.path.join(amundsen_rds_dir, 'migrations')
        config = Config(os.path.join(amundsen_rds_dir, 'alembic.ini'))
        config.set_main_option('script_location', migration_path.replace('%', '%%'))

        return config

    @contextlib.contextmanager
    def create_session(self) -> Session:
        """
        Create a SQLAlchemy session
        """
        session = self.session_factory()
        try:
            yield session
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
