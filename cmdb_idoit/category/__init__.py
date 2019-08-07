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

import textwrap

from cmdb_idoit.session import *
from cmdb_idoit.category.value_factory import *

from cmdb_idoit.category.cache import cmdbCategoryCache, is_categorie_cached
from cmdb_idoit.category.category import CMDBCategory, CMDBCategoryType

def get_category(category_const, category_id=None, category_type=CMDBCategoryType.type_specific):
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
    elif cmdbCategoryCache.isNoneAPICategory(category_const):
        raise CMDBNoneAPICategory(f"Category { category_const } cannot be handled by API, cached result!")
    elif category_id:
        return CMDBCategory(category_id, category_const, category_type)
    else:
        return CMDBCategory(None,category_const,CMDBCategoryType.type_custom)


def is_categorie_cached(category_const):
    """
    Check if the category is cached.
    """
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
            key = str(categorie['id'])
            if categorie['global'] == CMDBCategoryType.type_custom:
                key = 'c' + str(categorie['id'])
            parameters[key] = parameter

    results = dict()
    if len(parameters) > 0:
        results = multi_requests('cmdb.category_info', parameters)

    fetched = list()
    for categorie in categories:
        key = str(categorie['id'])
        if categorie['global'] == CMDBCategoryType.type_custom:
            key = 'c' + str(categorie['id'])
        if key in results:
            category_object = CMDBCategory(categorie['id'], categorie['const'], categorie['global'], results[key])
            fetched.append(category_object)
        elif is_categorie_cached(categorie['const']):
                fetched.append(get_category(categorie['const']))

    return fetched

