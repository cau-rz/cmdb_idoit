#!/usr/bin/env python3 
import click
import cmdb_idoit as cmdb
import logging
import json

# Load credentials
cmdb.init_session_from_config()

# We want some informations
logging.basicConfig(level=logging.DEBUG)

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
        catstruct[field] = categorie.getfieldtype(field)
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

if __name__ == '__main__':
    cli()
