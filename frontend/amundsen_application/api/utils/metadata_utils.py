# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging

from dataclasses import dataclass
from marshmallow import EXCLUDE
from typing import Any, Dict, List

from amundsen_common.models.dashboard import DashboardSummary, DashboardSummarySchema
from amundsen_common.models.feature import Feature, FeatureSchema
from amundsen_common.models.popular_table import PopularTable, PopularTableSchema
from amundsen_common.models.table import Table, TableSchema
from amundsen_application.models.user import load_user, dump_user
from amundsen_application.config import MatchRuleObject
from flask import current_app as app
import re


@dataclass
class TableUri:
    database: str
    cluster: str
    schema: str
    table: str

    def __str__(self) -> str:
        return f"{self.database}://{self.cluster}.{self.schema}/{self.table}"

    @classmethod
    def from_uri(cls, uri: str) -> 'TableUri':
        """
        TABLE_KEY_FORMAT = '{db}://{cluster}.{schema}/{tbl}'
        """
        pattern = re.compile(r'^(?P<database>.*?)://(?P<cluster>.*)\.(?P<schema>.*?)/(?P<table>.*?)$', re.X)

        groups = pattern.match(uri)

        spec = groups.groupdict() if groups else {}

        return TableUri(**spec)


def marshall_table_partial(table_dict: Dict) -> Dict:
    """
    Forms a short version of a table Dict, with selected fields and an added 'key'
    :param table_dict: Dict of partial table object
    :return: partial table Dict

    TODO - Unify data format returned by search and metadata.
    """
    schema = PopularTableSchema()
    table: PopularTable = schema.load(table_dict, unknown=EXCLUDE)
    results = schema.dump(table)
    # TODO: fix popular tables to provide these? remove if we're not using them?
    # TODO: Add the 'key' or 'id' to the base PopularTableSchema
    results['key'] = f'{table.database}://{table.cluster}.{table.schema}/{table.name}'
    results['last_updated_timestamp'] = None
    results['type'] = 'table'

    return results


def _parse_editable_rule(rule: MatchRuleObject,
                         schema: str,
                         table: str) -> bool:
    """
    Matches table name and schema with corresponding regex in matching rule
    :parm rule: MatchRuleObject defined in list UNEDITABLE_TABLE_DESCRIPTION_MATCH_RULES in config file
    :parm schema: schema name from Table Dict received from metadata service
    :parm table: table name from Table Dict received from metadata service
    :return: boolean which determines if table desc is editable or not for given table as per input matching rule
    """
    if rule.schema_regex and rule.table_name_regex:
        match_schema = re.match(rule.schema_regex, schema)
        match_table = re.match(rule.table_name_regex, table)
        return not (match_schema and match_table)

    if rule.schema_regex:
        return not re.match(rule.schema_regex, schema)

    if rule.table_name_regex:
        return not re.match(rule.table_name_regex, table)

    return True


def is_table_editable(schema_name: str, table_name: str, cfg: Any = None) -> bool:
    if cfg is None:
        cfg = app.config

    if schema_name in cfg['UNEDITABLE_SCHEMAS']:
        return False

    for rule in cfg['UNEDITABLE_TABLE_DESCRIPTION_MATCH_RULES']:
        if not _parse_editable_rule(rule, schema_name, table_name):
            return False

    return True


def marshall_table_full(table_dict: Dict) -> Dict:
    """
    Forms the full version of a table Dict, with additional and sanitized fields
    :param table_dict: Table Dict from metadata service
    :return: Table Dict with sanitized fields
    """

    schema = TableSchema()
    table: Table = schema.load(table_dict)
    results: Dict[str, Any] = schema.dump(table)

    is_editable = is_table_editable(results['schema'], results['name'])
    results['is_editable'] = is_editable

    # TODO - Cleanup https://github.com/lyft/amundsen/issues/296
    #  This code will try to supplement some missing data since the data here is incomplete.
    #  Once the metadata service response provides complete user objects we can remove this.
    results['owners'] = [_map_user_object_to_schema(owner) for owner in results['owners']]
    readers = results['table_readers']
    for reader_object in readers:
        reader_object['user'] = _map_user_object_to_schema(reader_object['user'])

    columns = results['columns']
    for col in columns:
        # Set editable state
        col['is_editable'] = is_editable
        # If order is provided, we sort the column based on the pre-defined order
        if app.config['COLUMN_STAT_ORDER']:
            # the stat_type isn't defined in COLUMN_STAT_ORDER, we just use the max index for sorting
            col['stats'].sort(key=lambda x: app.config['COLUMN_STAT_ORDER'].
                              get(x['stat_type'], len(app.config['COLUMN_STAT_ORDER'])))

    # TODO: Add the 'key' or 'id' to the base TableSchema
    results['key'] = f'{table.database}://{table.cluster}.{table.schema}/{table.name}'
    # Temp code to make 'partition_key' and 'partition_value' part of the table
    results['partition'] = _get_partition_data(results['watermarks'])

    # We follow same style as column stat order for arranging the programmatic descriptions
    prog_descriptions = results['programmatic_descriptions']
    results['programmatic_descriptions'] = _convert_prog_descriptions(prog_descriptions)

    return results


def marshall_dashboard_partial(dashboard_dict: Dict) -> Dict:
    """
    Forms a short version of dashboard metadata, with selected fields and an added 'key'
    and 'type'
    :param dashboard_dict: Dict of partial dashboard metadata
    :return: partial dashboard Dict
    """
    schema = DashboardSummarySchema(unknown=EXCLUDE)
    dashboard: DashboardSummary = schema.load(dashboard_dict)
    results = schema.dump(dashboard)
    results['type'] = 'dashboard'
    # TODO: Bookmark logic relies on key, opting to add this here to avoid messy logic in
    # React app and we have to clean up later.
    results['key'] = results.get('uri', '')
    return results


def marshall_dashboard_full(dashboard_dict: Dict) -> Dict:
    """
    Cleanup some fields in the dashboard response
    :param dashboard_dict: Dashboard response from metadata service.
    :return: Dashboard dictionary with sanitized fields, particularly the tables and owners.
    """
    # TODO - Cleanup https://github.com/lyft/amundsen/issues/296
    #  This code will try to supplement some missing data since the data here is incomplete.
    #  Once the metadata service response provides complete user objects we can remove this.
    dashboard_dict['owners'] = [_map_user_object_to_schema(owner) for owner in dashboard_dict['owners']]
    dashboard_dict['tables'] = [marshall_table_partial(table) for table in dashboard_dict['tables']]
    return dashboard_dict


def marshall_lineage_table(table_dict: Dict) -> Dict:
    """
    Decorate lineage entries with database, schema, cluster, and table
    :param table_dict:
    :return: table entry with additional fields
    """
    table_key = str(table_dict.get('key'))
    table_uri = TableUri.from_uri(table_key)
    table_dict['database'] = table_uri.database
    table_dict['schema'] = table_uri.schema
    table_dict['cluster'] = table_uri.cluster
    table_dict['name'] = table_uri.table
    return table_dict


def _convert_prog_descriptions(prog_descriptions: List = None) -> Dict:
    """
    Apply the PROGRAMMATIC_DISPLAY configuration to convert to the structure.
    :param prog_descriptions: A list of objects representing programmatic descriptions
    :return: A dictionary with organized programmatic_descriptions
    """
    left = []  # type: List
    right = []  # type: List
    other = prog_descriptions or []  # type: List
    updated_descriptions = {}

    if prog_descriptions:
        # We want to make sure there is a display title that is just source
        for desc in prog_descriptions:
            source = desc.get('source')
            if not source:
                logging.warning("no source found in: " + str(desc))

        # If config is defined for programmatic disply we organize and sort them based on the configuration
        prog_display_config = app.config['PROGRAMMATIC_DISPLAY']
        if prog_display_config:
            left_config = prog_display_config.get('LEFT', {})
            left = [x for x in prog_descriptions if x.get('source') in left_config]
            left.sort(key=lambda x: _sort_prog_descriptions(left_config, x))

            right_config = prog_display_config.get('RIGHT', {})
            right = [x for x in prog_descriptions if x.get('source') in right_config]
            right.sort(key=lambda x: _sort_prog_descriptions(right_config, x))

            other_config = dict(filter(lambda x: x not in ['LEFT', 'RIGHT'], prog_display_config.items()))
            other = list(filter(lambda x: x.get('source') not in left_config and x.get('source')
                                not in right_config, prog_descriptions))
            other.sort(key=lambda x: _sort_prog_descriptions(other_config, x))

    updated_descriptions['left'] = left
    updated_descriptions['right'] = right
    updated_descriptions['other'] = other
    return updated_descriptions


def _sort_prog_descriptions(base_config: Dict, prog_description: Dict) -> int:
    default_order = len(base_config)
    prog_description_source = prog_description.get('source')
    config_dict = base_config.get(prog_description_source)
    if config_dict:
        return config_dict.get('display_order', default_order)
    return default_order


def _map_user_object_to_schema(u: Dict) -> Dict:
    return dump_user(load_user(u))


def _get_partition_data(watermarks: Dict) -> Dict:
    if watermarks:
        high_watermark = next(filter(lambda x: x['watermark_type'] == 'high_watermark', watermarks))
        if high_watermark:
            return {
                'is_partitioned': True,
                'key': high_watermark['partition_key'],
                'value': high_watermark['partition_value']
            }
    return {
        'is_partitioned': False
    }


def marshall_feature_full(feature_dict: Dict) -> Dict:
    """
    Forms the full version of a table Dict, with additional and sanitized fields
    :param table_dict: Table Dict from metadata service
    :return: Table Dict with sanitized fields
    """

    schema = FeatureSchema()
    feature: Feature = schema.load(feature_dict)
    results: Dict[str, Any] = schema.dump(feature)

    # TODO do we need this for Features?
    # is_editable = is_table_editable(results['schema'], results['name'])
    # results['is_editable'] = is_editable

    results['owners'] = [_map_user_object_to_schema(owner) for owner in results['owners']]

    prog_descriptions = results['programmatic_descriptions']
    results['programmatic_descriptions'] = _convert_prog_descriptions(prog_descriptions)

    return results
