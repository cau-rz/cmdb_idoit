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

from datetime import date, datetime
import configparser
import json
import logging
import math
import os
import requests


url = None
apikey = None

headers = {'content-type': 'application/json'}

session = requests.Session()
session_stats = { 'requests': 0,
                  'queries': 0
                }


def init_session(cmdb_url, cmdb_apikey, cmdb_username, cmdb_password):
    """
    Initialise session.

    :param url cmdb_url: url to the json api
    :param str cmdb_apikey: i-doit apikey
    :param str cmdb_username: username for authentication
    :param str cmdb_password: password for authentication
    """
    global url, username, password, apikey, session
    url = cmdb_url
    username = cmdb_username
    password = cmdb_password
    apikey = cmdb_apikey

    session.auth = requests.auth.HTTPBasicAuth(username, password)
    session.verify = False
    session.headers.update(headers)


def init_session_from_config(instance='main'):
    """
    Initialise session using a configured profile.

    :param str instance: profile name, default is 'main'
    """
    global url, username, password, apikey, session
    config = configparser.ConfigParser()
    config.read(['cmdbrc', os.path.expanduser('~/.cmdbrc')], encoding='utf8')
    url = config[instance].get('url')
    username = config[instance].get('username')
    password = config[instance].get('password')
    apikey = config[instance].get('apikey')

    session.auth = requests.auth.HTTPBasicAuth(username, password)
    session.verify = config[instance].get('verify',False)
    session.headers.update(headers)

def __json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))


def request(method, parameters):
    """
    Call a JSON RPC `method` with given `parameters`. Automagically handling authentication
    and error handling.
    """
    global url
    if not type(parameters) is dict:
        raise TypeError('parameters not of type dict, but instead ', type(parameters))

    parameters['apikey'] = apikey
    payload = {
        "id": 1,
        "method": method,
        "params": parameters,
        "version": "2.0"}
    logging.debug('request:request_payload:' + json.dumps(payload, sort_keys=True, indent=4,default=__json_serial))
    response = session.post(url, data=json.dumps(payload,default=__json_serial), stream=False)
    session_stats['requests'] += 1
    session_stats['queries'] += 1

    # Validate response
    status_code = response.status_code
    if status_code > 400:
        raise Exception("HTTP-Error(%i)" % status_code)

    if 'content-type' in response.headers:
        if not response.headers['content-type'] == 'application/json':
            raise Exception("Response has unexpected content-type: %s for request %s" % (response.headers['content-type'],url),response.content)
    try:
        res_json = response.json()
    except ValueError:
        return None

    # Raise Exception when an error accures
    if 'error' in res_json:
        logging.error(res_json['error'])
        raise Exception("Error(%i): %s" % (res_json['error']['code'], res_json['error']['message']))

    logging.debug('result:' + json.dumps(res_json['result'], sort_keys=True, indent=4,default=__json_serial))
    return res_json['result']


def multi_requests(method, parameters):
    """
    Call a JSON RPC `method` with given `parameters`. Automagically handling authentication
    and error handling.
    """
    global url

    if not type(parameters) is dict:
        raise TypeError('parameters not of type dict, but instead ', type(parameters))

    """ 
    When we have more requests than the idoit system can handle then
    we split them up and merge the results.
    """
    max_parameters = 256
    if len(parameters) > max_parameters:
        length = len(parameters)
        result = dict()
        items = list(parameters.items())
        for i in range(0,math.ceil(length / max_parameters)):
          sub = dict(items[max_parameters * i:min(max_parameters * (i + 1),length)])
          sub_result = multi_requests(method,sub)
          result.update(sub_result)
        return result
    
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

    logging.debug('request_payload:' + json.dumps(payload, sort_keys=True, indent=4,default=__json_serial))
    response = session.post(url, data=json.dumps(payload,default=__json_serial), stream=False)
    session_stats['requests'] += 1
    session_stats['queries'] += len(payload)

    # Validate response
    status_code = response.status_code
    if status_code > 400:
        raise Exception("HTTP-Error(%i)" % status_code)

    if 'content-type' in response.headers:
        if not response.headers['content-type'] == 'application/json':
            raise Exception("Response has unexpected content-type: %s", response.headers['content-type'])
    res_jsons = response.json()
    if res_jsons is None:
        return dict()

    result = dict()
    for res_json in res_jsons:
        # Raise Exception when an error accures
        if 'error' in res_json and res_json['error']:
            logging.error(res_json['error'])
        else:
            result[res_json['id']] = res_json['result']

    logging.debug('result:' + json.dumps(result, sort_keys=True, indent=4,default=__json_serial))
    return result

def multi_method_request(parameters):
    """
    Call a JSON RPC `method` with given `parameters`. Automagically handling authentication
    and error handling.
    """
    global url
    if not type(parameters) is dict:
        raise TypeError('parameters not of type dict, but instead ', type(parameters))
    
    if len(parameters) == 0:
        return {}

    payload = list()
    for key, call in parameters.items():
        parameter = call['parameter']
        if not type(parameter) is dict:
            raise TypeError('entry of parameters not of type dict, but instead ', type(parameter))
        parameter['apikey'] = apikey
        payload.append({
            "id": key,
            "method": call['method'],
            "params": parameter,
            "version": "2.0"})

    logging.debug('request_payload:' + json.dumps(payload, sort_keys=True, indent=4,default=__json_serial))
    response = session.post(url, data=json.dumps(payload,default=__json_serial), stream=False)
    session_stats['requests'] += 1
    session_stats['queries'] += len(payload)

    # Validate response
    status_code = response.status_code
    if status_code > 400:
        raise Exception("HTTP-Error(%i)" % status_code)

    if 'content-type' in response.headers:
        if not response.headers['content-type'] == 'application/json':
            raise Exception("Response has unexpected content-type: %s" % response.headers['content-type'],response.content)
    try:
        res_jsons = response.json()
    except Exception as e:
        logging.error("multi_method_request: Failed to parse result",response.content)
        # Try to decode the last line of the response.
        try:
          res_jsons = json.loads(response.text.splitlines()[-1])
        except:
          raise e

    result = dict()
    for res_json in res_jsons:
        # Raise Exception when an error accures
        if 'error' in res_json and res_json['error']:
            logging.error(res_json['error'])
        else:
            result[res_json['id']] = res_json['result']

    logging.debug('result:' + json.dumps(result, sort_keys=True, indent=4,default=__json_serial))
    return result
