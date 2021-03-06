# -*- coding: utf-8 -*-
"""
Created on 2017年4月20日

@author: chenyitao
"""

import importlib
import logging
import os

import six

from ...base.util import Singleton
from ...default_config import default_config

from ..online_config import OnlineConfig
from ..event import EventCenter, Event

log = logging.getLogger(__name__)


@six.add_metaclass(Singleton)
class ExternManager(object):
    """
    扩展模块管理
    """

    # 扩展模块更新成功回调
    update_success_callback = set()

    def __init__(self):
        EventCenter()
        log.info('Extern Modules Is Loading.')
        super(ExternManager, self).__init__()
        self._load_local_models()
        log.info('Extern Modules Was Loaded.')

    def _load_local_models(self):
        """
        从配置数据库中加载模块
        :return:
        """
        self._rules_moulds = {}
        conf = OnlineConfig().extra_modules
        if not conf:
            return False
        for attr_name, module_info in conf.__dict__.items():
            if attr_name[:2] == '__' and attr_name[-2:] == '__':
                continue
            try:
                self._load_moulds(module_info)
            except Exception as e:
                log.exception(e)
                return False
        return True

    @staticmethod
    @EventCenter.route(Event.Type.ExtraModuleUpdate)
    def _models_update_event(event):
        """
        注册到事件中心，在收到相应事件时回调
        :param event:
        :return:
        """
        if default_config.PID != os.getpid():
            return
        EventCenter().update_the_status(
            event,
            Event.Status.Executed_Success
            if ExternManager()._update(event)
            else Event.Status.Executed_Failed
        )

    def _create_package(self, path, platform):
        if not os.path.exists(path):
            os.mkdir(path)
            with open(path + '__init__.py', 'a') as _:
                log.info('Create %s Extern Modules Packages.' % platform)

    def _download_package_file(self, event_mould, path):
        """
        从管理后台提供的URL下载最新的扩展模块
        :param event_mould:
        :param path:
        :return:
        """
        path_base = '%s/%s/' % (path, event_mould.s_platform)
        self._create_package(path_base, event_mould.s_platform)
        try:
            content = event_mould.s_source
            with open(path_base + event_mould.s_package + '.py', 'w') as f:
                f.write(content)
        except Exception as e:
            log.exception(e)
            log.warning(e)
        else:
            return True
        return False

    def _update(self, event):
        log.info('Extern Modules Is Updating...')
        event_model = Event(**event.event)
        if not event_model.s_platform:
            return False
        path = os.popen('find . -name extern_modules').readlines()[0].strip()
        if not self._download_package_file(event_model, path):
            return False
        if not self._load_local_models():
            return False
        log.info('Extern Modules Was Updated.')
        for cb in self.update_success_callback:
            cb()
        return True

    def _load_moulds(self, package):
        rules_path_base = '{}.worker.extern_modules'.format(default_config.PROJECT_ROOT)
        try:
            path = '{}.{}.{}'.format(
                rules_path_base,
                package.get('s_platform'),
                package.get('s_package')
            )
            pyc_path = path.replace('.', '/') + '.pyc'
            if os.path.exists(pyc_path):
                os.remove(pyc_path)
            module = importlib.import_module(path)
            module = importlib.reload(module)
        except Exception as e:
            log.exception(e)
            return False
        if not module:
            return False
        if not self._update_models_table(
            package.get('s_platform'), package.get('s_mould'), module
        ):
            return False
        return True

    def _update_models_table(self, platform, mould, module):
        """
        刷新扩展模块字典
        :param platform:
        :param mould:
        :param module:
        :return:
        """
        cls = getattr(module, mould)
        if not cls:
            return False
        feature = getattr(cls, 'feature', None)
        if not feature:
            return False
        valid = getattr(cls, 'valid', None)
        if not int(valid):
            return False
        if not self._rules_moulds.get(platform, None):
            self._rules_moulds[platform] = {}
        self._rules_moulds[platform][feature] = cls
        return True

    def get_model(self, platform, feature=None):
        models = self._rules_moulds.get(platform)
        if not models:
            return None
        return models.get(feature) if feature else models

    def get_all_modules(self):
        return self._rules_moulds
