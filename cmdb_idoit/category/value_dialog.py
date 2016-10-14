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


from .value_base import CMDBCategoryValueBase


class CMDBCategoryValueDialog(CMDBCategoryValueBase):

    def __init__(self, value=None):
        if isinstance(value, dict):
            if 'id' in value:
                self.value = value['id']
            elif 'value' in value:
                self.value = value['value']
            else:
                raise TypeError("No valid int-dialog representation", value)
        elif value is None:
            pass
        elif isinstance(value, list) and len(value) == 0:
            # This case is equivalent to the previous
            pass
        else:
            raise TypeError("No valid int-dialog representation", value)
