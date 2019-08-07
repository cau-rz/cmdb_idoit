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

class CMDBCategoryCache(dict):
    """
    A special `dict` for caching `CMDBCategory`'s.
    """

    def __init__(self):
        self.none_api_category = list()
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

    def isNoneAPICategory(self,key):
        return key in self.none_api_category

    def setNoneAPICategory(self, key):
        self.none_api_category.append(key)


cmdbCategoryCache = CMDBCategoryCache()

def is_categorie_cached(category_const):
    """
    Check if the category is cached.
    """
    return category_const in cmdbCategoryCache
