.. _configuration:

Configuration
=============

In this part of the documentation we talk about the runtime configuration.

The configuration happens in the *INI* style configuration file ``~/.cmdbrc``.

Profiles
--------

You can define multiple profiles for multiple *i-doit* instances,
e.g. one for production and one for testing purposes. Each section
in the configuration file correspond to one instance. The primary or default
instance is named **main**.

::

    [main]
    url=https://cmdb.example.com/path/to/jsonrpc.php
    username=exampleuser
    password=exampleuserpassword
    apikey=IDoITAPIKey
    verfiy=optionalpathtocert.pem

Each section MUST contain key/value-pairs for url, username, password and apikey.
The verify key is optional, but we recommend defining it
