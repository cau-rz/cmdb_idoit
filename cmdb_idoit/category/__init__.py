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

from cmdb_idoit.session import *
from cmdb_idoit.category.value_factory import *


class CMDBCategoryCache(dict):
    """
    A special `dict` for caching `CMDBCategory`'s.
    """

    def __init__(self):
        self.type_to_category = dict()

    def __setitem__(self, key, value):
        if not type(value) is CMDBCategory:
            raise TypeError("Object is not of type CMDBCategory")
        if key in self.type_to_category:
            dict.__setitem__(self, self.type_to_category[key], value)
        else:
            self.type_to_category[value.id] = value.const
            dict.__setitem__(self, key, value)

    def __getitem__(self, key):
        if key in self.type_to_category:
            return dict.__getitem__(self, self.type_to_category[key])
        else:
            return dict.__getitem__(self, key)

cmdbCategoryCache = CMDBCategoryCache()


class CMDBCategoryType(Enum):
    """
    A enumeration of the types of categories.
    """
    type_global = 1
    type_specific = 2
    type_custom = 3 


def get_category(category_const, category_id=None, category_global=CMDBCategoryType.type_specific):
    """
    Returns a `CMDBCategory` object iff a identifiable object is in `CMDBCategoryCache`.
    A object is identifiable if category_const is either the constant for that `CMDBCategory`
    or its id.

    When category_const and caregory_id are given then an new `CMDBCategory` will be instanciated
    given those values. For this to work category_const must be the constant matching the
    ident for the required `CMDBCategory`.

    The `CMDBCategory` will add itself to the `CMDBCategoryCache`, after successful retrieving
    it's values.

    Should there be no cached `CMDBCategory` and category_id is not given then the result is None.
    """
    if is_categorie_cached(category_const):
        return cmdbCategoryCache[category_const]
    elif category_id:
        return CMDBCategory(category_id, category_const, category_global)
    else:
        return None


def is_categorie_cached(category_const):
    return category_const in cmdbCategoryCache


def fetch_categories(categories):
    """
    Fetches a list of categories in one bulk request.
    Returns a list of requested categories.
    """
    parameters = dict()
    for categorie in categories:
        parameter = dict()
        if categorie['global'] == CMDBCategoryType.type_global:
            parameter['catgID'] = categorie['id']
        elif categorie['global'] == CMDBCategoryType.type_specific:
            parameter['catsID'] = categorie['id']
        else:
            parameter['category'] = categorie['const'];
        if not is_categorie_cached(categorie['const']):
            parameters[int(categorie['id'])] = parameter

    if len(parameters) > 0:
        results = multi_requests('cmdb.category_info', parameters)
    else:
        results = dict()

    fetched = list()
    for categorie in categories:
        if int(categorie['id']) in results:
            fetched.append(CMDBCategory(categorie['id'], categorie['const'], categorie['global'], results[int(categorie['id'])]))
        elif is_categorie_cached(categorie['const']):
            fetched.append(get_category(categorie['const']))

    return fetched

class CMDBCategory(dict):
    """
    A model representing a CMDB category.

    Each category is a set of fields, which have a data representation
    and a information type.
    """
    

    def __init__(self, category_id, category_const, category_type, result=None):
        self.id = category_id
        self.const = category_const
        self.category_type = category_type
        self.custom_category = False
        self.fields = dict()

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

        if not is_categorie_cached(self.const):
            logging.info('Caching category %s' % self.const)
            cmdbCategoryCache[self.const] = self

    def get_id(self):
        return self.id

    def get_const(self):
        return self.const

    def hasfield(self, index):
        return index in self.fields

    def getFields(self):
        return self.fields.keys()

    def getfield(self, index):
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

    def is_global_category(self):
        return self.category_type == CMDBCategoryType.type_global

    def is_specific_category(self):
        return self.category_type == CMDBCategoryType.type_specific

    def is_custom_category(self):
        return self.category_type == CMDBCategoryType.type_custom



class CMDBCategoryValuesList(list):
    """
    A model of a multi value category of an object.
    """


    def __init__(self, category):
        self.category = category
        self._field_up2date_state = dict()
        self.mark_updated(False)
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

    def append(self, value):
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

    def mark_updated(self, state=True):
        pass

    def has_updates(self):
        state = False
        for value in self:
            state = state or value.has_updates()
        return state


class CMDBCategoryValues(dict):
    """
    A model of category data of an object.
    """

    def __init__(self, category):
        self.id = None
        self.category = category
        self._field_up2date_state = dict()
        self.mark_updated(False)

    def _fill_category_data(self, fields):
        self.id = fields['id']
        for key in self.category.getFields():
            data_type = self.category.get_field_data_type(key)
            info_type = self.category.get_field_info_type(key)
            try:
                field_representation = value_representation_factory(data_type, info_type, fields[key])
                dict.__setitem__(self, key, field_representation)
            except Exception as e:
                raise Exception('Failed to create representation value for field %s in category %s' % (key, self.category.const), e)

    def __setitem__(self, index, value):
        if self.category.hasfield(index):
            # Get type, value of field
            field_representation = None
            if index in self:
                self._field_up2date_state[index] = self[index] == value
                field_representation = dict.__getitem__(self, index)
            else:
                self._field_up2date_state[index] = False
                data_type = self.category.get_field_data_type(index)
                info_type = self.category.get_field_info_type(index)
                field_representation = value_representation_factory(data_type, info_type)

            field_representation.set(value)
            dict.__setitem__(self, index, field_representation)
        else:
            raise KeyError("Category " + self.category.const + " has no field " + index)

    def __getitem__(self, index):
        field_data_type = self.category.get_field_data_type(index)
        field_info_type = self.category.get_field_info_type(index)
        if index in self:
          field_representation = dict.__getitem__(self, index)
          return field_representation.get()
        else:
            return None

    def items(self):
        keys = dict.keys(self)
        return [(key, self[key]) for key in keys]

    def values(self):
        return [value.store() for key, value in dict.items(self)]

    def update(self, other_dict):
        for key, val in other_dict.items():
            self[key] = val

    def mark_updated(self, state=True):
        """
        Marks all fields of this category instance as up to date.
        Hence when saved only manipulated and mandatory fields have to be commited
        or if no field at all is manipulated no commit at all is needed.

        With the argument `state` this can also be used to mark all fields as not up
        to date.
        """
        for field in self.category.getFields():
            self._field_up2date_state[field] = state

    def has_value_been_updated(self, key):
        return not self._field_up2date_state[key]

    def has_updates(self):
        state = True
        for field in self.category.getFields():
            state = state and self._field_up2date_state[field]
        return not state
