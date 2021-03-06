# encoding: utf-8
"""
@version: ??
@author: chenyitao
@license: Apache Licence 
@software: PyCharm
@file: helper.py
@time: 2018/3/22 13:35
"""
import hashlib
import re
import logging

import time
from copy import deepcopy

import six
from flask import json
from tddc.base.util import Singleton, SnowFlakeID
from tddc.worker import Event, OnlineConfig

from ...base.redisex_for_manager import RedisExForManager

from .models import Module

log = logging.getLogger(__name__)


@six.add_metaclass(Singleton)
class ModulesHelper(object):

    key_base = 'tddc:worker:config:common:extra_modules'

    def __init__(self):
        self.event_conf = type('EventConfig', (), OnlineConfig().event.default)

    @staticmethod
    def _get_module_info(filename, file_content):
        module = Module()
        module.s_source = deepcopy(file_content)
        file_content = file_content.decode().replace(' ', '')
        module.s_package = filename.split('.')[0].split('/')[-1]
        ret = re.search(r'class(.*?)\(', file_content)
        if not ret and ret.groups():
            return None, 'Mould Not Found.(%s)' % filename
        module.s_mould = ret.groups()[0]
        ret = re.search(r"version='(.*?)'", file_content)
        if not ret or not ret.groups():
            return None, 'Version Not Found.(%s)' % filename
        module.s_version = ret.groups()[0]
        ret = re.search(r"platform='(.*?)'", file_content)
        if not ret and ret.groups():
            return None, 'Platform Not Found.(%s)' % filename
        module.s_platform = ret.groups()[0]
        ret = re.search(r"feature='(.*?)'", file_content)
        if not ret and ret.groups():
            return None, 'Feature Not Found.(%s)' % filename
        module.s_feature = ret.groups()[0]
        ret = re.search(r"valid='(.*?)'", file_content)
        valid = ret.groups()[0] if ret and ret.groups() else '1'
        module.b_valid = valid == '1'
        _md5 = hashlib.md5()
        _md5.update(module.s_source)
        module.s_file_md5 = _md5.hexdigest()
        module.i_timestamp = int(time.time())
        return module

    def edit(self, owner, filename, file_content):
        module = self._get_module_info(filename, file_content)
        module.s_owner = owner
        module_online = RedisExForManager().hgetall(
            '{}:{}:{}'.format(self.key_base, owner.lower(), module.s_feature)
        )
        if module_online:
            module_online = Module(**module_online)
            if module.s_file_md5 == module_online.s_file_md5:
                return
        RedisExForManager().hmset(
            '{}:{}:{}'.format(self.key_base, owner.lower(), module.s_feature),
            module.to_dict()
        )

    def delete(self, owner, feature):
        RedisExForManager().delete(
            '{}:{}:{}'.format(self.key_base, owner.lower(), feature)
        )

    def query(self, owner='*', feature='*'):
        if owner == '*':
            keys = RedisExForManager().keys('{}:*'.format(self.key_base))
            return [Module(**RedisExForManager().hgetall(key)) for key in keys]
        else:
            if feature == '*':
                keys = RedisExForManager().keys('{}:{}:*'.format(
                    self.key_base, owner.lower())
                )
                return [Module(**RedisExForManager().hgetall(key)) for key in keys]
            else:
                key = RedisExForManager().keys('{}:{}:{}'.format(
                    self.key_base, owner.lower(), feature)
                )
                if key:
                    key = key[0]
                return Module(**RedisExForManager().hgetall(key))

    def push(self, owner, feature):
        data = {'e_type': Event.Type.OnlineConfigFlush,
                'name': 'Config Update',
                'describe': 'Config Update Event.',
                'event': {
                    'config_type': 'extra_modules'
                },
                'id': SnowFlakeID().get_id(),
                'status': 0,
                'timestamp': int(time.time())}
        RedisExForManager().publish(
            '{}:{}'.format(self.event_conf.topic, owner.lower()),
            json.dumps(data)
        )
        module = self.query(owner, feature)
        data = {'e_type': Event.Type.ExtraModuleUpdate,
                'name': 'Modules Update',
                'describe': 'Modules(%s|%s) Update Event.' % (owner, feature),
                'event': module.to_dict(),
                'id': SnowFlakeID().get_id(),
                'status': 0,
                'timestamp': int(time.time())}
        RedisExForManager().publish(
            '{}:{}'.format(self.event_conf.topic, owner.lower()),
            json.dumps(data)
        )
