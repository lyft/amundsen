# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import os

from search_service import create_app

"""
Entry Point to Flask.
"""

config_module_class = (os.getenv('SEARCH_SVC_CONFIG_MODULE_CLASS') or
                       'search_service.config.LocalConfig')

application = create_app(config_module_class=config_module_class)

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5001)
