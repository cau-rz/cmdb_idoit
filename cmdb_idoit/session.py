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
import configparser
import os
import logging
import json


url = None
apikey = None

headers = {'content-type': 'application/json'}

session = requests.Session()


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
    session.verify = config[instance].get('verify',True)
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
    logging.debug('request:request_payload:' + json.dumps(payload, sort_keys=True, indent=4))
    response = session.post(url, data=json.dumps(payload), verify=False, stream=False)

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

    logging.debug('result:' + json.dumps(res_json['result'], sort_keys=True, indent=4))
    return res_json['result']


def multi_requests(method, parameters):
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

    logging.debug('request_payload:' + json.dumps(payload, sort_keys=True, indent=4))
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

def multi_method_request(parameters):
    global url
    """
    Call a JSON RPC `method` with given `parameters`. Automagically handling authentication
    and error handling.
    """
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

    logging.debug('request_payload:' + json.dumps(payload, sort_keys=True, indent=4))
    response = session.post(url, data=json.dumps(payload), verify=False, stream=False)

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

    logging.debug('result:' + json.dumps(result, sort_keys=True, indent=4))
    return result
