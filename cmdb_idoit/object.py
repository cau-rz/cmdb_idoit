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
from .category import *
from .type import *

import collections.abc


class CMDBObjects(list):
    """
    A list of CMDB objects, which is automagically loading all objects given by the filter.
    By default no filters are applied resulting this to be the list of all objects in the cmdb.

    :ivar dict filters: Given filter for this object list.
    """

    def __init__(self, filters=None, limit=0):
        """
        :param dict filters: Definition of the objects list filter.
        :param int limit: Number of objects which should be loaded.
        """
        if filters is None:
            self.filters = dict()
        else:
            self.filters = filters

        parameter = {'filter': self.filters}
        if limit != 0:
            parameter['limit'] = limit

        result = request('cmdb.objects', {'filter': self.filters})
        for raw_object in result:
            cmdb_object = CMDBObject(raw_object)
            self.append(cmdb_object)

    def find_object_by_id(self, id):
        """
        Search and return an object by id.
        Return None if none is found.
        """
        if isinstance(id, str):
            id = int(id)
        for obj in self:
            if obj.id == id:
                return obj
        return None

    def find_object_by_title(self, title):
        """
        Search and return an object by title.
        Return None if none is found.
        """
        for obj in self:
            if obj.title == title:
                return obj
        return None

    def find_object_by_field(self, category_const, key, value):
        """
        Find an object by category field. This function will not always work
        for multi_value categories.
        """

        for cmdb_object in self:
            multi_value = get_cmdb_type(cmdb_object.type).get_category_inclusion(category_const).multi_value
            if multi_value:
                for entry in cmdb_object[category_const]:
                    if entry[key] == value:
                        return cmdb_object
            else:
                if cmdb_object[category_const][key] == value:
                    return cmdb_object
        return None

    def findObjectsByFunction(self, function):
        """
        Find all object for that `function` is true,
        return that list. Returns an empty list if no object is found.
        """
        return list(filter(function, self))

    def load_category_data(self, category_const):
        logging.info("Deprication Warning: You should use loadCategoryData")
        self.loadCategoryData(category_const)

    def loadCategoryData(self, category_const, reload=False):
        """
        Fetch category data for all contained objects.
        """
        parameters = dict()
        for obj in self:
            # Check if the category data has already been fetched on the object
            # TODO Provide an method which encapsulates the internal data structure
            if obj.hasTypeCategory(category_const):
                if not obj.field_data_fetched[category_const] or reload:
                    parameters[obj.id] = {'objID': obj.id, 'category': category_const}
        if len(parameters) == 0:
            logging.warning("Loading category data '%s' on set result in no action" % category_const)
        result = multi_requests('cmdb.category', parameters)

        for obj in self:
            if obj.id in result:
                obj._fill_category_data(category_const, result[obj.id])

    def loadAllCategoryData(self):
        """
        Fetch data for all categories for all contained objects.
        """
        parameters = dict()
        for obj in self:
            categories = obj.getTypeCategories()
            for category_const in categories:
                parstr = "%s--%s" % (category_const, obj.id)
                parameters["%s--%s" % (category_const, obj.id)] = {'objID': obj.id, 'category': category_const}
        result = multi_requests('cmdb.category', parameters)

        for obj in self:
            categories = obj.getTypeCategories()
            for category_const in categories:
                parstr = "%s--%s" % (category_const, obj.id)
                if parstr in result:
                    obj._fill_category_data(category_const, result[parstr])


def loadObject(ident):
    """
    Load object by ``ident``.
    """
    objects = CMDBObjects({'ids': [ident]})
    if len(objects) == 0:
        return None
    else:
        return objects.pop()


class CMDBObject(collections.abc.Mapping):
    """
    An cmdb object. Is basically a dictionary of the categories which
    are defined in its object type.

    :var int id: The numerical ident for this object.
    :var str sys_id: The cmdb internal system identifier
    :var str title: The title of the object.
    :var int type_id: The numerical type ident for this object.
    :var bool is_up2date: Has this object been changed.
    """

    def __init__(self, object_data, fetch_all=False):

        # Attributes of an object
        self.id = None
        self.sys_id = None
        self.title = None
        self.type = None
        self.is_up2date = False

        # Fields contains the structure of the object rebuild with CMDBCategoryValues and CMDBCategoryValuesList Objects
        self.fields = None
        self.field_data_fetched = dict()

        # Handle object data
        if isinstance(object_data, collections.abc.Mapping):
            self.id = int(data['id'])
            self.sys_id = data['sysid']
            self.title = data['title']
            self.status = data['status']
            self.type = data['type']
        else:
            self.type = object_data

        # Fetch type information
        self.type_object = get_cmdb_type(self.type)
        self.fields = self.type_object.getObjectStructure()
        self._reset_fetch_state()

        if fetchall:
            self.loadAllCategoryData()

    def _reset_fetch_state(self):
        for category_const in self.getTypeCategories():
            self.field_data_fetched[category_const] = False

    def loadAllCategoryData(self):
        """
        Fetch all avilable categories for this object.
        """

        # If this object is unsaved, we are not able to receive anything but an error, so skip.
        if self.id is None:
            return

        categories = self.getTypeCategories()
        parameters = dict()
        for category_const in categories:
            parameters[category_const] = {'objID': self.id, 'category': category_const}
        result = multi_requests('cmdb.category', parameters)
        for category_const in result:
            if len(result[category_const]) > 0:
                self._fill_category_data(category_const, result[category_const])

    def _is_category_data_fetched(self, category_const):
        return self.field_data_fetched[category_const]

    def loadCategoryData(self, category_const, reload=False):
        """
        Fetch the category data for the given category.

        :param category_const: The category constant for the to load category.
        :raise Exception: if the given category does not exist in the object type declaration.
        """

        # If this object is unsaved, we are not able to receive anything but an error, so skip.
        if self.id is None:
            return

        if category_const not in self.fields:
            raise Exception('Object has no category %s in his type %s' % (category_const, self.type_object.const))
        category_object = get_category(category_const)

        # Check if the category data has already been fetched
        if self.field_data_fetched[category_const] and not reload:
            return

        result = request('cmdb.category', {'objID': self.id, 'category': category_const})
        self._fill_category_data(category_const, result, category_object)

    def _fill_category_data(self, category_const, result, category_object=None):
        if category_const not in self.fields:
            raise Exception('Object has no category %s in his type %s' % (category_const, self.type_object.const))
        if not category_object:
            category_object = get_category(category_const)

        multi_value = get_cmdb_type(self.type).get_category_inclusion(category_const).multi_value

        if multi_value:
            for fields in result:
                entry = CMDBCategoryValues(category_object)
                entry._fill_category_data(fields)
                self.fields[category_const].append(entry)
        else:
            for fields in result:
                self.fields[category_const]._fill_category_data(fields)

        self.is_up2date = True
        self.field_data_fetched[category_const] = True

    def hasTypeCategory(self, category_const):
        return category_const in self.type_object.getCategories()

    def getTypeCategories(self):
        """
        Return the list of categories definied for this object.

        :rtype: list
        """
        return self.type_object.getCategories()

    def __setattr__(self, name, value):
        if name != "is_up2date":
            try:
                if self.__getattribute__(name) != value:
                    self.is_up2date = False
            except AttributeError:
                self.is_up2date = False
        super(CMDBObject, self).__setattr__(name, value)

    def __repr__(self):
        return repr({'id': self.id, 'type': self.type, 'title': self.title, 'values': self.fields})

    def __getitem__(self, key):
        # TODO: Fetch categorie data only at access time
        if not self._is_category_data_fetched(key) and self.id is not None:
            self.loadCategoryData(key)
        return self.fields[key]

    def __delitem__(self, category_const):
        multi_value = get_cmdb_type(self.type).get_category_inclusion(category_const).multi_value
        if multi_value:
            for i in range(1, len(self.fields[category_const])):
                del self.fields[category_const]
        else:
            raise NotImplementedError()

    def __len__(self):
        return len(self.fields)

    def __iter__(self):
        return self.fields.__iter__()

    def markUpdated(self):
        """
        Mark all fields in all loaded Categories as updated.
        So we when save is called we will rewrite all data.
        """
        for category_const in self.getTypeCategories():
            object_type = get_cmdb_type(self.type)
            multi_value = object_type.get_category_inclusion(category_const).multi_value
            if multi_value:
                for field in self.fields[category_const]:
                    field.mark_updated()
            else:
                self.fields[category_const].mark_updated()

    def save(self):
        """
        Save the object in the database. This will automagically create the object
        if it does not exists, yet.

        During the save only the required fields of the required categories are transmitted to the cmdb.
        If nothing has changed, no request will be queued.
        """

        is_create = self.id is None

        parameter = dict()
        method = "cmdb.object.create"
        if not is_create:
            method = "cmdb.object.update"
            parameter['id'] = self.id
        parameter['type'] = self.type
        parameter['title'] = self.title

        if not self.is_up2date:
            result = request(method, parameter)
            self.is_up2date = True

        if is_create:
            self.id = result['id']

        requests = dict()

        for category_const in self.getTypeCategories():
            if category_const == 'C__CATG__LOGBOOK':
                logging.info("Skip C__CATG__LOGBOOK")
                continue
            category = get_category(category_const)
            pm_tpl = dict()
            pm_tpl['objID'] = self.id
            pm_tpl['category'] = category_const

            object_type = get_cmdb_type(self.type)

            multi_value = object_type.get_category_inclusion(category_const).multi_value

            # Skip this category iff we are not creating and field is not fetched
            if not is_create and not self._is_category_data_fetched(category_const):
                continue

            if multi_value:
                for field in self.fields[category_const]:
                    if field.has_updates():
                        parameter = pm_tpl.copy()
                        parameter['data'] = dict()
                        logging.debug("%s" % (category_const))
                        for key, value in field.items():
                            logging.debug("%s[%s](%s)=%s" % (category_const, key, category.get_field_data_type(key), str(value)))
                            if field.has_value_been_updated(key):
                                parameter['data'][key] = value
                        if field.id is not None:
                            method = "cmdb.category.update"
                            parameter['data']['id'] = field.id
                        else:
                            method = "cmdb.category.create"
                        requests[len(requests)] = {'method': method, 'parameter': parameter}
                        field.mark_updated()
                    else:
                        logging.debug("Category %s/%s of Object %s has no updates skipping" % (category_const, field.id, self.id))
                for field in self.fields[category_const].deleted_items:
                    if field.id:
                        parameter = pm_tpl.copy()
                        logging.debug("Delete %s[%s]" % (category_const, str(field.id)))
                        method = "cmdb.category.delete"
                        parameter['id'] = field.id
                        requests[len(requests)] = {'method': "cmdb.category.delete", 'parameter': parameter}
            elif self.fields[category_const].has_updates():
                parameter = pm_tpl.copy()
                parameter['data'] = dict()
                parameter['data']['id'] = self.fields[category_const].id
                for key, value in self.fields[category_const].items():
                    if self.fields[category_const].has_value_been_updated(key):
                        logging.debug("%s[%s](%s)=%s" % (category_const, key, category.get_field_data_type(key), str(value)))
                        parameter['data'][key] = value
                if parameter['data']['id']:
                    method = "cmdb.category.update"
                else:
                    method = "cmdb.category.create"
                requests[len(requests)] = {'method': method, 'parameter': parameter}
                self.fields[category_const].mark_updated(False)
            else:
                logging.debug("Category %s of Object %s has no updates skipping" % (category_const, self.id))

        multi_method_request(requests)
