# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from contextlib import contextmanager
from urllib.parse import urlparse

import odoorpc

from .config import ODOO_DB, ODOO_LOGIN, ODOO_PASSWORD, ODOO_URL


@contextmanager
def login():
    url = urlparse(ODOO_URL)
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
    odoo.login(ODOO_DB, ODOO_LOGIN, ODOO_PASSWORD)
    yield odoo
