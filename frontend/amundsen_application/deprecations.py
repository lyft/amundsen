# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import os
import warnings

from flask import Flask

warnings.simplefilter('always', DeprecationWarning)


# Deprecation Warnings
def process_deprecations(app: Flask) -> None:
    if os.getenv('APP_WRAPPER') or os.getenv('APP_WRAPPER_CLASS'):
        warnings.warn("'APP_WRAPPER' and 'APP_WRAPPER_CLASS' variables are deprecated since version (3.9.0), "
                      "and will be removed in version 4. "
                      "Please use 'FLASK_APP_MODULE_NAME' and 'FLASK_APP_CLASS_NAME' instead",
                      DeprecationWarning)

    if os.getenv('APP_WRAPPER_ARGS'):
        warnings.warn("'APP_WRAPPER_ARGS' variable is deprecated since version (3.9.0), "
                      "and will be removed in version 4. "
                      "Please use 'FLASK_APP_KWARGS_DICT' instead", DeprecationWarning)

    if app.config.get("POPULAR_TABLE_COUNT", None) is not None:
        app.config["POPULAR_RESOURCES_COUNT"] = app.config["POPULAR_TABLE_COUNT"]
        warnings.warn("'POPULAR_TABLE_COUNT' variable is deprecated since version (3.9.0), "
                      "and will be removed in version 4. "
                      "Please use 'POPULAR_RESOURCES_COUNT' instead", DeprecationWarning)

    if app.config.get("POPULAR_TABLE_PERSONALIZATION", None) is not None:
        app.config["POPULAR_RESOURCES_PERSONALIZATION"] = app.config["POPULAR_TABLE_PERSONALIZATION"]
        warnings.warn("'POPULAR_TABLE_PERSONALIZATION' variable is deprecated since version (3.9.0), "
                      "and will be removed in version 4. "
                      "Please use 'POPULAR_RESOURCES_PERSONALIZATION' instead", DeprecationWarning)
