# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import os
from amundsen_application import create_app


if not os.getenv('FRONTEND_SVC_CONFIG_MODULE_CLASS'):
    os.environ['FRONTEND_SVC_CONFIG_MODULE_CLASS'] = 'amundsen_application.config.TestConfig'

application = create_app()

if __name__ == '__main__':
    application.run(host='0.0.0.0')
