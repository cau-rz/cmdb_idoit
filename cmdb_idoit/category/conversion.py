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

import datetime
import logging

def conver_list(func,values):
    if values is None:
        return []
    elif isinstance(values,list):
        return [ func(value) for value in values ]
    else:
        raise Exception("Expected value of type list, but instead it has type %s '%s'" % (type(values),repr(values)))

def conver_integer(value):
    if value is None:
        return None
    elif isinstance(value,int):
        return value
    elif isinstance(value,str):
        try:
          return int(value)
        except ValueError:
            raise Exception("Can't convert %s to integer" % value,e)
    elif isinstance(value,int):
        return value
    else:
        raise Exception("Conversion of none string to integer is not supported '%s'" % repr(value))

def conver_string(value):
    if value is None:
        return None
    elif isinstance(value,str):
        return value
    else:
        raise Exception("Value is not of type string, but instead of type %s '%s'" % (type(value),repr(value)))

def conver_float(value):
    if value is None:
        return None
    elif isinstance(value,float):
        return value
    elif isinstance(value,int):
        return float(value)
    elif isinstance(value,str):
        try:
            #locale.setlocale( locale.LC_ALL, 'en_US.UTF-8') 
            return float(value)
        except Exception as e:
            logging.warning("Can't covert %s to float" % value,e)
    else:
        raise Exception("Conversion of none string/int to float is not supported '%s'" % repr(value))

def conver_money(value):
    if value is None:
        return None
    elif isinstance(value,float):
        return value
    elif isinstance(value,str):
        try:
            #locale.setlocale( locale.LC_ALL, 'en_US.UTF-8') 
            money_value = value.split(' ')[0]
            money_value.replace(",","")
            if len(money_value) == 0:
                return float(0)
            else:
                return float(money_value)
        except Exception as e:
            logging.warning("Can't covert %s to float/money" % value,e)
    else:
        raise Exception("Conversion of none string to float/money is not supported '%s'" % repr(value))

def conver_datetime(value):
    if value is None:
        return None
    elif isinstance(value,str):
        try:
            newvalue = str(value).split(' - ')[0]
            return datetime.datetime.strptime(newvalue, "%Y-%m-%d %H:%M:%S")
        except:
            return datetime.datetime.strptime(value, "%Y-%m-%d - %H:%M")
    else:
        raise Exception("Conversion of none string to datetime is not supported '%s'" % repr(value))

def conver_date(value):
    if value is None:
        return None
    elif isinstance(value,str):
        # Example: 2017-07-18
        try:
            value = str(value).split(' ')[0]
            return datetime.datetime.strptime(value, "%Y-%m-%d")
        except Exception as e:
            logging.warning(e)
    else:
        raise Exception("Conversion of none string to datetime is not supported '%s'" % repr(value))

def conver_dialog(value):
    return conver_integer(value)

def conver_gps(value):
    if value is None:
        return None
    elif isinstance(value,dict):
        latitude = value['latitude']
        longitude = value['longitude']
        return {'latitude': self.latitude, 'longitude': self.longitude }
    else:
        raise Exception("Value is not of type dict, but instead of type %s '%s'" % (type(value),repr(value)))
