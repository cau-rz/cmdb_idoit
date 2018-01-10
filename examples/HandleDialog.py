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

# We want some informations
logging.basicConfig(level=logging.DEBUG)

# Initialise CMDB session
cmdb.init_session(url,apikey,username,password)

# Alternatively we could use
# > cmdb.init_session_from_config()
# to load configuration from file.

# Load the dialog data for C__CATG__CONTACT for property role,
# the resulting object contains all dialog informations currently
# available.
logging.info('Load Dialog for C__CATG__CONTACT and property role')
role = cmdb.CMDBDialog('C__CATG__CONTACT','role')

# Add a new dialog value, be careful, those values can not be removed.
logging.info('Create new dialog value, does nothing if it exists.')
role.add('Master of Disaster')

# Loop over all entries and print them for our amusement 
for dialog_entry in role.values():
    print(dialog_entry)
