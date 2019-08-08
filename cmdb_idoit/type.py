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
from .exceptions import CMDBUnkownType, CMDBNoneAPICategory

from cmdb_idoit.category import get_category, fetch_categories
from cmdb_idoit.category.category import CMDBCategoryType, getCategoryValueObject

import collections.abc

class CMDBTypeCache(collections.abc.MutableMapping):

    def __init__(self):
        self.const_to_type = dict()
        self.map = dict()

    def __setitem__(self, key, value):
        if not type(value) is CMDBType:
            raise TypeError("Object is not of type CMDBType")
        if key in self.const_to_type:
            self.map[self.const_to_type[key]] = value
        else:
            self.const_to_type[value.get_const()] = value.get_id()
            self.map[key] = value

    def __getitem__(self, key):
        if key in self.const_to_type:
            return self.map[self.const_to_type[key]]
        else:
            return self.map[key]

    def __delitem__(self, key):
        """
        We assume cached types to be inherent.
        """
        raise NotImplemented("You shall not delete items from type cache")

    def __contains__(self, key):
        if key in self.const_to_type:
            return self.const_to_type[key] in self.map
        else:
            return key in self.map 

    def __iter__(self):
        return self.map.__iter__();
    
    def __len__(self):
        return len(self.map);



cmdbTypeCache = CMDBTypeCache()


def get_cmdb_type(type_id):
    if type_id in cmdbTypeCache:
        return cmdbTypeCache[type_id]
    else:
        return CMDBType(type_id)


def get_type_id_from_const(type_const):
    """
    Returns the type constant for an given type id.
    """
    cmdb_type = get_cmdb_type(type_const)
    return cmdb_type.get_id()


def get_type_const_from_id(type_id):
    """
    Returns the type id for an given type const.
    """
    cmdb_type = get_cmdb_type(type_id)
    return cmdb_type.get_const()


class CMDBType(dict):

    class CMDBTypeCategoryInclusion:
        multi_value = None
        source_table = None
        parent = None
        category = None

    def __init__(self, type_id):
        self.id = None
        self.const = None
        self.status = 0
        self.title = None
        self.meta = dict()
        self.global_categories = dict()
        self.specific_categories = dict()
        self.custom_categories= dict()

        self._load(type_id)
        cmdbTypeCache[self.get_id()] = self

    def get_id(self):
        return self.id

    def get_const(self):
        return self.const

    def get_type_group():
        return self.meta['type_group']

    def _load(self, type_id):

        result = request('cmdb.object_types', {'filter': {'id': type_id}})

        if len(result) == 0:
            raise CMDBUnkownType(f"Unkown type { type_id }")
            return

        result = result.pop()

        self.id = int(result['id'])
        self.const = result['const']
        self.titlte = result['title']
        self.status = result['status']
        self.meta['type_group'] = result['type_group']
        self.meta['type_group_title'] = result['type_group_title']
        self.meta['tree_group'] = result['tree_group']

        logging.debug("Loading type %s" % self.get_const())

        result = request('cmdb.object_type_categories', {'type': self.get_id()})

        # process structural information about categories
        categories = list()
        if 'catg' in result:
            categories += [(CMDBCategoryType.type_global, c) for c in result['catg']]

        if 'cats' in result:
            categories += [(CMDBCategoryType.type_specific, c) for c in result['cats']]

        if 'custom' in result:
            categories += [(CMDBCategoryType.type_custom, c) for c in result['custom']]

        categories_parameter = list()
        for category_type, category in categories:
            categories_parameter.append({'id': category['id'], 'const': category['const'], 'global': category_type})
        logging.debug("Fetch categories for type %s" % self.const)
        fetch_categories(categories_parameter)

        for glob, cat in categories:
            logging.debug("Loading category %s" % cat['const'])
            category_type_inclusion = self.CMDBTypeCategoryInclusion()
            if 'parent' in cat:
                category_type_inclusion.parent = cat['parent']
            category_type_inclusion.multi_value = cat['multi_value'] == "1"
            category_type_inclusion.source_table = cat['source_table']
            
            try:
                category_object = get_category(category_const=cat['const'], category_id=cat['id'], category_type=glob)
                category_type_inclusion.category = category_object
                if category_object.is_global_category():
                    self.global_categories[category_object.get_const()] = category_type_inclusion
                elif category_object.is_specific_category():
                    self.specific_categories[category_object.get_const()] = category_type_inclusion
                else:
                    self.custom_categories[category_object.get_const()] = category_type_inclusion
            except CMDBNoneAPICategory as e:
                pass

    def get_category_inclusion(self, category_const):
        if category_const in self.global_categories:
            return self.global_categories[category_const]
        elif category_const in self.specific_categories:
            return self.specific_categories[category_const]
        else:
            return self.custom_categories[category_const]

    def getCategories(self):
        return list(self.global_categories.keys()) + list(self.specific_categories.keys()) + list(self.custom_categories.keys())

    def getObjectStructure(self):
        """
        Initialize the structure of a type. So every category is prepared as a CMDBCategoryValues
        Object, except for those multie value categories.
        """
        values = dict()

        for category_object in  self.global_categories.values():
            values[category_object.category.get_const()] = getCategoryValueObject(category_object.category,category_object.multi_value)

        for category_object in  self.specific_categories.values():
            values[category_object.category.get_const()] = getCategoryValueObject(category_object.category,category_object.multi_value)

        for category_object in  self.custom_categories.values():
            values[category_object.category.get_const()] = getCategoryValueObject(category_object.category,category_object.multi_value)

        return values
