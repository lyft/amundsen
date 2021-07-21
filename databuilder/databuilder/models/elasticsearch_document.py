# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
from abc import ABCMeta


class ElasticsearchDocument:
    """
    Base class for ElasticsearchDocument
    Each different resource ESDoc will be a subclass
    """
    __metaclass__ = ABCMeta

    def to_json(self) -> str:
        """
        Convert object to json
        :return:
        """
        obj_dict = {k: v for k, v in sorted(self.__dict__.items())}
        data = json.dumps(obj_dict) + "\n"
        return data
