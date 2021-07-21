# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import csv
import importlib
from collections import defaultdict
from typing import Any, List

from pyhocon import ConfigTree

from databuilder.extractor.base_extractor import Extractor
from databuilder.models.badge import Badge, BadgeMetadata
from databuilder.models.table_lineage import ColumnLineage, TableLineage
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata


def split_badge_list(badges: str, separator: str) -> List[str]:
    """
    Splits a string of badges into a list, removing all empty badges.
    """
    if badges is None:
        return []

    return [badge for badge in badges.split(separator) if badge]


class CsvExtractor(Extractor):
    # Config keys
    FILE_LOCATION = 'file_location'

    """
    An Extractor that extracts records via CSV.
    """

    def init(self, conf: ConfigTree) -> None:
        """
        :param conf:
        """
        self.conf = conf
        self.file_location = conf.get_string(CsvExtractor.FILE_LOCATION)

        model_class = conf.get('model_class', None)
        if model_class:
            module_name, class_name = model_class.rsplit(".", 1)
            mod = importlib.import_module(module_name)
            self.model_class = getattr(mod, class_name)
        self._load_csv()

    def _load_csv(self) -> None:
        """
        Create an iterator to execute sql.
        """
        if not hasattr(self, 'results'):
            with open(self.file_location, 'r') as fin:
                self.results = [dict(i) for i in csv.DictReader(fin)]

        if hasattr(self, 'model_class'):
            results = [self.model_class(**result)
                       for result in self.results]
        else:
            results = self.results
        self.iter = iter(results)

    def extract(self) -> Any:
        """
        Yield the csv result one at a time.
        convert the result to model if a model_class is provided
        """
        try:
            return next(self.iter)
        except StopIteration:
            return None
        except Exception as e:
            raise e

    def get_scope(self) -> str:
        return 'extractor.csv'


class CsvTableBadgeExtractor(Extractor):
    # Config keys
    TABLE_FILE_LOCATION = 'table_file_location'
    BADGE_FILE_LOCATION = 'badge_file_location'
    BADGE_SEPARATOR = 'badge_separator'

    """
    An Extractor that combines Table and Badge CSVs.
    """
    def init(self, conf: ConfigTree) -> None:
        self.conf = conf
        self.table_file_location = conf.get_string(CsvTableBadgeExtractor.TABLE_FILE_LOCATION)
        self.badge_file_location = conf.get_string(CsvTableBadgeExtractor.BADGE_FILE_LOCATION)
        self.badge_separator = conf.get_string(CsvTableBadgeExtractor.BADGE_SEPARATOR, default=',')
        self._load_csv()

    def _get_key(self,
                 db: str,
                 cluster: str,
                 schema: str,
                 tbl: str
                 ) -> str:
        return TableMetadata.TABLE_KEY_FORMAT.format(db=db,
                                                     cluster=cluster,
                                                     schema=schema,
                                                     tbl=tbl)

    def _load_csv(self) -> None:
        with open(self.badge_file_location, 'r') as fin:
            self.badges = [dict(i) for i in csv.DictReader(fin)]
        # print("BADGES: " + str(self.badges))

        parsed_badges = defaultdict(list)
        for badge_dict in self.badges:
            db = badge_dict['database']
            cluster = badge_dict['cluster']
            schema = badge_dict['schema']
            table_name = badge_dict['table_name']
            id = self._get_key(db, cluster, schema, table_name)
            split_badges = split_badge_list(badges=badge_dict['name'],
                                            separator=self.badge_separator)
            for badge_name in split_badges:
                badge = Badge(name=badge_name, category=badge_dict['category'])
                parsed_badges[id].append(badge)

        with open(self.table_file_location, 'r') as fin:
            tables = [dict(i) for i in csv.DictReader(fin)]

        results = []
        for table_dict in tables:
            db = table_dict['database']
            cluster = table_dict['cluster']
            schema = table_dict['schema']
            table_name = table_dict['name']
            id = self._get_key(db, cluster, schema, table_name)
            badges = parsed_badges[id]

            if badges is None:
                badges = []
            badge_metadata = BadgeMetadata(start_label=TableMetadata.TABLE_NODE_LABEL,
                                           start_key=id,
                                           badges=badges)
            results.append(badge_metadata)
        self._iter = iter(results)

    def extract(self) -> Any:
        """
        Yield the csv result one at a time.
        convert the result to model if a model_class is provided
        """
        try:
            return next(self._iter)
        except StopIteration:
            return None
        except Exception as e:
            raise e

    def get_scope(self) -> str:
        return 'extractor.csvtablebadge'


class CsvTableColumnExtractor(Extractor):
    # Config keys
    TABLE_FILE_LOCATION = 'table_file_location'
    COLUMN_FILE_LOCATION = 'column_file_location'
    BADGE_SEPARATOR = 'badge_separator'

    """
    An Extractor that combines Table and Column CSVs.
    """

    def init(self, conf: ConfigTree) -> None:
        """
        :param conf:
        """
        self.conf = conf
        self.table_file_location = conf.get_string(CsvTableColumnExtractor.TABLE_FILE_LOCATION)
        self.column_file_location = conf.get_string(CsvTableColumnExtractor.COLUMN_FILE_LOCATION)
        self.badge_separator = conf.get_string(CsvTableBadgeExtractor.BADGE_SEPARATOR, default=',')
        self._load_csv()

    def _get_key(self,
                 db: str,
                 cluster: str,
                 schema: str,
                 tbl: str
                 ) -> str:
        return TableMetadata.TABLE_KEY_FORMAT.format(db=db,
                                                     cluster=cluster,
                                                     schema=schema,
                                                     tbl=tbl)

    def _load_csv(self) -> None:
        """
        Create an iterator to execute sql.
        """
        with open(self.column_file_location, 'r') as fin:
            self.columns = [dict(i) for i in csv.DictReader(fin)]

        parsed_columns = defaultdict(list)
        for column_dict in self.columns:
            db = column_dict['database']
            cluster = column_dict['cluster']
            schema = column_dict['schema']
            table_name = column_dict['table_name']
            id = self._get_key(db, cluster, schema, table_name)
            split_badges = split_badge_list(badges=column_dict['badges'],
                                            separator=self.badge_separator)
            column = ColumnMetadata(
                name=column_dict['name'],
                description=column_dict['description'],
                col_type=column_dict['col_type'],
                sort_order=int(column_dict['sort_order']),
                badges=split_badges
            )
            parsed_columns[id].append(column)

        # Create Table Dictionary
        with open(self.table_file_location, 'r') as fin:
            tables = [dict(i) for i in csv.DictReader(fin)]

        results = []
        for table_dict in tables:
            db = table_dict['database']
            cluster = table_dict['cluster']
            schema = table_dict['schema']
            table_name = table_dict['name']
            id = self._get_key(db, cluster, schema, table_name)
            columns = parsed_columns[id]
            if columns is None:
                columns = []
            table = TableMetadata(database=table_dict['database'],
                                  cluster=table_dict['cluster'],
                                  schema=table_dict['schema'],
                                  name=table_dict['name'],
                                  description=table_dict['description'],
                                  columns=columns,
                                  # TODO: this possibly should parse stringified booleans;
                                  # right now it only will be false for empty strings
                                  is_view=bool(table_dict['is_view']),
                                  tags=table_dict['tags']
                                  )
            results.append(table)
        self._iter = iter(results)

    def extract(self) -> Any:
        """
        Yield the csv result one at a time.
        convert the result to model if a model_class is provided
        """
        try:
            return next(self._iter)
        except StopIteration:
            return None
        except Exception as e:
            raise e

    def get_scope(self) -> str:
        return 'extractor.csvtablecolumn'


class CsvTableLineageExtractor(Extractor):
    # Config keys
    TABLE_LINEAGE_FILE_LOCATION = 'table_lineage_file_location'

    """
    An Extractor that creates Table Lineage between two tables
    """

    def init(self, conf: ConfigTree) -> None:
        """
        :param conf:
        """
        self.conf = conf
        self.table_lineage_file_location = conf.get_string(CsvTableLineageExtractor.TABLE_LINEAGE_FILE_LOCATION)
        self._load_csv()

    def _load_csv(self) -> None:
        """
        Create an iterator to execute sql.
        """

        with open(self.table_lineage_file_location, 'r') as fin:
            self.table_lineage = [dict(i) for i in csv.DictReader(fin)]

        results = []
        for lineage_dict in self.table_lineage:
            source_table_key = lineage_dict['source_table_key']
            target_table_key = lineage_dict['target_table_key']
            lineage = TableLineage(
                table_key=source_table_key,
                downstream_deps=[target_table_key]
            )
            results.append(lineage)

        self._iter = iter(results)

    def extract(self) -> Any:
        """
        Yield the csv result one at a time.
        convert the result to model if a model_class is provided
        """
        try:
            return next(self._iter)
        except StopIteration:
            return None
        except Exception as e:
            raise e

    def get_scope(self) -> str:
        return 'extractor.csvtablelineage'


class CsvColumnLineageExtractor(Extractor):
    # Config keys
    COLUMN_LINEAGE_FILE_LOCATION = 'column_lineage_file_location'

    """
    An Extractor that creates Column Lineage between two columns
    """

    def init(self, conf: ConfigTree) -> None:
        """
        :param conf:
        """
        self.conf = conf
        self.column_lineage_file_location = conf.get_string(CsvColumnLineageExtractor.COLUMN_LINEAGE_FILE_LOCATION)
        self._load_csv()

    def _load_csv(self) -> None:
        """
        Create an iterator to execute sql.
        """

        with open(self.column_lineage_file_location, 'r') as fin:
            self.column_lineage = [dict(i) for i in csv.DictReader(fin)]

        results = []
        for lineage_dict in self.column_lineage:
            source_column_key = lineage_dict['source_column_key']
            target_column_key = lineage_dict['target_column_key']
            lineage = ColumnLineage(
                column_key=source_column_key,
                downstream_deps=[target_column_key]
            )
            results.append(lineage)

        self._iter = iter(results)

    def extract(self) -> Any:
        """
        Yield the csv result one at a time.
        convert the result to model if a model_class is provided
        """
        try:
            return next(self._iter)
        except StopIteration:
            return None
        except Exception as e:
            raise e

    def get_scope(self) -> str:
        return 'extractor.csvcolumnlineage'
