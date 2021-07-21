"""
The Generic Usage Extractor allows you to populate the "Frequent Users" and "Popular Tables" features within
Amundsen with the help of the TableColumnUsage class. Because this is a generic usage extractor, you need to create
a custom log parser to calculate poplarity. There is an example of how to calculate table popularity for Snowflake
in databuilder/example/scripts/sample_snowflake_table_usage.scala.
"""

import logging
from typing import (
    Any, Dict, Iterator, Union,
)

from pyhocon import ConfigFactory, ConfigTree

from databuilder import Scoped
from databuilder.extractor import sql_alchemy_extractor
from databuilder.extractor.base_extractor import Extractor
from databuilder.extractor.sql_alchemy_extractor import SQLAlchemyExtractor
from databuilder.models.table_column_usage import ColumnReader, TableColumnUsage

LOGGER = logging.getLogger(__name__)


class GenericUsageExtractor(Extractor):
    # SELECT statement from table that contains usage data
    SQL_STATEMENT = """
        SELECT
            database,
            schema,
            name,
            user_email,
            read_count
        FROM
            {database}.{schema}.{table}
        {where_clause_suffix};
    """
    # CONFIG KEYS
    WHERE_CLAUSE_SUFFIX_KEY = 'where_clause_suffix'
    POPULARITY_TABLE_DATABASE = 'popularity_table_database'
    POPULARTIY_TABLE_SCHEMA = 'popularity_table_schema'
    POPULARITY_TABLE_NAME = 'popularity_table_name'
    DATABASE_KEY = 'database_key'

    DEFAULT_CONFIG = ConfigFactory.from_dict(
        {WHERE_CLAUSE_SUFFIX_KEY: ' ',
         POPULARITY_TABLE_DATABASE: 'PROD',
         POPULARTIY_TABLE_SCHEMA: 'SCHEMA',
         POPULARITY_TABLE_NAME: 'TABLE',
         DATABASE_KEY: 'snowflake'}
    )

    def init(self, conf: ConfigTree) -> None:
        conf = conf.with_fallback(GenericUsageExtractor.DEFAULT_CONFIG)
        self._where_clause_suffix = conf.get_string(GenericUsageExtractor.WHERE_CLAUSE_SUFFIX_KEY)
        self._popularity_table_database = conf.get_string(GenericUsageExtractor.POPULARITY_TABLE_DATABASE)
        self._popularity_table_schema = conf.get_string(GenericUsageExtractor.POPULARTIY_TABLE_SCHEMA)
        self._popularity_table_name = conf.get_string(GenericUsageExtractor.POPULARITY_TABLE_NAME)
        self._database_key = conf.get_string(GenericUsageExtractor.DATABASE_KEY)

        self.sql_stmt = GenericUsageExtractor.SQL_STATEMENT.format(
            where_clause_suffix=self._where_clause_suffix,
            database=self._popularity_table_database,
            schema=self._popularity_table_schema,
            table=self._popularity_table_name
        )

        LOGGER.info("SQL for popularity: {}".format(self.sql_stmt))

        self._alchemy_extractor = sql_alchemy_extractor.from_surrounding_config(conf, self.sql_stmt)
        sql_alch_conf = Scoped.get_scoped_conf(conf, self._alchemy_extractor.get_scope()) \
            .with_fallback(ConfigFactory.from_dict({SQLAlchemyExtractor.EXTRACT_SQL: self.sql_stmt}))
        self._alchemy_extractor.init(sql_alch_conf)
        self._extract_iter: Union[None, Iterator] = None

    def extract(self) -> Union[TableColumnUsage, None]:
        if not self._extract_iter:
            self._extract_iter = self._get_extract_iter()
        try:
            return next(self._extract_iter)
        except StopIteration:
            return None

    def get_scope(self) -> str:
        return "extractor.generic_usage"

    def _get_extract_iter(self) -> Iterator[TableColumnUsage]:
        """
        Using raw level iterator, it groups to table and yields TableColumnUsage
        :return:
        """
        for row in self._get_raw_extract_iter():
            col_readers = []
            col_readers.append(ColumnReader(database=self._database_key,
                                            cluster=row["database"],
                                            schema=row["schema"],
                                            table=row["name"],
                                            column="*",
                                            user_email=row["user_email"],
                                            read_count=row["read_count"]))
            yield TableColumnUsage(col_readers=col_readers)

    def _get_raw_extract_iter(self) -> Iterator[Dict[str, Any]]:
        """
        Provides iterator of result row from SQLAlchemy extractor
        :return:
        """
        row = self._alchemy_extractor.extract()
        while row:
            yield row
            row = self._alchemy_extractor.extract()
