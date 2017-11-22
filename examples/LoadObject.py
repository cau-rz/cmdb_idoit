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

import logging
import cmdb_idoit as cmdb

# Credentials
url = "https://cmdb.example.de/src/jsonrpc.php"
username = 'exampleuser'
password = 'examplepassword'
apikey = 'exampleapikey'


# Initialise CMDB session
cmdb.init_session(url,apikey,username,password)

# Alternatively we could use
cmdb.init_session_from_config('test')
# to load configuration from file.

# We want some informations
logging.basicConfig(level=logging.DEBUG)

# Load a specific object where we know the object id of.
obj = cmdb.loadObject('12452')

# Load all available Category Data for that object.
obj.loadAllCategoryData()

print(obj)
