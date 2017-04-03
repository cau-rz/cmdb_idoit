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


class CMDBCategoryValueBase:
    """
    Encapsulate and transform between the python working
    representation of an field value and the storage representation
    of idoit
    """

    value = None

    def __init__(self, value=None):
        self.value = value

    def set(self, value):
        """
        Set the value in the representation of a value.
        """
        self.value = value

    def get(self):
        """
        Return the working value for an representation of a value.
        """
        return self.value

    def store(self):
        """
        Return the storage representation of a value.
        """
        return self.value

    def __repr__(self):
        return repr(self.value)


class CMDBCategoryValueInt(CMDBCategoryValueBase):
    pass
