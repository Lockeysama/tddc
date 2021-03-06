# -*- coding: utf-8 -*-
'''
Created on 2017年5月5日

@author: chenyitao
'''

import json
import time
import datetime
from collections import defaultdict


class Singleton(type):
    """
    单例metaclass
    """

    def __init__(cls, name, bases, dict):
        super(Singleton, cls).__init__(name, bases, dict)
        cls._instance = defaultdict()

    def __call__(cls, *args, **kw):
        tag = kw.get('tag') or 'default'
        if cls._instance.get(tag) is None:
            cls._instance[tag] = super(Singleton, cls).__call__(*args, **kw)
        return cls._instance[tag]


def object2json(obj):
    info = {k: v for k, v in obj.__dict__.items()
            if v is not None
            and '__' not in k}
    return json.dumps(info)


def timer(func):
    '''
    执行时间计算装饰器
    '''
    def _deco(*args, **kwargs):
        start = time.time()
        func(*args, **kwargs)
        end = time.time()
        print(end-start)
    return _deco


def count_time(func):
    def int_time(*args, **kwargs):
        start_time = datetime.datetime.now()
        ret = func(*args, **kwargs)
        over_time = datetime.datetime.now()
        total_time = (over_time-start_time).total_seconds()
        print(func, total_time)
        return ret
    return int_time
