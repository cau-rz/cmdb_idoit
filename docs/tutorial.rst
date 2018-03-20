.. _tutorial:

Tutorial
========

In this part of the documentation we discuss practical patterns for access, modifying and storing data in the cmdb.

Connect to the cmdb
-------------------

We can connect to the cmdb by utilizing the configuration (See :ref:`configuration`)

::

  import cmdb_idoit as cmdb

  cmdb.init_session_from_config()

or directly define access parameters in the code

::

  import cmdb_idoit as cmdb
     
  url = "https://cmdb.example.de/src/jsonrpc.php"
  username = 'exampleuser'
  password = 'examplepassword'
  apikey = 'exampleapikey'

  cmdb.init_session(url,apikey,username,password)


Loading Objects
---------------

Let us start with a simple example to access Objects. 
Therefore we first determine the object type constant. 
For this example we want all the servers, so the constant is ``C__OBJTYPE__SERVER``. 
If you want another object type, see :ref:`commandline`.

The following will load all server objects and print their title.

::

  servers = cmdb.CMDBObjects({'type': 'C__OBJTYPE__SERVER'})

  for server in servers:
    print(server.title)


Accessing category data
-----------------------

Now we have all the servers, we can access category data by using the objects
as :py:class:`dict` with the category constants as keys. Accessing them directly 
will fetch the data on demand from the database. Each category itself
is also accessible like an natural :py:class:`dict` with a fixed key set.

::

  for server in servers:
    print(server['C__CATG__GLOBAL']['title'])

If you are going access a lot of category data of the same category for several
objects you should prefetch the dataset. 

Prefetch category data for objects
----------------------------------

::

  servers.loadCategoryData('C__CATG__GLOBAL')

  for server in servers:
    print(server['C__CATG__GLOBAL']['title'])


As an exercise try both variants and measure the time.

Handle multi value categories
-----------------------------

Some object have so called multi value categories, hence have multiple 
instantiations of the same category. Those are represented as :py:class:`list`
so we can iterate over them.


:: 
  servers.loadCategoryData('C__CATG__CONTACT')

  for server in servers:
    print(server.title)
    for contact in server['C__CATG__CONTACT']:
      print(contact['contact'])

The above example will print a set of numbers, for each server. Those numbers are
the object identifier for another object. If you want to more about the contact
you have to load that object, it may have any possible object type.

Change an object
----------------

Every object has a :py:attr:`cmdb_idoit.CMDBObject.title` which can be manipulated without loading any further
category data.

::

  someserver = servers.pop()
  someserver.title = "Some new Title"
  someserver.save()

We can of course manipulate other data, too.

::

  someserver['C__CATG__GLOBAL']['title'] = "New Title"
  someserver.save()


The above example will, save the new value. Even if you have not loaded the
category data for ``C__CATG__GLOBAL``.

Dealing with Dialogs
--------------------

Many values in the i-doit web interface are predefined lists of selectable values, so called dialogs, 
e.g. the room type. In the API those attributes are represented as :py:class:`int`. You can either
define needed values in the Web Interface and view their :py:class:`int` representation with the 
:ref:`commandline` utility or you define them in code and use the defined value directly.

::

  cmdb_status = cmdb.CMDBDialog('C__CATG__GLOBAL','cmdb_status')
  cmdb_status_planned = cmdb_status.get_dialog_from_const('C__CMDB_STATUS__PLANNED')

This example loads the dialog values for ``C__CATG__GLOBAL.cmdb_status`` and stores the value 
for the planned state into a local variable. The above variant is more language save than the
code below, but the code below allows definition of dialog values in code. At the time of this
writing there is no way to define constants for values like used above, you have to predefine
them in the web interface.

:: 
  
  cmdb_status_timetravel_value = "Wibbly Wobbly Timey Wimey"
  cmdb_status.add(cmdb_status_timetravel_value)
  cmdb_status_timetravel = cmdb_status.get_dialog_from_value(cmdb_status_timetravel_value)

  someserver['C__CATG__GLOBAL']['cmdb_status'] = cmdb_status_timetravel
  someserver.save()

The CMDBDialog object is aware of the available values, so readding them every time you run the
code will not add them again. As long as you do not change the value.
