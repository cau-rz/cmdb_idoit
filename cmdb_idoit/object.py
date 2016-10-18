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


class CMDBObjects(list):
    """
    A list of objects.

    By default no filters are applied resulting this to be the list of all object in the cmdb.
    """
    filters = dict()

    def __init__(self, filters=dict()):
        self.filters = filters

        result = request('cmdb.objects', {'filter': self.filters})
        for raw_object in result:
            cmdb_object = CMDBObject(raw_object['type'])
            cmdb_object.fill(raw_object)
            self.append(cmdb_object)

    def find_object_by_id(self, id):
        for obj in self:
            if obj.id == id:
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

    def load_category_data(self, category_const):
        parameters = dict()
        for obj in self:
            parameters[obj.id] = {'objID': obj.id, 'category': category_const}
        result = multi_requests('cmdb.category', parameters)

        for obj in self:
            if obj.id in result:
                obj._fill_category_data(category_const, result[obj.id])


class CMDBObject(dict):
    """
    A CMDB Object.
    """

    def __init__(self, type_id):
        self.id = None
        self.sys_id = None
        self.title = None
        self.type = type_id
        self.is_up2date = False

        # Fields contains the structure of the object rebuild with CMDBCategoryValues and CMDBCategoryValuesList Objects
        self.fields = None
        self.field_data_fetched = dict()

        self.__fetchtype__()

    def __fetchtype__(self):
        self.type_object = get_cmdb_type(self.type)
        self.fields = self.type_object.getObjectStructure()

        for category_const in self.getTypeCategories():
            self.field_data_fetched[category_const] = False

    def fill(self, data, fetchall=False):
        self.id = data['id']
        self.sys_id = data['sysid']
        self.title = data['title']
        self.status = data['status']
        self.type = data['type']

        if fetchall:
            for category_const in self.getTypeCategories():
                self._fetch_category_data(category_const)

    def _is_category_data_fetched(self, category_const):
        return self.field_data_fetched[category_const]

    def _fetch_category_data(self, category_const):
        if category_const not in self.fields:
            raise Exception('Object has no category %s in his type %s' % (category_const, self.type_object.const))
        category_object = get_category(category_const)

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
                entry.mark_updated()
                self.fields[category_const].append(entry)
        else:
            for fields in result:
                self.fields[category_const]._fill_category_data(fields)
            self.fields[category_const].mark_updated()

        self.is_up2date = True
        self.field_data_fetched[category_const] = True

    def getTypeCategories(self):
        return self.type_object.getCategories()

    def __setattr__(self, name, value):
        if name != "is_up2date":
            self.is_up2date = False
        super(CMDBObject, self).__setattr__(name, value)

    def __repr__(self):
        return repr({'id': self.id, 'type': self.type, 'title': self.title, 'values': self.fields})

    def __setitem__(self, key, value):
        raise Exception('You can\'t create new categories, without manipulating the type directly.')

    def __getitem__(self, key):
        # TODO: Fetch categorie data only at access time
        if not self._is_category_data_fetched(key) and self.id is not None:
            self._fetch_category_data(key)
        return self.fields[key]

    def __delitem__(self, category_const):
        multi_value = get_cmdb_type(self.type).get_category_inclusion(category_const).multi_value
        if multi_value:
            for i in range(1, len(self.fields[category_const])):
                del self.fields[category_const]
        else:
            raise NotImplementedError()

    def save(self):

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
                        requests[len(requests)] = {'method':method, 'parameter': parameter}
                        field.mark_updated()
                    else:
                        logging.debug("Category %s/%s of Object %s has no updates skipping" % (category_const, field.id, self.id))
                for field in self.fields[category_const].deleted_items:
                    if field.id:
                        parameter = pm_tpl.copy()
                        logging.debug("Delete %s[%s]" % (category_const, str(field.id)))
                        method = "cmdb.category.delete"
                        parameter['id'] = field.id
                        requests[len(requests)] = {'method':"cmdb.category.delete", 'parameter': parameter}
            elif self.fields[category_const].has_updates():
                parameter = pm_tpl.copy()
                parameter['data'] = dict()
                parameter['data']['id'] = self.fields[category_const].id
                for key, value in self.fields[category_const].items():
                    logging.debug("%s[%s](%s)=%s" % (category_const, key, category.get_field_data_type(key), str(value)))
                    parameter['data'][key] = value
                if parameter['data']['id']:
                    method = "cmdb.category.update"
                else:
                    method = "cmdb.category.create"
                requests[len(requests)] = {'method': method, 'parameter': parameter}
                self.fields[category_const].mark_updated()
            else:
                logging.debug("Category %s of Object %s has no updates skipping" % (category_const, self.id))

        multi_method_request(requests)
