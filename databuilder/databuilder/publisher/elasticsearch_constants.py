# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from amundsen_common.models.index_map import (
    DASHBOARD_ELASTICSEARCH_INDEX_MAPPING as DASHBOARD_INDEX_MAP, TABLE_INDEX_MAP, USER_INDEX_MAP,
)

# Please use constants in amundsen_common.models.index_map directly. This file is only here
# for backwards compatibility.
TABLE_ELASTICSEARCH_INDEX_MAPPING = TABLE_INDEX_MAP
DASHBOARD_ELASTICSEARCH_INDEX_MAPPING = DASHBOARD_INDEX_MAP
USER_ELASTICSEARCH_INDEX_MAPPING = USER_INDEX_MAP
