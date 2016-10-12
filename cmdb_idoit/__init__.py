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

import requests
import json
import base64
import logging
import configparser
import os

headers = {'content-type': 'application/json'}

session = requests.Session()

url = None
apikey = None


def init_session(cmdb_url, cmdb_apikey, cmdb_username, cmdb_password):
    global url, username, password, apikey, session
    url = cmdb_url
    username = cmdb_username
    password = cmdb_password
    apikey = cmdb_apikey

    session.auth = requests.auth.HTTPBasicAuth(username, password)
    session.verify = False
    session.headers.update(headers)


def init_session_from_config(instance='main'):
    global url, username, password, apikey, session
    config = configparser.ConfigParser()
    config.read(['cmdbrc', os.path.expanduser('~/.cmdbrc')], encoding='utf8')
    url = config[instance].get('url')
    username = config[instance].get('username')
    password = config[instance].get('password')
    apikey = config[instance].get('apikey')

    session.auth = requests.auth.HTTPBasicAuth(username, password)
    session.verify = False
    session.headers.update(headers)


def request(method, parameters):
    global url
    """
    Call a JSON RPC `method` with given `parameters`. Automagically handling authentication
    and error handling.
    """
    if not type(parameters) is dict:
        raise TypeError('parameters not of type dict, but instead ', type(parameters))

    parameters['apikey'] = apikey
    payload = {
        "id": 1,
        "method": method,
        "params": parameters,
        "version": "2.0"}
    logging.debug('request_payload:' + json.dumps(payload, sort_keys=True, indent=4))
    response = session.post(url, data=json.dumps(payload), verify=False, stream=False)

    # Validate response
    status_code = response.status_code
    if status_code > 400:
        raise Exception("HTTP-Error(%i)" % status_code)

    if 'content-type' in response.headers:
        if not response.headers['content-type'] == 'application/json':
            raise Exception("Response has unexpected content-type: %s" % response.headers['content-type'])
    try:
        res_json = response.json()
    except ValueError:
        return None

    # Raise Exception when an error accures
    if 'error' in res_json:
        logging.error(res_json['error'])
        raise Exception("Error(%i): %s" % (res_json['error']['code'], res_json['error']['message']))

    logging.debug('result:' + json.dumps(res_json['result'], sort_keys=True, indent=4))
    return res_json['result']


def _requests(method, parameters):
    global url
    """
    Call a JSON RPC `method` with given `parameters`. Automagically handling authentication
    and error handling.
    """
    if not type(parameters) is dict:
        raise TypeError('parameters not of type dict, but instead ', type(parameters))

    payload = list()
    for key, parameter in parameters.items():
        if not type(parameter) is dict:
            raise TypeError('entry of parameters not of type dict, but instead ', type(parameter))
        parameter['apikey'] = apikey
        payload.append({
            "id": key,
            "method": method,
            "params": parameter,
            "version": "2.0"})

    response = session.post(url, data=json.dumps(payload), verify=False, stream=False)

    # Validate response
    status_code = response.status_code
    if status_code > 400:
        raise Exception("HTTP-Error(%i)" % status_code)

    if 'content-type' in response.headers:
        if not response.headers['content-type'] == 'application/json':
            raise Exception("Response has unexpected content-type: %s", response.headers['content-type'])
    res_jsons = response.json()

    result = dict()
    for res_json in res_jsons:
        # Raise Exception when an error accures
        if 'error' in res_json and res_json['error']:
            logging.error(res_json['error'])
        else:
            result[res_json['id']] = res_json['result']

    logging.debug('result:' + json.dumps(result, sort_keys=True, indent=4))
    return result


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


class CMDBCategory(dict):
    """
    A model representing a CMDB category.
    """

    def __init__(self, category_id, category_const, global_category):
        self.id = category_id
        self.const = category_const
        self.global_category = global_category
        self.fields = dict()

        parameter = dict()
        if self.global_category:
            parameter['catgID'] = self.id
        else:
            parameter['catsID'] = self.id

        result = request('cmdb.category_info', parameter)

        if type(result) is dict:
            self.fields = result

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

    def getfieldtype(self, index):
        return self.fields[index]['data']['type']


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

    def __delitem__(self,index):
        if isinstance(index,slice):
            for x in sorted(range(0,len(self))[index],reverse=True):
                del self[x]
        else:
            item = list.__getitem__(self,index)
            if isinstance(item,CMDBCategoryValues) and item.id:
                self.deleted_items.append(item)
            list.__delitem__(self,index)

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
            # Get type,value of field
            field_type = self.category.getfieldtype(index)
            field_value = None
            if index in self:
                self._field_up2date_state[index] = self[index] == value
                field_value = dict.__getitem__(self,index)
            else:
                self._field_up2date_state[index] = False
            # rough field Type/handling detection 
            if field_type == 'int':
                if type(field_value) is list:
                    # TODO We need to encapsulate values in an extra type ....
                    #      to get a better guess 
                    pass
                else:
                    if not isinstance(field_value,dict):
                        field_value = dict()
                    field_value['value'] = value
                    value = field_value
            elif field_type == 'text':
                if not isinstance(field_value,dict):
                    field_value = dict()
                field_value['ref_title'] = value
                value = field_value
            dict.__setitem__(self, index, value)
        else:
            raise KeyError("Category " + self.category.const + " has no field " + index)

    def __getitem__(self,index):
        field_type = self.category.getfieldtype(index)
        field_value = dict.__getitem__(self,index)
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
        return [ (key, self[key]) for key in keys ]

    def values(self):
        keys = dict.keys(self)
        return [ self[key] for key in keys ]

    def update(self,other_dict):
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


class CMDBTypeCache(dict):

    def __init__(self):
        self.const_to_type = dict()

    def __setitem__(self, key, value):
        if not type(value) is CMDBType:
            raise TypeError("Object is not of type CMDBType")
        if key in self.const_to_type:
            dict.__setitem__(self, self.const_to_type[key], value)
        else:
            self.const_to_type[value.get_const()] = value.get_id()
            dict.__setitem__(self, key, value)

    def __getitem__(self, key):
        if key in self.const_to_type:
            return dict.__getitem__(self, self.const_to_type[key])
        else:
            return dict.__getitem__(self, key)

    def __contains__(self, key):
        if key in self.const_to_type:
            return dict.__contains__(self, self.const_to_type[key])
        else:
            return dict.__contains__(self, key)


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
    return cmdb_type.get_const


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
        self.special_categories = dict()

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
            logging.warning("Can't fetch type information for type_id: %s" % type_id)
            self.id = type_id
            self.const = 'UNKNOWN_TYPE_' + type_id
            return

        result = result.pop()

        self.id = result['id']
        self.const = result['const']
        self.titlte = result['title']
        self.status = result['status']
        self.meta['type_group'] = result['type_group']
        self.meta['type_group_title'] = result['type_group_title']
        self.meta['tree_group'] = result['tree_group']

        logging.info("Loading type %s" % self.get_const())

        result = request('cmdb.object_type_categories', {'type': self.get_id()})

        # process structural information about categories
        categories = list()
        if 'catg' in result:
            categories += [(True, c) for c in result['catg']]

        if 'cats' in result:
            categories += [(False, c) for c in result['cats']]

        for glob, cat in categories:
            logging.info("Loading category %s" % cat['const'])
            category_type_inclusion = self.CMDBTypeCategoryInclusion()
            if 'parent' in cat:
                category_type_inclusion.parent = cat['parent']
            category_type_inclusion.multi_value = cat['multi_value'] == "1"
            category_type_inclusion.source_table = cat['source_table']

            category_object = get_category(category_const=cat['const'], category_id=cat['id'], category_global=glob)
            category_type_inclusion.category = category_object
            if glob:
                self.global_categories[category_object.get_const()] = category_type_inclusion
            else:
                self.special_categories[category_object.get_const()] = category_type_inclusion

    def get_category_inclusion(self, category_const):
        if category_const in self.global_categories:
            return self.global_categories[category_const]
        else:
            return self.special_categories[category_const]

    def getCategories(self):
        return list(self.global_categories.keys()) + list(self.special_categories.keys())

    def getObjectStructure(self):
        """
        Initialize the structure of a type. So every category is prepared as a CMDBCategoryValues
        Object, except for those multie value categories.
        """
        values = dict()

        for category_object in list(self.global_categories.values()) + list(self.special_categories.values()):
            if category_object.multi_value:
                values[category_object.category.get_const()] = CMDBCategoryValuesList(category_object.category)
            else:
                values[category_object.category.get_const()] = CMDBCategoryValues(category_object.category)

        return values


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
        result = _requests('cmdb.category', parameters)

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

    def __delitem__(self,category_const):
        multi_value = get_cmdb_type(self.type).get_category_inclusion(category_const).multi_value
        if multi_value:
            for i in range(1,len(self.fields[category_const])):
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

        for category_const in self.getTypeCategories():
            category = get_category(category_const)
            parameter = dict()
            parameter['objID'] = self.id
            parameter['category'] = category_const

            object_type = get_cmdb_type(self.type)

            multi_value = object_type.get_category_inclusion(category_const).multi_value

            # Skip this category iff we are not creating and field is not fetched
            if not is_create and not self._is_category_data_fetched(category_const):
                continue

            if multi_value:
                for field in self.fields[category_const]:
                    if field.has_updates():
                        parameter['data'] = dict()
                        for key, value in field.items():
                            logging.debug("%s[%s](%s)=%s" % (category_const, key, category.getfieldtype(key), str(value)))
                            if field.has_value_been_updated(key):
                                parameter['data'][key] = value
                        if field.id:
                            method = "cmdb.category.update"
                            parameter['data']['id'] = field.id
                        else:
                            method = "cmdb.category.create"
                        request(method, parameter)
                        field.mark_updated()
                    else:
                        logging.debug("Category %s/%s of Object %s has no updates skipping" % (category_const, field.id, self.id))
                for field in  self.fields[category_const].deleted_items:
                    if field.id:
                        method = "cmdb.category.delete"
                        parameter['id'] = field.id
                        request(method, parameter)
            elif self.fields[category_const].has_updates():
                parameter['data'] = dict()
                parameter['data']['id'] = self.fields[category_const].id
                for key, value in self.fields[category_const].items():
                    logging.debug("%s[%s](%s)=%s" % (category_const, key, category.getfieldtype(key), str(value)))
                    parameter['data'][key] = value
                if parameter['data']['id']:
                    method = "cmdb.category.update"
                else:
                    method = "cmdb.category.create"
                request(method, parameter)
                self.fields[category_const].mark_updated()
            else:
                logging.debug("Category %s of Object %s has no updates skipping" % (category_const, self.id))
