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

from cmdb_idoit.exceptions import CMDBMissingTypeInformation
from cmdb_idoit.session import request

import pkg_resources
import re
import jsonpath_ng
import datetime
import textwrap

rules = None

def _get_rules():
    global rules
    if rules != None:
        return rules

    # request i-doit version
    result = request("idoit.version",{})
    if 'version' not in result:
        raise Exception("Can't determine idoit version")
    version = result['version'].split('.')

    resource_package = __name__  # Could be any module/package name
    resource_path = '/'.join(('map', f"{version[0]}_{version[1]}.map"))  # Do not use os.path.join(), see below

    template = pkg_resources.resource_string(resource_package, resource_path)
    rules = dict()
    for line in template.decode('utf-8').splitlines():
        rule_raw = re.split('[ \t]+',line)
        if len(rule_raw) < 4:
            raise Exception("None conformal rule: %s" % line)
        if rule_raw[0] not in rules:
            rules[rule_raw[0]] = dict()
        #jpath = jsonpath_ng.parse(rule_raw[3]) 
        rules[rule_raw[0]][rule_raw[1]] = { 
                'type': rule_raw[2], 
                'path': rule_raw[3],
                'jpath': None
                }
    return rules

def _apply_rule(rule,value):
    if rule['jpath'] is None:
        rule['jpath'] = jsonpath_ng.parse(rule['path']) 
    return rule['jpath'].find(value)

class AttributeType:

    def __init__(self,primary,conversion_function,is_list=None,rule=None):
        self.primary = primary
        self.conversion_function = conversion_function
        self.is_list = is_list
        self.rule = rule

    def __call__(self,value):
        if self.is_list:
            return conver_list(self.conversion_function,value)
        else:
            return self.conversion_function(value)

    def check(self,value):
        if self.isList():
            if not isinstance(value,list):
                raise Exception("type check error '%s' is not a %s" % (value,type(self.encapsulate)))
            else:
                for element in value:
                    if not isinstance(element,self.primary):
                        raise Exception("type check error the inner elements of '%s' is of type and not of type %s" % (value,type(element),type(self.primary)))
        elif not isinstance(value,self.primary):
            raise Exception("type check error '%s' is of type %s and not of type %s" % (value,type(value),repr(self.primary)))
        return True
        
    def isList(self):
        return self.is_list

    def hasRule(self):
        return self.rule is not None

    def getPrimaryType(self):
        return self.primary

    def __repr__(self):
        if self.isList():
            return "list of %s" % self.primary.__name__
        else:
            return self.primary.__name__


def get_type_mapping(category_const,field_name):
    """
    Get the type mapping for given category and field.
    
    :param str category_const: category constant
    :param str field: Name of a field of given category

    :rtype: str or None
    """
    rules = _get_rules()
    if category_const in rules:
        if field_name in rules[category_const]:
            return rules[category_const][field_name]['path']
    return None


def type_determination(category,key):

    rules = _get_rules()
    category_const = category.get_const()
    # Do we have an overwrite for this category,key combination
    if category_const in rules:
        if key in rules[category_const]:
            rule = rules[category_const][key]
            type_string = rule['type']
            if type_string == 'int':
                return AttributeType(int,conver_integer,rule=rule)
            elif type_string == 'list_int':
                return AttributeType(int,conver_integer,True,rule=rule)
            elif type_string == 'text':
                return AttributeType(str,conver_string,rule=rule)
            elif type_string == 'list_text':
                return AttributeType(str,conver_string,True,rule=rule)
            elif type_string == 'double':
                return AttributeType(float,conver_float,rule=rule)
            elif type_string == 'list_double':
                return AttributeType(float,conver_float,True,rule=rule)
            elif type_string == 'gps':
                return AttributeType(dict,conver_gps,rule=rule)
            elif type_string == 'dialog':
                return AttributeType(int,conver_dialog,rule=rule)
            elif type_string == 'money':
                return AttributeType(float,conver_money,rule=rule)

    # otherwise guess the type
    try:
        data_type = category.getFieldObject(key)['data']['type']
        info_type = category.getFieldObject(key)['info']['type']
    except Exception as e:
        raise CMDBMissingTypeInformation(f"Missing type informations for { key } in { category.get_const() }",e)

    base_type = None
    conv_func = lambda x:x 
    if data_type == 'int':
        base_type = int
        conv_func = conver_integer 
    elif data_type == 'float':
        base_type = float
        conv_func = conver_float
    elif data_type == 'double':
        base_type = float
        if info_type == 'money':
            conv_func = conver_money
        else:
            conv_func = conver_float
    elif data_type == 'text':
        base_type = str
        conv_func = conver_string
    elif data_type == 'text_area':
        base_type = str
        conv_func = conver_string
    elif data_type == 'date':
        base_type = datetime.datetime
        conv_func = conver_date
    elif data_type == 'date_time':
        base_type = datetime.datetime
        conv_func = conver_datetime
    else:
        raise Exception('Unknown data_type %s' % data_type)

    if info_type in ['dialog_list','object_browser','multiselect']:
        return AttributeType(base_type,conv_func,True)

    return AttributeType(base_type,conv_func,False)


def value_representation_factory(category,key,value = None):
    category_const = category.get_const()
    attr_type = category.getFieldType(key)
    # Weird empty values check
    if value == False:
        value = None
    if isinstance(value,list):
        if len(value) == 0:
            value = None
        elif len(value) == 1 and isinstance(value[0],list) and len(value[0]) == 0:
            value = None
    if attr_type.hasRule() and value is not None:
            matches = _apply_rule(attr_type.rule,value)
            if len(matches) == 0:
                field_object = category.getFieldObject(key)
                if not 'type' in field_object['data']:
                    data_type = "<not defined>"
                else:
                    data_type = field_object['data']['type']

                logging.fatal(textwrap.dedent(f"""\
                        There was a fatal error applying a representation mapping for {category_const}.{key}.
                        According to the API the type of this attribute is "{data_type}" the mapping suggested
                        a JSON path of "{ attr_type.rule['path'] }", this path doesn't match on:

                          { value }

                        Either the api result has been changed and hence the mapping didn't work any more,
                        or we do something utterly wrong.
                        """))
                raise Exception("Error matching value,",rules[category_const][key]['path'],str(value))
            match_values = [match.value for match in matches]
            if attr_type.isList():
                return attr_type(match_values)
            elif len(match_values) == 1:
                    return attr_type(match_values.pop())
            else:
                raise Exception("Expected one element but got multiple:",str(value))
    else:
        # Handle other values
        return attr_type(value)
