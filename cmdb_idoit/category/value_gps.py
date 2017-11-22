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

class CMDBCategoryValueGPS(CMDBCategoryValueBase):
    
    def __init__ (self, value=None):
        self.latitude = None
        self.longitude = None
        if value is not None:
            self.latitude = value['latitude']
            self.longitude = value['longitude']

    def store(self):
        return  {'latitude': self.latitude, 'longitude': self.longitude }

    def get(self):
        return self.store()

    def __repr__(self):
        return repo(self.store())
