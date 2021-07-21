# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import abc
from typing import Dict, List, Optional

from flask import Response


class BaseMailClient(abc.ABC):
    @abc.abstractmethod
    def __init__(self, recipients: List[str]) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def send_email(self,
                   html: str,
                   subject: str,
                   optional_data: Optional[Dict] = None,
                   recipients: Optional[List[str]] = None,
                   sender: Optional[str] = None) -> Response:
        """
        Sends an email using the following parameters
        :param html: HTML email content
        :param subject: The subject of the email
        :param optional_data: An optional dictionary of any values needed for custom implementations
        :param recipients: An optional list of recipients for the email, the implementation
            for this class should determine whether to use the recipients from the function,
            the __init__ or both
        :param sender: An optional sending address associated with the email, the implementation
            should determine whether to use this value or another (e.g. from envvars)
        :return:
        """
        raise NotImplementedError  # pragma: no cover
