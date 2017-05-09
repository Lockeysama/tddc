# -*- coding: utf-8 -*-
'''
Created on 2017年4月12日

@author: chenyitao
'''

from conf.base_site import HBASE_HOST_PORTS
from plugins.db.hbase_manager.hbase_manager import HBaseManager


class DBManager(object):
    '''
    classdocs
    '''

    def __init__(self, tag, callback=None):
        '''
        Constructor
        '''
        self._tag = tag
        print('---->DB Manager(%s) Is Starting.' % self._tag)
        self._hbase_status = False
        self._callback =callback
        self._hbase_manager = HBaseManager(HBASE_HOST_PORTS, self._db_manager_was_ready)
        
    def _db_manager_was_ready(self):
        print('---->DB Manager(%s) Was Ready.' % self._tag)
        self._hbase_status = True
        if self._callback:
            self._callback()
    
    def hbase_instance(self):
        if self._hbase_status:
            return self._hbase_manager
        else:
            print('HBase Is Not Ready.')
            return None
        
    def put_to_hbase(self, table, row_key, items):
        if self.hbase_instance():
            try:
                return self.hbase_instance().put(table, row_key, items)
            except Exception, e:
                print('put_to_hbase', e)
            return False


def main():
    pass

if __name__ == '__main__':
    main()