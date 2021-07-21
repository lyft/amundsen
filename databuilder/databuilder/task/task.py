# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Iterator

from pyhocon import ConfigTree

from databuilder import Scoped
from databuilder.extractor.base_extractor import Extractor
from databuilder.loader.base_loader import Loader
from databuilder.task.base_task import Task
from databuilder.transformer.base_transformer import NoopTransformer, Transformer
from databuilder.utils.closer import Closer

LOGGER = logging.getLogger(__name__)


class DefaultTask(Task):
    """
    A default task expecting to extract, transform and load.

    """

    # Determines the frequency of the log on task progress
    PROGRESS_REPORT_FREQUENCY = 'progress_report_frequency'

    def __init__(self,
                 extractor: Extractor,
                 loader: Loader,
                 transformer: Transformer = NoopTransformer()) -> None:
        self.extractor = extractor
        self.transformer = transformer
        self.loader = loader

        self._closer = Closer()
        self._closer.register(self.extractor.close)
        self._closer.register(self.transformer.close)
        self._closer.register(self.loader.close)

    def init(self, conf: ConfigTree) -> None:
        self._progress_report_frequency = \
            conf.get_int(f'{self.get_scope()}.{DefaultTask.PROGRESS_REPORT_FREQUENCY}', 500)

        self.extractor.init(Scoped.get_scoped_conf(conf, self.extractor.get_scope()))
        self.transformer.init(Scoped.get_scoped_conf(conf, self.transformer.get_scope()))
        self.loader.init(Scoped.get_scoped_conf(conf, self.loader.get_scope()))

    def run(self) -> None:
        """
        Runs a task
        """
        LOGGER.info('Running a task')
        try:
            record = self.extractor.extract()
            count = 0
            while record:
                record = self.transformer.transform(record)
                if not record:
                    # Move on if the transformer filtered the record out
                    record = self.extractor.extract()
                    continue

                # Support transformers which return one record, or yield multiple
                results = record if isinstance(record, Iterator) else [record]
                for result in results:
                    if result:
                        self.loader.load(result)
                        count += 1

                if count > 0 and count % self._progress_report_frequency == 0:
                    LOGGER.info(f'Extracted {count} records so far')

                # Prepare the next record
                record = self.extractor.extract()
            LOGGER.info(f'Total extracted records: {count}')
        finally:
            self._closer.close()
