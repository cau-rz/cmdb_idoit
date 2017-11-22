from .value_base import CMDBCategoryValueBase

import datetime
import time


class CMDBCategoryValueDateTime(CMDBCategoryValueBase):

    def __init__(self, value=None):
        if value is None or len(value) == 0:
            self.value = None
        else:
            # Example: 2017-07-18 14:10:03 - 14:10
            try:
              newvalue = str(value).split(' - ')[0]
              self.value = datetime.datetime.strptime(newvalue, "%Y-%m-%d %H:%M:%S")
            except:
              self.value = datetime.datetime.strptime(value, "%Y-%m-%d - %H:%M")

class CMDBCategoryValueDate(CMDBCategoryValueBase):

    def __init__(self, value=None):
        if value is None or len(value) == 0 or value == '-':
            self.value = None
        else:
            # Example: 2017-07-18
            value = str(value).split(' ')[0]
            self.value = datetime.datetime.strptime(value, "%Y-%m-%d")
