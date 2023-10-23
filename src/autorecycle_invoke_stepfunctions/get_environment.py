#!/usr/bin/env python
import logging
import os
from typing import Union

logger = logging.getLogger(__name__)


def get_current_environment() -> Union[str, None]:
    environment: Union[str, None] = os.getenv("ENVIRONMENT")
    return environment
