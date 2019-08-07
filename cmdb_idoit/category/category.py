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

from enum import Enum
import logging

from cmdb_idoit.session import request, requests
from cmdb_idoit.exceptions import CMDBNoneAPICategory, CMDBMissingTypeInformation, CMDBConversionException
from cmdb_idoit.category.value_factory import type_determination, value_representation_factory, type_repr

def getCategoryValueObject(category,multi_value):
    if multi_value:
        return CMDBCategoryValuesList(category)
    else:
        return CMDBCategoryValues(category)

class CMDBCategoryType(Enum):
    """
    An enum for the kind of categories.
    """
    type_global = 1   #: Global category kind, this kind can be part of several object types.
    type_specific = 2 #: Specific category kind, this kind of categories may be special to few or only one object types.
    type_custom = 3   #: Custom category kind, this kind of categories are user defined and may be unique to a idoit instance.


class CMDBCategory(dict):
    """
    A model representing a CMDB category.

    Each category is a set of fields, which have a data representation
    and a information type.
    """
    

    def __init__(self, category_id, category_const, category_type, result=None):
        self.id = int(category_id)
        self.const = category_const
        self.category_type = category_type
        self.custom_category = False
        self.fields = dict()
        self.field_type = dict()

        parameter = dict()
        if self.is_global_category():
            parameter['catgID'] = self.id
        elif self.is_specific_category():
            parameter['catsID'] = self.id
        else:
            parameter['category'] = self.const

        if result is None:
            result = request('cmdb.category_info', parameter)

        if type(result) is dict:
            self.fields = result

        # Determine types for all fields
        for key in list(self.getFields()):
            try:
                self.field_type[key] = type_determination(self, key)
            except CMDBMissingTypeInformation as e:
                logging.exception(e)
                logging.warning(f"Ignore field { key } in category { self.get_const() }")
                del self.fields[key]

    def get_id(self):
        """
        Get the numerical identifier of a category.
        """
        return self.id

    def get_const(self):
        """
        Get the category constant of a category.
        """
        return self.const

    def hasField(self, index):
        """
        Check if a category has a given field.
        """
        return index in self.fields

    def getFields(self):
        """
        Return the list of fields of a category.
        """
        return self.fields.keys()

    def getFieldType(self, index):
        return self.field_type[index]

    def getFieldTypes(self):
        return self.field_type


    def getFieldObject(self,index):
        """
        Return the description for the given field as retrieved from the cmdb.
        """
        return self.fields[index]

    def getField(self, index):
        return self.fields[index]['data']['field']

    def get_field_data_type(self, index):
        """
        Return the data type of a field.
        """
        return self.fields[index]['data']['type']

    def get_field_info_type(self, index):
        """
        Return the information type of a field.
        """
        return self.fields[index]['info']['type']

    def getFieldType(self, index):
        """
        Return the type for a field, determinated by `cmdb_idoit.category.type_determination`.
        """
        return type_determination(self, index)

    def is_global_category(self):
        """
        Check if this category is of global kind.
        """
        return self.category_type == CMDBCategoryType.type_global

    def is_specific_category(self):
        """
        Check if this category is of specific kind.
        """
        return self.category_type == CMDBCategoryType.type_specific

    def is_custom_category(self):
        """
        Check if this category is of custom kind.
        """
        return self.category_type == CMDBCategoryType.type_custom



class CMDBCategoryValuesList(list):
    """
    A model of a multi value category of an object.
    """

    def __init__(self, category):
        self.category = category
        self.deleted_items = list()

    def __setitem__(self, index, value):
        cat_value = self._dict_to_catval(value)
        list.__setitem__(self, index, cat_value)

    def __delitem__(self, index):
        if isinstance(index, slice):
            for x in sorted(range(0, len(self))[index], reverse=True):
                del self[x]
        else:
            item = list.__getitem__(self, index)
            if isinstance(item, CMDBCategoryValues) and item.id:
                logging.debug("Add %s[%s] to deleted items" % (self.category.const,item.id))
                self.deleted_items.append(item)
            list.__delitem__(self, index)

    def remove(self, item):
        """
        Remove category instanciation from list.
        """
        if isinstance(item, CMDBCategoryValues) and item.id:
            logging.debug("Add %s[%s] to deleted items" % (self.category.const,item.id))
            self.deleted_items.append(item)
        list.remove(self,item)

    def append(self, value):
        """
        Append an instanciation to the list.
        """
        cat_value = self._dict_to_catval(value)
        list.append(self, cat_value)

    def _dict_to_catval(self, value):
        if isinstance(value, CMDBCategoryValues):
            return value
        elif isinstance(value, dict):
            cat_value = CMDBCategoryValues(self.category)

            for k, v in value.items():
                cat_value[k] = v

            return cat_value
        else:
            raise TypeError("CMDBCategoryValuesList works only with dict or CMDBCategoryValues, but not with %s" % type(value))

    def markChanged(self, state=True):
        """
        Change the update marker for all fields in all instanciations of the category.
        """
        for value in self:
            value.markChanged(state)

    def hasChanged(self):
        """
        Check if any of the instanciations of the category has a field which is marked updated.
        """
        for value in self:
            if value.hasChanged():
                return True
        return False


class CMDBCategoryValues(dict):
    """
    A model of category data of an object.
    """

    def __init__(self, category):
        self.id = None
        self.category = category
        self.field_type = category.getFieldTypes()
        self.field_data = dict()
        """
        Store the update/change state for each field in the values set of a category.
        The value for a field is True when an update/change to that field had been applied
        and a write to the database is required.
        """
        self._change_state = dict()
        self.markUnchanged()


    def _fill_category_data(self, fields):
        self.id = fields['id']
        for key in self.category.getFields():
            try:
                if key in fields:
                    if self.category.hasField(key):
                        value = value_representation_factory(self.category, key, fields[key])
                        dict.__setitem__(self, key, value)
            except ConversionException as e:
                logging.fatal(textwrap.dedent("""\
                              There was a fatal error while deriving a representativ value for %(category)s.%(attribute)s.
                              According to the API the type of this attribute is '%(type)s', but it was not possible to 
                              derive this type from the received data:
 
                              %(data)s

                              Either we do something ugly wrong or a mapping for this attribute is needed.
                              For more information consult the mitigation chapter in the documentation.""" 
                              % { 'category': self.category.const, 'attribute': key, 'data': repr(fields[key]),'type': type_repr(self.field_type[key])}))
                raise Exception(e)

        # Since this method should only be callend on a loading process, remark all fields to be unchanged 
        self.markUnchanged()

    def __setitem__(self, index, value):
        if self.category.hasField(index):
            try:
              type_check(self.field_type[index],value)
            except Exception as e:
                logging.error("Type check of index %s has failed" % index)
                raise e
            if dict.__contains__(self,index):
               old_value = dict.__getitem__(self,index)
            else:
               old_value = None
            if old_value != value:
                self.markFieldChanged(index)
                dict.__setitem__(self, index, value)
        else:
            raise KeyError("Category " + self.category.const + " has no field " + index)

    def __getitem__(self, index):
        try:
            return dict.__getitem__(self, index)
        except KeyError as e:
            if self.category.hasField(index):
                return None
            else:
                raise e

    def items(self):
        keys = dict.keys(self)
        return [(key, self[key]) for key in keys]

    def values(self):
        return [value.store() for key, value in dict.items(self)]

    def update(self, other_dict):
        for key, val in other_dict.items():
            self[key] = val

    def markFieldChanged(self,key):
        self._change_state[key] = True

    def markFieldUnchanged(self,key):
        self._change_state[key] = False

    def hasFieldChanged(self, key):
        return self._change_state[key]

    def markFieldsChanged(self):
        """
        Marks all fields of this CategoryValue to be changed.
        Hence a save operation would save them all.
        """
        for field in self.category.getFields():
            self.markFieldChanged(field)
            
    def markUnchanged(self):
        """
        Marks all fields of this CategoryValue to be unchanged.
        Hence a save operation wouldn't save any.
        """
        for field in self.category.getFields():
            self.markFieldUnchanged(field)

    def hasChanged(self):
        for field in self.category.getFields():
            if self.hasFieldChanged(field):
                return True
        return False

