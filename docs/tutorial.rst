.. _tutorial:

Tutorial
========

In this part of the documentation we discuss practical examples for access, modifying and storing data in the cmdb.

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
    print(server['title'])


Accessing category data
-----------------------


Prefetch category data for objects
----------------------------------



