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
# > cmdb.init_session_from_config()
# to load configuration from file.

# We want some informations
logging.basicConfig(level=logging.INFO)

# Create a list of Objects declared by the given filter. Since we are lazy by
# default we only fetch the list of matching objects and type informations.
# Everything else is fetched when needed.
logging.info('Load all person objects')
persons = cmdb.CMDBObjects({'type': 'C__OBJTYPE__PERSON'})

# In the loop below we want to access a value from the category C__CATS__PERSON,
# we could do that without any further work, but that would result in tons
# of request to the CMDB, so we fetch the needed data in one big request. 
# That is faster and we don't get kicked for being way to active.
logging.info('Load category data')
persons.load_category_data('C__CATS__PERSON')

logging.info('Print all the data')
for person in persons:
    print("%s %s %s" % (person.id, person.title, person['C__CATS__PERSON']['mail']))
