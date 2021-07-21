# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import (
    Any, Dict, Optional,
)

from amundsen_rds.models import RDSModel


def serialize_record(record: Optional[RDSModel]) -> Dict[str, Any]:
    if record is None:
        return {}

    record_dict = {key: value for key, value in vars(record).items() if key in record.__table__.columns.keys()}

    return record_dict
