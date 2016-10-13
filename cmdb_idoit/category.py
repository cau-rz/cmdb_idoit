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

from .session import *


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


def get_category(category_const, category_id=None, category_global=False):
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
    if category_const in cmdbCategoryCache:
        return cmdbCategoryCache[category_const]
    elif category_id:
        return CMDBCategory(category_id, category_const, category_global)
    else:
        return None


def fetch_categories(categories):
    """
    Fetches a list of categories in one bulk request.
    """
    parameters = dict()
    for categorie in categories:
        parameter = dict()
        if categorie['global']:
            parameter['catgID'] = categorie['id']
        else:
            parameter['catsID'] = categorie['id']
        parameters[int(categorie['id'])] = parameter

    results = multi_requests('cmdb.category_info', parameters)
    fetched = list()
    for categorie in categories:
        if int(categorie['id']) in results:
            fetched.append(CMDBCategory(categorie['id'], categorie['const'], categorie['global'], results[int(categorie['id'])]))

    return fetched


class CMDBCategory(dict):
    """
    A model representing a CMDB category.

    Each category is a set of fields, which have a data representation
    and a information type.
    """

    def __init__(self, category_id, category_const, global_category, result=None):
        self.id = category_id
        self.const = category_const
        self.global_category = global_category
        self.fields = dict()

        parameter = dict()
        if self.global_category:
            parameter['catgID'] = self.id
        else:
            parameter['catsID'] = self.id

        if result is None:
            result = request('cmdb.category_info', parameter)

        if type(result) is dict:
            self.fields = result

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


class CMDBCategoryValuesList(list):
    """
    A model of a multi value category of an object.
    """

    deleted_items = list()

    def __init__(self, category):
        self.category = category
        self._field_up2date_state = dict()
        self.mark_updated(False)

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
    id = None

    def __init__(self, category):
        self.category = category
        self._field_up2date_state = dict()
        self.mark_updated(False)

    def _fill_category_data(self, fields):
        self.id = fields['id']
        for key in self.category.getFields():
            dict.__setitem__(self, key, fields[key])

    def __setitem__(self, index, value):
        if self.category.hasfield(index):
            # Get type, value of field
            field_type = self.category.get_field_data_type(index)
            field_value = None
            if index in self:
                self._field_up2date_state[index] = self[index] == value
                field_value = dict.__getitem__(self, index)
            else:
                self._field_up2date_state[index] = False
            # rough field Type/handling detection
            if field_type == 'int':
                if type(field_value) is list:
                    # TODO We need to encapsulate values in an extra type ....
                    #      to get a better guess
                    pass
                else:
                    if not isinstance(field_value, dict):
                        field_value = dict()
                    field_value['value'] = value
                    value = field_value
            elif field_type == 'text':
                if not isinstance(field_value, dict):
                    field_value = dict()
                field_value['ref_title'] = value
                value = field_value
            dict.__setitem__(self, index, value)
        else:
            raise KeyError("Category " + self.category.const + " has no field " + index)

    def __getitem__(self, index):
        field_type = self.category.get_field_data_type(index)
        field_value = dict.__getitem__(self, index)
        if not field_value:
            return None
        if field_type == 'int':
            if type(field_value) is list:
                if len(field_value) == 0:
                    field_value = None
                else:
                    field_value = [val['id'] for val in field_value]
            elif 'value' in field_value:
                field_value = field_value['value']
        elif field_type == 'text':
            if type(field_value) is dict:
                field_value = field_value['ref_title']
        return field_value

    def items(self):
        keys = dict.keys(self)
        return [(key, self[key]) for key in keys]

    def values(self):
        keys = dict.keys(self)
        return [self[key] for key in keys]

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
