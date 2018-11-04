# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import os

MANIFEST_NAMES = ("__manifest__.py", "__openerp__.py", "__terp__.py")


def is_addons_dir(addons_dir):
    """ Test if an directory contains Odoo addons. """
    if not os.path.isdir(addons_dir):
        return False
    for p in os.listdir(addons_dir):
        addon_dir = os.path.join(addons_dir, p)
        if not os.path.isdir(addon_dir):
            continue
        for manifest_name in MANIFEST_NAMES:
            if os.path.exists(os.path.join(addon_dir, manifest_name)):
                return True
    return False
