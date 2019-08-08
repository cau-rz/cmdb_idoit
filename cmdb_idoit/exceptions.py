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

class CMDBConversionException(Exception):
    pass

class CMDBRequestError(Exception):
    def __init__(self,message,errnr):
        self.message = message 
        self.errnr = int(errnr)

class CMDBNoneAPICategory(Exception):
    pass

class CMDBMissingTypeInformation(Exception):
    pass

class CMDBUnkownType(Exception):
    pass
