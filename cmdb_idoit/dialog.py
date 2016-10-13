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


def get_cmdb_dialog(category_const, field_name):
    return CMDBDialog(category_const, field_name)


class CMDBDialog:
    """
      Representation of a dialog value set.
    """

    def __init__(self, category_const, field_name):
        self.category = category_const
        self.field = field_name
        self.dialog_from_const = dict()
        self.dialog_from_id = dict()
        self._load()

    def _load(self):

        result = request('cmdb.dialog.read', {'category': self.category, 'property': self.field})

        if len(result) == 0:
            logging.warning("Can't fetch dialog entries for category %s and field %s" % (self.category, self.field))
            raise Exception('No dialog informations')
            return
        else:
            for entry in result:
                self.dialog_from_const[entry['const']] = entry
                self.dialog_from_id[entry['id']] = entry

    def get_field_name(self):
        return self.field_name

    def get_category(self):
        return self.category_const

    def get_dialog_from_const(self, dialog_const):
        return self.dialog_from_const[dialog_const]

    def get_dialog_from_id(self, dialog_id):
        return self.dialog_from_id[dialog_id]

    def values(self):
        return self.dialog_from_const.values()
