API
===

This part of the documentation covers all the interfaces of cmdb_idoit.

Object Types
------------

.. autoclass:: cmdb_idoit.CMDBType
   :members:
   :inherited-members:

.. autofunction:: cmdb_idoit.get_cmdb_type

.. autofunction:: cmdb_idoit.get_type_id_from_const

.. autofunction:: cmdb_idoit.get_type_const_from_id

Type Categories
---------------

Each object type is actually metadata and a set of subtypes, which we call categories in the i-doit context.
There are three kinds of categories.

.. autoclass:: cmdb_idoit.CMDBCategoryType 
  :members:

.. autoclass:: cmdb_idoit.CMDBCategory

.. autofunction:: cmdb_idoit.get_category

.. autofunction:: cmdb_idoit.is_categorie_cached

.. autofunction:: cmdb_idoit.fetch_categories


Object Instances
----------------

.. autoclass:: cmdb_idoit.CMDBObject
   :members:

.. autofunction:: cmdb_idoit.loadObject

.. autoclass:: cmdb_idoit.CMDBObjects
   :members:


Type Category Instances
-----------------------

.. autoclass:: cmdb_idoit.CMDBCategoryValuesList
   :members:
   :inherited-members:

.. autoclass:: cmdb_idoit.CMDBCategoryValues
   :members:
   :inherited-members:


Type and Category Caches
------------------------

To prevent repeated type information requests, information gets cached.

.. autoclass:: cmdb_idoit.CMDBTypeCache
   :members:

.. autoclass:: cmdb_idoit.CMDBCategoryCache
   :members:

Dialogs
-------

.. autoclass:: cmdb_idoit.CMDBDialog
   :members:

.. autofunction:: cmdb_idoit.get_cmdb_dialog

.. autofunction:: cmdb_idoit.get_cmdb_dialog_id_from_const

