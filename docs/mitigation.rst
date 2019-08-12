Mitigating around glitches
==========================

This part of the documentation describes the mechanisms which we need 
to mitigate around the glitches of the wrapped JSON-API.

Fixing data structures
----------------------

See `cmdb_idoit.category.value_factory.type_determination`, which basically 
processes queried data structures by a set of rules from `cmdb_idoit.category.map`.

When the determined type of an attribute of a category is not derivable from the
received data, you will see some critical error like below:

:: 

  CRITICAL:root:There was a fatal error while deriving a representativ value for C__CATG__CONTACT.contact.
  According to the API the type of this attribute is 'int', but it was not possible to
  derive this type from the received data:

  [{'phone': '..', 'ldap_group': '', 'sysid': '..' 'title': '..', 'type': 'C__OBJTYPE__PERSON_GROUP', 'email_address': '..', 'id': '1234', 'right_group': '0'}]

  Either we do something ugly wrong or a mapping for this attribute is needed.
  For more information consult the mitigation chapter in the documentation.


For fixing this kind of error we need to create a mapping.

Type Mappings
.............

A type mapping is a entry consisting of the category constant, the name of the attribute,
the type which should be derived and a jsonpath-ng expression. The mapping for the above
error example would be:

::

  C__CATG__CONTACT contact int $[*].id


Ignoring Attributes without type informations
---------------------------------------------

Since version 1.13 idoit doesn't provide type informations for random attributes.
We automagically ignore these attriubtes, usage of these attributes results
in a `KeyError`. Ignoring is reporting by a WARNING log message.
    

Fixing type values
------------------

For fixing type values we first need to determine the type of an attribute,
this logic is done by `cmdb_idoit.category.value_factory.type_determination`.
We use the determined type to later check if a value is indeed of the right
type, which is done by `cmdb_idoit.category.value_factory.type_check`.
But the main work for converting the values themself is done by a set
of conversion functions living in `cmdb_idoit.category.conversion`.


API
...

.. autofunction:: cmdb_idoit.category.value_factory.value_representation_factory

.. autofunction:: cmdb_idoit.category.value_factory.type_determination

.. autofunction:: cmdb_idoit.category.value_factory.get_type_mapping

.. autoclass:: cmdb_idoit.category.value_factory.AttributeType
