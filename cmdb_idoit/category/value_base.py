"""
    This file is part of cmdb_idoit.

    cmdb_idoit is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    cmdb_idoit is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with cmdb_idoit.  If not, see <http://www.gnu.org/licenses/>.
"""

import logging
import locale


class CMDBCategoryValueBase:
    """
    Encapsulate and transform between the python working
    representation of an field value and the storage representation
    of idoit
    """

    value = None

    def __init__(self, value=None):
        self.value = value

    def set(self, value):
        """
        Set the value in the representation of a value.
        """
        self.value = value

    def get(self):
        """
        Return the working value for an representation of a value.
        """
        return self.value

    def store(self):
        """
        Return the storage representation of a value.
        """
        return self.value

    def __repr__(self):
        return repr(self.value)


class CMDBCategoryValueInt(CMDBCategoryValueBase):

    def __init__(self,value=None):
        if value is not None:
            try:
               self.value = int(value)
            except ValueError:
                raise Exception("Can't guess the index of a dict to get the right integer: %s",str(value))


class CMDBCategoryValueListInt(CMDBCategoryValueBase):

    def __init__(self,value=None):
        self.value = list()
        if value is not None:
            if isinstance(value,list):
                if len(value) == 0:
                    value = None
                elif len(value) >= 1:
                    for val in value:
                        self.value.append(CMDBCategoryValueInt(val))
            else:
                self.value.append(CMDBCategoryValueInt(value))

class CMDBCategoryValueDouble(CMDBCategoryValueBase):
    
    def __init__(self, value = None):
        if value is None:
            self.value = None
        else:
            try:
               #locale.setlocale( locale.LC_ALL, 'en_US.UTF-8') 
               self.value = float(value)
            except Exception as e:
                logging.warning("Float %s can't be parsed" % value)
                raise e

class CMDBCategoryValueMoney(CMDBCategoryValueBase):
    def __init__(self, value = None):
        if value is None or len(value.strip()) == 0:
            self.value = None
        else:
            try:
                money_value = value.split(' ')[0]
                if len(money_value) == 0:
                    self.value = 0
                else:
                    locale.setlocale( locale.LC_ALL, 'en_US.UTF-8')
                    self.value = locale.atof(money_value)
            except Exception as e:
                raise Exception("String '%s' is not parseable" % value,e)

