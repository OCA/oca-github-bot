# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from ..queue import task, getLogger

_logger = getLogger(__name__)


@task()
def heartbeat():
    _logger.info("heartbeat")
