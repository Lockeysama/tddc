# -*- coding: utf-8 -*-
'''
Created on 2017年4月7日

@author: chenyitao
'''

import json
import gevent

from plugins.mq.kafka_manager.kafka_helper import KafkaHelper
from base.task.task_status_updater import TaskStatusUpdater


class TaskManagerBase(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self._task_status_updater = TaskStatusUpdater()
        self._producer = KafkaHelper.make_producer()

    def _push_task(self, topic, task):
        msg = json.dumps(task.__dict__)
        if msg:
            try:
                self._producer.send(topic, msg)
            except Exception, e:
                print('_push_task', e)
                gevent.sleep(1)
                return self._push_task(topic, task)
            else:
                return True
        return False

    def _consume_msg_exp(self, exp_type, info, exception=None):
        if 'JSON_ERR' in exp_type:
            print('*'*5+exp_type+'*'*5+
                  '\nException: '+info+'\n'+
                  exception.message+'\n'+
                  '*'*(10+len(exp_type))+'\n')
        elif 'TASK_ERR' in exp_type or 'EVENT_ERR' in exp_type:
            print('*'*5+exp_type+'*'*5+
                  '\nException: '+
                  'item={item}\n'.format(item=info)+
                  'item_type={item_type}\n'.format(item_type=type(info))+
                  '*'*(10+len(exp_type))+'\n')
