# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
from talos.core import config
from artifacts_corepy.db import resource

from artifacts_corepy.common import exceptions

CONF = config.CONF
LOG = logging.getLogger(__name__)


class DiffConfTemplate(resource.DiffConfTemplate):
    def _addtional_create(self, session, data, created):
        if 'roles' in data:
            for perm_role in data['roles']:
                resource.DiffConfTemplateRole(transaction=session).create({
                    'diff_conf_template_id': created['id'],
                    'role': perm_role['role'],
                    'permission': perm_role['permission']
                })
