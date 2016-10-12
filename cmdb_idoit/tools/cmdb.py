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
import cmdb_idoit as cmdb
import logging
import json

# Load credentials
cmdb.init_session_from_config()

# We want some informations
logging.basicConfig(level=logging.WARNING)


@click.group()
def cli():
    pass


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
  struct = dict()
  for catconst in cmdb_categories:
    categorie = cmdb.get_category(catconst)
    catstruct = dict()
    for field in categorie.getFields():
        catstruct[field] = "%s, %s" % (categorie.get_field_data_type(field),categorie.get_field_info_type(field))
    catinc = cmdb_type.get_category_inclusion(catconst)
    if catinc.multi_value:
        struct[catconst] = list([catstruct])
    else:
        struct[catconst] = catstruct
  print(json.dumps(struct, sort_keys=True, indent=4))

@cli.group("category")
def cli_cat():
    pass

@cli_cat.command("list")
def show_object_categories():
    pass

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
    print(objects)
    for category in with_category:
        print(category)


if __name__ == '__main__':
    cli()
