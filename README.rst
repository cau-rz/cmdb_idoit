cmdb-idoit
==========

An abstraction around the json-rpc interface of i-doit.


Configuration
-------------

For `init_session_from_config` a configuration file in INI-Style Format must
be available either at ``~/.cmdbrc`` or ``./cmdbrc``. Following the example:

::

  [main]                                                                          
  url=https://cmdb.example.com/src/jsonrpc.php                                 
  username=johndoe
  password=cleartextpw
  apikey=mycmdbapikey
