Mitigating around glitches
==========================

This part of the documentation describes the mechanisms which we need 
to mitigate around the glitches of the wrapped JSON-API.

Fixing data structures
----------------------

See `cmdb_idoit.category.value_factory.type_determination`, which basically 
processes queried data structures by a set of rules from `cmdb_idoit.category.map`.

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

.. autofunction:: cmdb_idoit.category.value_factory.type_check
