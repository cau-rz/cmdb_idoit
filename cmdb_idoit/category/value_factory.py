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


from .value_base import *
from .value_dialog import *
from .value_text import *


def value_representation_factory(data_type, info_type, value=None):
    try:
        if data_type == 'int':
            if info_type == 'dialog':
                return CMDBCategoryValueDialog(value)
            elif info_type == 'dialog_plus':
                return CMDBCategoryValueDialog(value)
            elif info_type == 'object_browser':
                return CMDBCategoryValueInt(value)
            elif info_type == 'int':
                return CMDBCategoryValueInt(value)
            elif info_type == 'n2m':
                return CMDBCategoryValueBase(value)
            elif info_type == 'multiselect':
                return CMDBCategoryValueBase(value)
            else:
                raise NotImplementedError('Info type %s with data type %s is not implemented' % (info_type, data_type))
        elif data_type == 'float':
            if info_type == 'float':
                return CMDBCategoryValueBase(value)
            else:
                raise NotImplementedError('Info type %s with data type %s is not implemented' % (info_type, data_type))
        elif data_type == 'double':
            if info_type == 'double':
                return CMDBCategoryValueBase(value)
            else:
                raise NotImplementedError('Info type %s with data type %s is not implemented' % (info_type, data_type))
        elif data_type == 'text_area':
            return CMDBCategoryValueBase(value)
        elif data_type == 'text':
            if info_type == 'text':
                return CMDBCategoryValueText(value)
            elif info_type == 'multiselect':
                return CMDBCategoryValueBase(value)
            else:
                raise NotImplementedError('Info type %s with data type %s is not implemented' % (info_type, data_type))
        else:
            raise NotImplementedError('Data type %s is not implement' % data_type)
    except Exception as e:
        raise Exception('Error with value of data type %s and info type %s' % (data_type, info_type), e, value)
