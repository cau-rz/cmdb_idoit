#!/usr/bin/env python3
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

import click
from datetime import date, datetime
import cmdb_idoit as cmdb
import logging
import json



@click.group()
@click.option('--profile',help='Profile to use',default='main')
@click.option('--debug/--no-debug',default=False)
def cli(profile,debug):
    if debug:
        # We want some informations
        logging.basicConfig(level=logging.DEBUG)
    else:
        # Not so much informations
        logging.basicConfig(level=logging.INFO)

    # Load credentials
    cmdb.init_session_from_config(profile)

@cli.group("type")
def cli_type():
    pass


@cli_type.command("list")
def list_object_types():
  types = cmdb.request('cmdb.object_types',dict())
  print("Group\tTitle\tId\tConst")
  for typ in types:
    print("%s\t%s\t%s\t%s"% (typ['type_group_title'],typ['title'],typ['id'],typ['const']))


@cli_type.command("declaration")
@click.argument('type_const')
def show_type_declaration(type_const):
  cmdb_type = cmdb.get_cmdb_type(type_const)
  cmdb_categories = cmdb_type.getCategories()
  print(type_const)
  for catconst in cmdb_categories:
    categorie = cmdb.get_category(catconst)
    catinc = cmdb_type.get_category_inclusion(catconst)
    _show_category_declaration(categorie,catinc.multi_value)

#  C__CATS__SERVICE
#    str description        mapped '$.id'
#    str install_path
#    int installation       mapped '$.id'

def _show_category_declaration(category, multi=False):
    print("  %s"  % category.const, end="")
    if multi:
        print("  (list)",end="")
    for field in category.getFields():
        field_type = repr(category.getFieldType(field))
        field_map  = cmdb.value_factory.get_type_mapping(category.const,field)
        print("\n    (%s) %s" % (field_type,field),end="")
        if field_map is not None:
            print(" - mapped with %s" % field_map,end="")
    print("\n")
@cli.group("category")
def cli_cat():
    pass

@cli_cat.command("list")
def show_object_categories():
    pass

@cli_cat.command("declaration")
@click.argument('category_const')
def show_category_declaration(category_const):
    categorie = cmdb.get_category(category_const)
    if categorie is None:
        print("No category with name: %s" % category_const)
        return
    _show_category_declaration(categorie)

@cli_cat.command("dialog")
@click.argument("category_const")
@click.argument("field_name")
def show_category_field_dialog(category_const, field_name):
    cmdb_dialog = cmdb.CMDBDialog(category_const,field_name)
    print("Id\tConstant\t\tTitle")
    for dialog in cmdb_dialog.values():
        print("%s\t%s\t\t%s" % (dialog['id'], dialog['const'], dialog['title']))

@cli.group("object")
def cli_obj():
    pass

@cli_obj.command("find")
@click.option('-t','--type',help="Type of Object",required=True)
@click.option('-c','--with-category',help="load values for category",multiple=True)
def object_find(type,with_category=list()):
    objects = cmdb.CMDBObjects(filters=dict(
        { 'type': type }
        ))
    for category in with_category:
        objects.load_category_data(category)
    for object in objects:
        for category in with_category:
            print(json.dumps(object[category], sort_keys=True, indent=4))

@cli_obj.command("load")
@click.option('-i','--load-object', help="id of requested object",required=True)
@click.option('-c','--with-category',help="load values for category",multiple=True)
def object_load(load_object,with_category=list()):
    obj = cmdb.loadObject(load_object)
    if obj is None:
        print("Can't load object with id: %s" % load_object)
    else:
        print("object\t:",obj.id)
        print("object\ttitle:",obj.title)
        for category_const in with_category:
            obj.loadCategoryData(category_const);
            print(json.dumps(obj[category_const], sort_keys=True, indent=4))

def __json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, cmdb.CMDBRequestError):
        return obj.message
    raise TypeError ("Type %s not serializable" % type(obj))

@cli.command("run")
@click.argument("filename")
def run_queries(filename):
    with open(filename,'r') as f:
        rq = json.load(f)
        if isinstance(rq,dict):
            requests = {}
            requests[0] = { 'method': rq['method'], 'parameter': rq['params'] }
            result = cmdb.multi_method_request(rq,store_errors=True)
            print("Request:")
            print(json.dumps(requests, sort_keys=True, indent=4))
            print("Result:")
            print(json.dumps(result, sort_keys=True, indent=4,default=__json_serial))
        elif isinstance(rq,list):
            requests = {}
            for r in rq:
                requests[r['id']] = { 'method': r['method'], 'parameter': r['params'] }
            result = cmdb.multi_method_request(requests,store_errors=True)
            print("Request:")
            print(json.dumps(requests, sort_keys=True, indent=4))
            print("Result:")
            print(json.dumps(result, sort_keys=True, indent=4,default=__json_serial))

if __name__ == '__main__':
    cli()
