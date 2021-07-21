# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import abc

from pyhocon import ConfigFactory, ConfigTree


class Scoped(object, metaclass=abc.ABCMeta):
    _EMPTY_CONFIG = ConfigFactory.from_dict({})
    """
    An interface for class that works with scoped (nested) config.
    https://github.com/chimpler/pyhocon
    A scoped instance will use config within its scope. This is a way to
    distribute configuration to its implementation instead of having it in
    one central place.
    This is very useful for DataBuilder as it has different components
    (extractor, transformer, loader, publisher) and its component itself
    could have different implementation.
    For example these can be a configuration for two different extractors
     "extractor.mysql.url" for MySQLExtractor
     "extractor.filesystem.source_path" for FileSystemExtractor

     For MySQLExtractor, if you defined scope as "extractor.mysql", scoped
     config will basically reduce it to the config that is only for MySQL.
     config.get("extractor.mysql") provides you all the config within
     'extractor.mysql'. By removing outer context from the config,
     MySQLExtractor is highly reusable.
    """

    @abc.abstractmethod
    def init(self, conf: ConfigTree) -> None:
        """
        All scoped instance is expected to be lazily initialized. Means that
        __init__ should not have any heavy operation such as service call.
        The reason behind is that Databuilder is a code at the same time,
        code itself is used as a configuration. For example, you can
        instantiate scoped instance with all the parameters already set,
        ready to run, and actual execution will be executing init() and
        execute.

        :param conf: Typesafe config instance
        :return: None
        """
        pass

    @abc.abstractmethod
    def get_scope(self) -> str:
        """
        A scope for the config. Typesafe config supports nested config.
        Scope, string, is used to basically peel off nested config
        :return:
        """
        return ''

    def close(self) -> None:
        """
        Anything that needs to be cleaned up after the use of the instance.
        :return: None
        """
        pass

    @classmethod
    def get_scoped_conf(cls, conf: ConfigTree, scope: str) -> ConfigTree:
        """
        Convenient method to provide scoped method.

        :param conf: Type safe config instance
        :param scope: scope string
        :return: Type safe config instance
        """
        if not scope:
            return Scoped._EMPTY_CONFIG

        return conf.get(scope, Scoped._EMPTY_CONFIG)
