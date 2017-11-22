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


from .value_base import *
from .value_dialog import *
from .value_text import *
from .value_datetime import *
from .value_gps import *

import pkg_resources
import re
import jsonpath_ng

def read_rules():
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
        rules[rule_raw[0]][rule_raw[1]] = { 'type': rule_raw[2], 'path': rule_raw[3] }
    return rules

rules = None

def value_representation_factory(category,key,value = None):
    global rules
    category_const = category.get_const()
    if rules is None:
      rules = read_rules()
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
                jpath = jsonpath_ng.parse(rules[category_const][key]['path'])
                matches = jpath.find(value)
                if len(matches) == 0:
                    raise Exception("Error matching value:",str(value))
                if itype == 'int':
                    # Dialog Handling?
                    if len(matches) == 1:
                      return CMDBCategoryValueInt(matches.pop().value)
                    raise Exception("Expected one element but got multiple:",str(value))
                elif itype == 'list_int':
                    return CMDBCategoryValueListInt([ match.value for match in matches])
                elif itype == 'double':
                    if len(matches) == 1:
                        return CMDBCategoryValueDouble(matches.pop().value)
                elif itype == 'gps':
                    if len(matches) == 1:
                      return CMDBCategoryValueGPS(matches.pop().value)
                    raise Exception("Expected one element but got multiple:",str(value))
                elif itype == 'text':
                    if len(matches) == 1:
                      return CMDBCategoryValueText(matches.pop().value)
                    raise Exception("Expected one element but got multiple:",str(value))
                elif itype == 'list_text':
                    if len(matches) >= 1:
                        return [CMDBCategoryValueText(match.value) for match in matches]
                    raise Exception("Expected one element but got multiple:",str(value))
                elif itype == 'money':
                    if len(matches) == 1:
                      return CMDBCategoryValueMoney(matches.pop().value)
                    raise exception("Expected one element but got multiple:",str(value))
                elif itype == 'dialog':
                    if len(matches) == 1:
                      return CMDBCategoryValueDialog(matches.pop().value)
                    raise exception("Expected one element but got multiple:",str(value))
        return value_representation_factory_by_data_info(category.getFieldObject(key),value)

def value_representation_factory_by_data_info(field_object, value=None):
    data_type = field_object['data']['type']
    info_type = field_object['info']['type']
    try:
        if data_type == 'int':
            if info_type == 'dialog':
                return CMDBCategoryValueDialog(value)
            elif info_type == 'dialog_list':
                # List?
                return CMDBCategoryValueDialog(value)
            elif info_type == 'dialog_plus':
                return CMDBCategoryValueDialog(value)
            elif info_type == 'object_browser':
                return CMDBCategoryValueListInt(value)
            elif info_type == 'int':
                return CMDBCategoryValueInt(value)
            elif info_type == 'n2m':
                return CMDBCategoryValueBase(value)
            elif info_type == 'multiselect':
                return CMDBCategoryValueBase(value)
            else:
                raise NotImplementedError('Info type %s with data type %s is not implemented' % (info_type, data_type))
        elif data_type == 'float':
            if info_type == 'float':
                return CMDBCategoryValueBase(value)
            else:
                raise NotImplementedError('Info type %s with data type %s is not implemented' % (info_type, data_type))
        elif data_type == 'double':
            if info_type == 'double':
                return CMDBCategoryValueDouble(value)
            elif info_type == 'money':
                return CMDBCategoryValueMoney(value)
            else:
                raise NotImplementedError('Info type %s with data type %s is not implemented' % (info_type, data_type))
        elif data_type == 'text_area':
            return CMDBCategoryValueBase(value)
        elif data_type == 'text':
            if info_type == 'text':
                return CMDBCategoryValueText(value)
            elif info_type == 'multiselect':
                return CMDBCategoryValueBase(value)
            elif info_type == 'dialog':
                return CMDBCategoryValueDialog(value)
            elif info_type == 'dialog_list':
                # List?
                return CMDBCategoryValueDialog(value)
            elif info_type == 'upload':
                return CMDBCategoryValueBase(value)
            else:
                raise NotImplementedError('Info type %s with data type %s is not implemented' % (info_type, data_type))
        elif data_type == 'date_time':
            return CMDBCategoryValueDateTime(value)
        elif data_type == 'date':
            if info_type == 'date':
                return CMDBCategoryValueDate(value)
        else:
            raise NotImplementedError('Data type %s is not implement' % data_type)
    except Exception as e:
        raise Exception('Error with value of data type %s and info type %s' % (data_type, info_type), e, value)
