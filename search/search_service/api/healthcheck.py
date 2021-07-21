# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import Tuple

from flasgger import swag_from


@swag_from('swagger_doc/healthcheck.yml')
def healthcheck() -> Tuple[str, int]:
    return '', 200
