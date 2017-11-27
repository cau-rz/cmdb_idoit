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

from .conversion import *

import pkg_resources
import re
import jsonpath_ng
import datetime

rules = None

def _get_rules():
    global rules
    if rules != None:
        return rules

    resource_package = __name__  # Could be any module/package name
    resource_path = '/'.join(('map', '1_9_4.map'))  # Do not use os.path.join(), see below

    template = pkg_resources.resource_string(resource_package, resource_path)
    rules = dict()
    for line in template.decode('utf-8').splitlines():
        rule_raw = re.split('[ \t]+',line)
        if len(rule_raw) < 4:
            raise Exception("None conformal rule: %s" % line)
        if rule_raw[0] not in rules:
            rules[rule_raw[0]] = dict()
        jpath = jsonpath_ng.parse(rule_raw[3]) 
        rules[rule_raw[0]][rule_raw[1]] = { 
                'type': rule_raw[2], 
                'path': rule_raw[3],
                'jpath': jpath
                }
    return rules

def type_determination(category,key):

    rules = _get_rules()
    category_const = category.get_const()
    # Do we have an overwrite for this category,key combination
    if category_const in rules:
        if key in rules[category_const]:
            type_string = rules[category_const][key]['type']
            if type_string == 'int':
                return int
            elif type_string == 'list_int':
                return (list,int)
            elif type_string == 'text':
                return str 
            elif type_string == 'list_text':
                return (list,str)
            elif type_string == 'double':
                return float
            elif type_string == 'list_double':
                return (list,float)

    # otherwise guess the type
    data_type = category.getFieldObject(key)['data']['type']
    info_type = category.getFieldObject(key)['info']['type']

    base_type = None
    if data_type == 'int':
        base_type = int
    elif data_type == 'float':
        base_type = float
    elif data_type == 'double':
        base_type = float
    elif data_type == 'text':
        base_type = str
    elif data_type == 'text_area':
        base_type = str
    elif data_type == 'date':
        base_type = datetime.datetime
    elif data_type == 'date_time':
        base_type = datetime.datetime
    else:
        raise Exception('Unknown data_type %s' % data_type)

    if info_type == 'dialog_list':
        return (list,base_type)
    elif info_type == 'object_browser':
        return (list,base_type)
    elif info_type == 'multiselect':
        return (list,basetype)

    return base_type

def type_check(type_desc,value):
    if isinstance(type_desc,tuple):
        if not isinstance(value,type_desc[0]):
            raise Exception("type check error '%s' is not a %s" % (value,type(type_desc[0])))
        else:
            for element in value:
                if not isinstance(element,type_desc[1]):
                    raise Exception("type check error the inner elements of '%s' are not of type %s" % (value,type(type_desc[1])))
    elif not isinstance(value,type_desc):
        raise Exception("type check error '%s' are not of type %s" % (value,type(type_desc)))
    return True


def value_representation_factory(category,key,value = None):
    rules = _get_rules()
    category_const = category.get_const()
    data_type = category.getFieldObject(key)['data']['type']
    info_type = category.getFieldObject(key)['info']['type']
    if value == False:
        value = None
    if isinstance(value,list) and len(value) == 0:
        value = None
    if isinstance(value,list) and isinstance(value[0],list) and len(value[0]) == 0:
        value = None
    if value is not None:
        if category_const in rules:
            if key in rules[category_const]:
                itype = rules[category_const][key]['type']
                jpath = rules[category_const][key]['jpath']
                matches = jpath.find(value)
                if len(matches) == 0:
                    raise Exception("Error matching value,",rules[category_const][key]['path'],str(value))
                if itype == 'int':
                    # Dialog Handling?
                    if len(matches) == 1:
                      return conver_integer(matches.pop().value)
                    raise Exception("Expected one element but got multiple:",str(value))
                elif itype == 'list_int':
                    return conver_list(conver_integer,[match.value for match in matches])
                elif itype == 'double':
                    if len(matches) == 1:
                        return conver_float(matches.pop().value)
                elif itype == 'gps':
                    if len(matches) == 1:
                      return conver_gps(matches.pop().value)
                    raise Exception("Expected one element but got multiple:",str(value))
                elif itype == 'text':
                    if len(matches) == 1:
                      return conver_string(matches.pop().value)
                    raise Exception("Expected one element but got multiple:",str(value))
                elif itype == 'list_text':
                    if len(matches) >= 1:
                        return conver_list(conver_string,[match.value for match in matches])
                    raise Exception("Expected one element but got multiple:",str(value))
                elif itype == 'money':
                    if len(matches) == 1:
                      return conver_money(matches.pop().value)
                    raise exception("Expected one element but got multiple:",str(value))
                elif itype == 'dialog':
                    if len(matches) == 1:
                      return conver_dialog(matches.pop().value)
                    raise exception("Expected one element but got multiple:",str(value))
    return value_representation_factory_by_data_info(category.getFieldObject(key),value)

def value_representation_factory_by_data_info(field_object, value=None):
    data_type = field_object['data']['type']
    info_type = field_object['info']['type']

    if data_type == 'int':
        conver_func = conver_integer
    elif data_type == 'float':
        conver_func = conver_float 
    elif data_type == 'double':
        if info_type == 'money':
            conver_func = conver_money
        else:
            conver_func = conver_float
    elif data_type == 'text':
        conver_func = conver_string
    elif data_type == 'text_area':
        conver_func = conver_string
    elif data_type == 'date':
        conver_func = conver_date
    elif data_type == 'date_time':
        conver_func = conver_datetime
    else:
        raise Exception('Unknown data_type %s',data_type)

    if info_type == 'dialog_list':
        return conver_list(conver_func,value)
    elif info_type == 'object_browser':
        return conver_list(conver_func,value)
    elif info_type == 'multiselect':
        return conver_list(conver_func,value)
    else:
        return conver_func(value)
