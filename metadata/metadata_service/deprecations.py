# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import warnings

from flask import Flask

warnings.simplefilter('always', DeprecationWarning)


# Deprecation Warnings
def process_deprecations(app: Flask) -> None:
    if app.config.get("POPULAR_TABLE_MINIMUM_READER_COUNT", None) is not None:
        app.config["POPULAR_RESOURCES_MINIMUM_READER_COUNT"] = app.config["POPULAR_TABLE_MINIMUM_READER_COUNT"]
        warnings.warn("'POPULAR_TABLE_MINIMUM_READER_COUNT' variable is deprecated since version (3.6.0),"
                      "and will be removed in version 4."
                      "Please use 'POPULAR_TABLE_MINIMUM_READER_COUNT' instead", DeprecationWarning)


def print_deprecation_warning(message: str) -> None:
    warnings.warn(message, DeprecationWarning)
