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

        result = request('cmdb.objects', parameter)
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
            self.id = int(object_data['id'])
            self.sys_id = object_data['sysid']
            self.title = object_data['title']
            self.status = object_data['status']
            self.type = int(object_data['type'])
        else:
            self.type = object_data

        # Fetch type information
        self.type_object = get_cmdb_type(self.type)
        self.fields = self.type_object.getObjectStructure()
        self._reset_fetch_state()

        if fetch_all:
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
        return category_const in self.fields.keys()

    def getTypeCategories(self):
        """
        Return the list of categories definied for this object.

        :rtype: list
        """
        return self.fields.keys()

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
        if isinstance(self.fields[category_const],CMDBCategoryValuesList):
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
        for category_fields in self.fields.values():
            if isinstance(category_fields,CMDBCategoryValuesList):
                for field in category_fields:
                    field.mark_updated()
            else:
                category_fields.mark_updated()

    def hasUpdates(self):
        if not self.is_up2date:
            return True
        for category_const,field in self.fields.items():
            if field.has_updates():
                return True
        return False

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

        def _category_save_parameters(category,field):
            category_const = category.get_const()
            method = None
            parameter_data = dict()
            for key, value in field.items():
                logging.debug("%s[%s](%s)=%s" % (category_const, key, category.get_field_data_type(key), str(value)))
                if field.has_value_been_updated(key):
                    parameter_data[key] = value
            if field.id is not None:
                method = "cmdb.category.save"
                parameter_data['id'] = field.id
            else:
                method = "cmdb.category.create"

            return (method,parameter_data)

        for category_const,category_fields in self.fields.items():
            category = category_fields.category

            # Skip the logbook category, we do not manipulate this category ever.
            if category_const == 'C__CATG__LOGBOOK':
                logging.debug("Skipping C__CATG__LOGBOOK")
                continue

            # Skip the category iff we are not creating a new object and the category
            # was not fetched, and hence no change had been applied
            if not is_create and not self._is_category_data_fetched(category_const):
                continue

            parameter_template = dict()
            parameter_template['objID'] = self.id
            parameter_template['category'] = category_const

            if isinstance(category_fields,CMDBCategoryValuesList):
                # Process changed entries
                for field in category_fields:
                    if field.has_updates():
                        # Receive changeset and processing method and queue the request
                        (method,data) = _category_save_parameters(category,field)
                        parameter = parameter_template.copy()
                        parameter['data'] = data
                        requests[len(requests)] = {'method': method, 'parameter': parameter}
                        # Update the field update state. This should happen after processing the requests
                        field.mark_updated()
                # Process removed entries
                for field in category_fields.deleted_items:
                    if field.id is not None:
                        parameter = parameter_template.copy()
                        logging.debug("Delete %s[%s]" % (category_const, str(field.id)))
                        method = "cmdb.category.delete"
                        parameter['id'] = field.id
                        requests[len(requests)] = {'method': "cmdb.category.delete", 'parameter': parameter}
            elif category_fields.has_updates():
                # Receive changeset and processing method and queue the request
                (method,data) = _category_save_parameters(category,category_fields)
                parameter = parameter_template.copy()
                parameter['data'] = data
                requests[len(requests)] = {'method': method, 'parameter': parameter}
                # Update the field update state. This should happen after processing the requests
                category_fields.mark_updated()
            else:
                logging.debug("Category %s of Object %s has no updates skipping" % (category_const, self.id))

        multi_method_request(requests)
