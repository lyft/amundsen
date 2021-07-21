import json
import logging
import re
from typing import Dict

from apache_atlas.client.base_client import AtlasClient
from apache_atlas.exceptions import AtlasServiceException
from apache_atlas.model.misc import SearchFilter
from apache_atlas.model.typedef import AtlasTypesDef
from requests import Timeout

from databuilder.types.atlas.types_def import (
    application_schema, bookmark_schema, cluster_schema, column_schema, column_table_relation, dashboard_chart_schema,
    dashboard_execution_schema, dashboard_group_schema, dashboard_query_schema, dashboard_schema, data_owner_schema,
    database_cluster_relation, database_schema, hive_table_partition, lineage_schema, reader_referenceable_relation,
    reader_schema, report_schema, schema_cluster_relation, schema_schema, source_schema, table_partition_schema,
    table_schema, table_schema_relation, table_source_relation, user_reader_relation, user_schema,
)

LOGGER = logging.getLogger(__name__)


# noinspection PyMethodMayBeStatic
class AtlasEntityInitializer:
    def __init__(self, client: AtlasClient) -> None:
        self.driver = client

    def assign_subtypes(self, regex: str, super_type: str) -> None:
        LOGGER.info(f'\nAssigning {super_type} entity to all the subtypes entity definitions with postfix ')
        entities_to_update = []
        entity_defs = self.driver.typedef.get_all_typedefs(search_filter=SearchFilter()).get('entityDefs', [])

        for e in entity_defs:
            if re.compile(regex).match(e.name) is not None:
                LOGGER.info(f'Assigning {e.name} as a subtype of {super_type}')
                e["superTypes"].append(super_type)
                entities_to_update.append(e)

        typedef_dict = {
            "entityDefs": entities_to_update
        }

        self.driver.typedef.update_atlas_typedefs(AtlasTypesDef(attrs=typedef_dict))
        LOGGER.info(f'Assignment of "{super_type}" Entity to existing "{regex}" entities Completed.\n')

    def create_or_update(self, typedef_dict: Dict, info: str, attempt: int = 1) -> None:
        try:
            LOGGER.info(f"Trying to create {info} Entity")
            self.driver.typedef.create_atlas_typedefs(AtlasTypesDef(attrs=typedef_dict))
        except AtlasServiceException:
            LOGGER.info(f"Already Exists, updating {info} Entity")
            try:
                self.driver.typedef.update_atlas_typedefs(AtlasTypesDef(attrs=typedef_dict))
            except Exception:
                # This is a corner case, for Atlas Sample Data
                LOGGER.warn(f"Error updating {info} Entity.", exc_info=True)

        except Timeout:
            # Sometimes on local atlas instance you do get ReadTimeout a lot.
            # This will try to apply definition 3 times and then cancel
            if attempt < 4:
                LOGGER.info("ReadTimeout - Another Try.")
                self.create_or_update(typedef_dict, info, attempt + 1)
            else:
                LOGGER.info(f"ReadTimeout Exception - Cancelling Operation: {attempt}", exc_info=True)
        except Exception:
            LOGGER.info(f"Error creating/updating {info} Entity Definition", exc_info=True)
        finally:
            LOGGER.info(f"Applied {info} Entity Definition")

    def get_schema_dict(self, schema: str) -> Dict:
        return json.loads(schema)

    def create_table_schema(self) -> None:
        self.create_or_update(self.get_schema_dict(table_schema), "Table")

    def create_column_schema(self) -> None:
        self.create_or_update(self.get_schema_dict(column_schema), "Column")

    def create_column_table_relation(self) -> None:
        self.create_or_update(self.get_schema_dict(column_table_relation), "Column <-> Table")

    def create_cluster_schema(self) -> None:
        self.create_or_update(self.get_schema_dict(cluster_schema), "Cluster")

    def create_database_schema(self) -> None:
        self.create_or_update(self.get_schema_dict(database_schema), "Database")

    def create_database_cluster_relation(self) -> None:
        self.create_or_update(self.get_schema_dict(database_cluster_relation), "Database <-> Cluster")

    def create_schema_schema(self) -> None:
        self.create_or_update(self.get_schema_dict(schema_schema), "Schema")

    def create_schema_cluster_relation(self) -> None:
        self.create_or_update(self.get_schema_dict(schema_cluster_relation), "Schema <-> Database")

    def create_table_schema_relation(self) -> None:
        self.create_or_update(self.get_schema_dict(table_schema_relation), "Table <-> Schema")

    def create_user_schema(self) -> None:
        self.create_or_update(self.get_schema_dict(user_schema), "User")

    def create_reader_schema(self) -> None:
        self.create_or_update(self.get_schema_dict(reader_schema), "Reader")

    def create_bookmark_schema(self) -> None:
        self.create_or_update(self.get_schema_dict(bookmark_schema), "Bookmark")

    def create_report_schema(self) -> None:
        self.create_or_update(self.get_schema_dict(report_schema), "Report")

    def create_user_reader_relation(self) -> None:
        self.create_or_update(self.get_schema_dict(user_reader_relation), "User <-> Reader")

    def create_reader_referenceable_relation(self) -> None:
        self.create_or_update(self.get_schema_dict(reader_referenceable_relation), "Reader <-> Referenceable")

    def create_table_partition_schema(self) -> None:
        self.create_or_update(self.get_schema_dict(table_partition_schema), "Partition")

    def create_hive_table_partition(self) -> None:
        self.create_or_update(self.get_schema_dict(hive_table_partition), "Hive Table Partition")

    def create_data_owner_relation(self) -> None:
        self.create_or_update(self.get_schema_dict(data_owner_schema), "Data Owner Relation")

    def create_application_schema(self) -> None:
        self.create_or_update(self.get_schema_dict(application_schema), "Application")

    def create_source_schema(self) -> None:
        self.create_or_update(self.get_schema_dict(source_schema), "Source")

    def create_table_source_relation(self) -> None:
        self.create_or_update(self.get_schema_dict(table_source_relation), "Table <-> Source")

    def create_lineage_schema(self) -> None:
        self.create_or_update(self.get_schema_dict(lineage_schema), "LineageProcess")

    def create_dashboard_group_schema(self) -> None:
        self.create_or_update(self.get_schema_dict(dashboard_group_schema), "Dashboard Group")

    def create_dashboard_schema(self) -> None:
        self.create_or_update(self.get_schema_dict(dashboard_schema), "Dashboard")

    def create_dashboard_chart_schema(self) -> None:
        self.create_or_update(self.get_schema_dict(dashboard_chart_schema), "Dashboard Chart")

    def create_dashboard_query_schema(self) -> None:
        self.create_or_update(self.get_schema_dict(dashboard_query_schema), "Dashboard Query")

    def create_dashboard_execution_schema(self) -> None:
        self.create_or_update(self.get_schema_dict(dashboard_execution_schema), "Dashboard Execution")

    def create_dashboard_cluster_relation(self) -> None:
        self.create_or_update(self.get_schema_dict(database_cluster_relation), "Dashboard <-> Cluster")

    def create_required_entities(self, fix_existing_data: bool = False) -> None:
        """
        IMPORTANT: The order of the entity definition matters.
        Please keep this order.
        :return: Creates or Updates the entity definition in Apache Atlas
        """
        self.create_cluster_schema()
        self.create_column_schema()
        self.create_reader_schema()
        self.create_user_schema()
        self.create_bookmark_schema()
        self.create_report_schema()
        self.create_database_schema()
        self.create_database_cluster_relation()
        self.create_schema_schema()
        self.create_schema_cluster_relation()
        self.create_table_schema()
        self.create_column_table_relation()
        self.create_table_schema_relation()
        self.create_source_schema()
        self.create_table_source_relation()
        self.create_application_schema()
        self.create_lineage_schema()
        self.assign_subtypes(regex="(.*)_table$", super_type="Table")
        self.assign_subtypes(regex="(.*)_column$", super_type="Column")
        self.create_user_reader_relation()
        self.create_reader_referenceable_relation()
        self.create_table_partition_schema()
        self.create_hive_table_partition()
        self.create_data_owner_relation()
        self.create_dashboard_group_schema()
        self.create_dashboard_schema()
        self.create_dashboard_query_schema()
        self.create_dashboard_chart_schema()
        self.create_dashboard_execution_schema()
        self.create_dashboard_cluster_relation()
