# -*- coding: utf-8 -*-
"""Definitions."""

from __future__ import unicode_literals

import pyesedb


COLUMN_TYPE_DESCRIPTIONS = {
    pyesedb.column_types.NULL: 'Null',
    pyesedb.column_types.BOOLEAN: 'Boolean',
    pyesedb.column_types.INTEGER_8BIT_UNSIGNED: 'Integer 8-bit unsigned',
    pyesedb.column_types.INTEGER_16BIT_SIGNED: 'Integer 16-bit signed',
    pyesedb.column_types.INTEGER_32BIT_SIGNED: 'Integer 32-bit signed',
    pyesedb.column_types.CURRENCY: 'Currency',
    pyesedb.column_types.FLOAT_32BIT: 'Floating point 32-bit',
    pyesedb.column_types.DOUBLE_64BIT: 'Floating point 64-bit',
    pyesedb.column_types.DATE_TIME: 'Filetime',
    pyesedb.column_types.BINARY_DATA: 'Binary data',
    pyesedb.column_types.TEXT: 'Text',
    pyesedb.column_types.LARGE_BINARY_DATA: 'Large binary data',
    pyesedb.column_types.LARGE_TEXT: 'Large text',
    pyesedb.column_types.SUPER_LARGE_VALUE: 'Super large value',
    pyesedb.column_types.INTEGER_32BIT_UNSIGNED: 'Integer 32-bit unsigned',
    pyesedb.column_types.INTEGER_64BIT_SIGNED: 'Integer 64-bit signed',
    pyesedb.column_types.GUID: 'GUID',
    pyesedb.column_types.INTEGER_16BIT_UNSIGNED: 'Integer 16-bit unsigned',
}

COLUMN_TYPE_IDENTIFIERS = {
    pyesedb.column_types.NULL: 'JET_coltypNil',
    pyesedb.column_types.BOOLEAN: 'JET_coltypBit',
    pyesedb.column_types.INTEGER_8BIT_UNSIGNED: 'JET_coltypUnsignedByte',
    pyesedb.column_types.INTEGER_16BIT_SIGNED: 'JET_coltypShort',
    pyesedb.column_types.INTEGER_32BIT_SIGNED: 'JET_coltypLong',
    pyesedb.column_types.CURRENCY: 'JET_coltypCurrency',
    pyesedb.column_types.FLOAT_32BIT: 'JET_coltypIEEESingle',
    pyesedb.column_types.DOUBLE_64BIT: 'JET_coltypIEEEDouble',
    pyesedb.column_types.DATE_TIME: 'JET_coltypDateTime',
    pyesedb.column_types.BINARY_DATA: 'JET_coltypBinary',
    pyesedb.column_types.TEXT: 'JET_coltypText',
    pyesedb.column_types.LARGE_BINARY_DATA: 'JET_coltypLongBinary',
    pyesedb.column_types.LARGE_TEXT: 'JET_coltypLongText',
    pyesedb.column_types.SUPER_LARGE_VALUE: 'JET_coltypSLV',
    pyesedb.column_types.INTEGER_32BIT_UNSIGNED: 'JET_coltypUnsignedLong',
    pyesedb.column_types.INTEGER_64BIT_SIGNED: 'JET_coltypLongLong',
    pyesedb.column_types.GUID: 'JET_coltypGUID',
    pyesedb.column_types.INTEGER_16BIT_UNSIGNED: 'JET_coltypUnsignedShort',
}
