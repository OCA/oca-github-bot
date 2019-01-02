# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from contextlib import contextmanager
from urllib.parse import urlparse

import odoorpc

from . import config


@contextmanager
def login():
    url = urlparse(config.ODOO_URL)
    if url.scheme == "https":
        protocol = "jsonrpc+ssl"
    elif url.scheme == "http":
        protocol = "jsonrpc"
    if ":" in url.netloc:
        host, port = url.netloc.split(":")
        port = int(port)
    else:
        host = url.netloc
        if url.scheme == "https":
            port = 443
        elif url.scheme == "http":
            port = 80

    odoo = odoorpc.ODOO(host, protocol=protocol, port=port)
    odoo.login(config.ODOO_DB, config.ODOO_LOGIN, config.ODOO_PASSWORD)
    yield odoo
