# -*- coding: utf-8 -*-
"""
@author  : chenyitao
@email   : yt.chen@bshier.com
@license: Apache Licence
@software: PyCharm
@file    : process.py
@time    : 2018/9/11 11:24
"""
import setproctitle
import time
from os import getpid

import gevent.monkey
import logging

import gevent
import six

from . import logging_ext

from ..base.util import Device, Singleton
from ..default_config import default_config

from .authorization import Authorization
from .online_config import OnlineConfig
from .monitor import Monitor
from .redisex import RedisEx
from .extern_modules import ExternManager

log = logging.getLogger(__name__)


@six.add_metaclass(Singleton)
class Worker(object):

    def __init__(self):
        super(Worker, self).__init__()
        setproctitle.setproctitle(
            'TDDC-{}-{}'.format(default_config.PLATFORM, default_config.FEATURE)
        )
        logging_ext.patch()
        log.info('{} Is Start.'.format(default_config.PLATFORM))
        Authorization()
        if not Authorization().logged:
            return
        OnlineConfig()
        if OnlineConfig().first:
            return
        Monitor()
        ExternManager()
        self._start_plugins()
        gevent.spawn(self._heart)
        gevent.sleep()

    @staticmethod
    def _heart():
        while True:
            if default_config.PID != getpid():
                return
            try:
                RedisEx().hset(
                    'tddc:worker:monitor:health:{}'.format(default_config.PLATFORM.lower()),
                    '{}|{}'.format(
                        Device.mac(), default_config.FEATURE
                    ),
                    time.time()
                )
            except Exception:
                pass
            gevent.sleep(15)

    @classmethod
    def start(cls):
        cls()
        log.info('{} Is Running.'.format(default_config.PLATFORM))
        while Authorization().logged and not OnlineConfig().first:
            gevent.sleep(10)
        if not Authorization().logged:
            log.error('Process Exit(Authorization Failed).')
        elif OnlineConfig().first:
            log.error('Process Exit(Online Config Must Be Edit).')

    def _start_plugins(self):
        for plugin_cls, args, kwargs in self.plugins():
            if not plugin_cls:
                continue
            if not args and not kwargs:
                plugin_cls()
            elif args and not kwargs:
                plugin_cls(*args)
            elif not args and kwargs:
                plugin_cls(**kwargs)
            else:
                plugin_cls(*args, **kwargs)

    def plugins(self):
        raise NotImplementedError
