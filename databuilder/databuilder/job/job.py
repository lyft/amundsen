# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging

from pyhocon import ConfigTree
from statsd import StatsClient

from databuilder import Scoped
from databuilder.job.base_job import Job
from databuilder.publisher.base_publisher import NoopPublisher, Publisher
from databuilder.task.base_task import Task

LOGGER = logging.getLogger(__name__)


class DefaultJob(Job):
    # Config keys
    IS_STATSD_ENABLED = 'is_statsd_enabled'
    JOB_IDENTIFIER = 'identifier'

    """
    Default job that expects a task, and optional publisher
    If configured job will emit success/fail metric counter through statsd where prefix will be
    amundsen.databuilder.job.[identifier] .
    Note that job.identifier is part of metrics prefix and choose unique & readable identifier for the job.

    To configure statsd itself, use environment variable: https://statsd.readthedocs.io/en/v3.2.1/configure.html
    """

    def __init__(self,
                 conf: ConfigTree,
                 task: Task,
                 publisher: Publisher = NoopPublisher()) -> None:
        self.task = task
        self.conf = conf
        self.publisher = publisher
        self.scoped_conf = Scoped.get_scoped_conf(self.conf,
                                                  self.get_scope())
        if self.scoped_conf.get_bool(DefaultJob.IS_STATSD_ENABLED, False):
            prefix = f'amundsen.databuilder.job.{self.scoped_conf.get_string(DefaultJob.JOB_IDENTIFIER)}'
            LOGGER.info('Setting statsd for job metrics with prefix: %s', prefix)
            self.statsd = StatsClient(prefix=prefix)
        else:
            self.statsd = None

    def init(self, conf: ConfigTree) -> None:
        pass

    def _init(self) -> None:
        self.task.init(self.conf)

    def launch(self) -> None:
        """
        Launch a job by initializing job, run task and publish.
        :return:
        """

        logging.info('Launching a job')
        #  Using nested try finally to make sure task get closed as soon as possible as well as to guarantee all the
        #  closeable get closed.
        try:
            is_success = True
            self._init()
            try:
                self.task.run()
            finally:
                self.task.close()

            self.publisher.init(Scoped.get_scoped_conf(self.conf, self.publisher.get_scope()))
            Job.closer.register(self.publisher.close)
            self.publisher.publish()

        except Exception as e:
            is_success = False
            raise e
        finally:
            # TODO: If more metrics are needed on different construct, such as task, consider abstracting this out
            if self.statsd:
                if is_success:
                    LOGGER.info('Publishing job metrics for success')
                    self.statsd.incr('success')
                else:
                    LOGGER.info('Publishing job metrics for failure')
                    self.statsd.incr('fail')

            Job.closer.close()

        logging.info('Job completed')
