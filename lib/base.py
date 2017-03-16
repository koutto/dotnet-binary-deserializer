from __future__ import absolute_import

import struct
import sys
import logging

from lib.datatypes import *

logging.basicConfig(level=logging.INFO)



def print_records(records, skip=0, fp=None, first_call=True, output=None, fp_enabled=False):
    """prints the given record tree into a file like object
    
    :param records: a tree of record objects
    :type records: wcf.records.Record
    :param skip: start value for intending (Default: 0)
    :type skip: int
    :param fp: file like object to print to (Default: sys.stdout)
    
    """
    if records == None:
        return
    if fp_enabled and fp == None:
        fp = sys.stdout

    was_el = False
    for r in records:
        if isinstance(r, EndElementRecord):
            continue
        if isinstance(r, Element):
            out = ('\r\n' if not first_call else '') + ' ' * skip + str(r)
            if output:
                output[0] += out
            if fp_enabled:
                fp.write(out)
        else:
            out = str(r)
            if output:
                output[0] += out
            if fp_enabled:
                fp.write(out)
       
        new_line = False
        if hasattr(r, 'childs'):
            new_line = print_records(r.childs, skip+1, fp, False, output)
        if isinstance(r, Element):
            if new_line:
                out = '\r\n' + ' ' * skip
                if output:
                    output[0] += out
                if fp_enabled:
                    fp.write(out)
            if hasattr(r, 'prefix'):
                out = '</%s:%s>' % (r.prefix, r.name)
                if output:
                    output[0] += out
                if fp_enabled:
                    fp.write(out)
            else:
                out = '</%s>' % r.name
                if output:
                    output[0] += out
                if fp_enabled:
                    fp.write(out)
            was_el = True
        else:
            was_el = False
    return was_el

def repr_records(records, skip=0):
    if records == None:
        return

    for r in records:
        print ' '*skip + str(r)
        if hasattr(r, 'childs'):
            repr_records(r.childs, skip+1)

def dump_records(records):
    """
    returns the byte representation of a given record tree

    :param records: the record tree
    :type records: wcf.records.Record
    :returns: a bytestring
    :rtype: str
    """
    out = ''
    #print records
    for r in records:
        msg = 'Write %s' % type(r).__name__
        if r == records[-1]:
            if isinstance(r, Text):
                r.type = r.type + 1
                msg += ' with EndElement (0x%X)' % r.type
        log.debug(msg)
        log.debug('Value %s' % str(r))
        if isinstance(r, Element) and not isinstance(r, EndElementRecord) and len(r.attributes):
            log.debug(' Attributes:')
            for a in r.attributes:
                log.debug(' %s: %s' % (type(a).__name__, str(a)))
        #print r
        out += r.to_bytes()
        
        if hasattr(r, 'childs'):
            out += dump_records(r.childs)
            if len(r.childs) == 0 or not isinstance(r.childs[-1], Text):
                log.debug('Write EndElement for %s' % r.name)
                out += EndElementRecord().to_bytes()
        elif isinstance(r, Element) and not isinstance(r, EndElementRecord):
            log.debug('Write EndElement for %s' % (r.name,))
            out += EndElementRecord().to_bytes()

    return out


class Record(object):
    records = dict()

    @classmethod
    def add_records(cls, records):
        """adds records to the lookup table

        :param records: list of Record subclasses
        :type records: list(Record)
        """
        for r in records:
            Record.records[r.type] = r

    def __init__(self, type=None):
        if type:
            self.type = type

    def to_bytes(self):
        """
        Generates the representing bytes of the record

        >>> from wcf.records import *
        >>> Record(0xff).to_bytes()
        '\\xff'
        >>> ElementRecord('a', 'test').to_bytes()
        'A\\x01a\\x04test'
        """
        return struct.pack('<B', self.type)

    def __repr__(self):
        args = ['type=0x%X' % self.type]
        return '<%s(%s)>' % (type(self).__name__, ','.join(args))

    @classmethod
    def parse(cls, fp):
        """
        Parses the binary data from fp into Record objects

        :param fp: file like object to read from
        :returns: a root Record object with its child Records
        :rtype: Record

        >>> from wcf.records import *
        >>> from StringIO import StringIO as io
        >>> buf = io('A\\x01a\\x04test\\x01')
        >>> r = Record.parse(buf)
        >>> r
        [<ElementRecord(type=0x41)>]
        >>> str(r[0])
        '<a:test >'
        >>> dump_records(r)
        'A\\x01a\\x04test\\x01'
        >>> _ = print_records(r)
        <a:test ></a:test>
        """
        if cls != Record:
            return cls()
        root = []
        records = root
        parents = []
        last_el = None
        type = True
        while type:
            type = fp.read(1)
            if type:
                type = struct.unpack('<B', type)[0]
                if type in Record.records:
                    log.debug('%s found' % Record.records[type].__name__)
                    obj = Record.records[type].parse(fp)
                    if isinstance(obj, EndElementRecord):
                        if len(parents) > 0:
                            records = parents.pop()
                        #records.append(obj)
                    elif isinstance(obj, Element):
                        last_el = obj
                        records.append(obj)
                        parents.append(records)
                        obj.childs = []
                        records = obj.childs
                    elif isinstance(obj, Attribute) and last_el:
                        last_el.attributes.append(obj)
                    else:
                        records.append(obj)
                    log.debug('Value: %s' % str(obj))
                elif type-1 in Record.records:
                    log.debug('%s with end element found (0x%x)' %
                            (Record.records[type-1].__name__, type))
                    records.append(Record.records[type-1].parse(fp))
                    #records.append(EndElementRecord())
                    last_el = None
                    if len(parents) > 0:
                        records = parents.pop()
                else:
                    log.warn('type 0x%x not found' % type)

        return root


class Element(Record):
    pass


class Attribute(Record):
    pass


class Text(Record):
    pass


class EndElementRecord(Element):
    type = 0x01


class CommentRecord(Record):
    type = 0x02
    
    def __init__(self, comment, *args, **kwargs):
        self.comment = comment

    def to_bytes(self):
        """
        >>> CommentRecord('test').to_bytes()
        '\\x02\\x04test'
        """
        string = Utf8String(self.comment)

        return (super(CommentRecord, self).to_bytes() + 
                string.to_bytes())

    def __str__(self):
        """
        >>> str(CommentRecord('test'))
        '<!-- test -->'
        """
        return '<!-- %s -->' % self.comment

    @classmethod
    def parse(cls, fp):
        data = Utf8String.parse(fp).value
        return cls(data)


class ArrayRecord(Record):
    type = 0x03

    datatypes = {
            0xB5 : ('BoolTextWithEndElement', 1, '?'),
            0x8B : ('Int16TextWithEndElement', 2, 'h'),
            0x8D : ('Int32TextWithEndElement', 4, 'i'),
            0x8F : ('Int64TextWithEndElement', 8, 'q'),
            0x91 : ('FloatTextWithEndElement', 4, 'f'),
            0x93 : ('DoubleTextWithEndElement', 8, 'd'),
            0x95 : ('DecimalTextWithEndElement', 16, ''),
            0x97 : ('DateTimeTextWithEndElement', 8, ''),
            0xAF : ('TimeSpanTextWithEndElement', 8, ''),
            0xB1 : ('UuidTextWithEndElement', 16, ''),
            }

    def __init__(self, element, recordtype, data):
        self.element = element
        self.recordtype = recordtype
        self.count = len(data)
        self.data = data

    def to_bytes(self):
        """
        >>> from wcf.records.elements import ShortElementRecord
        >>> ArrayRecord(ShortElementRecord('item'), 0x8D, ['\\x01\\x00\\x00\\x00', '\\x02\\x00\\x00\\x00', '\\x03\\x00\\x00\\x00']).to_bytes()
        '\\x03@\\x04item\\x01\\x8d\\x03\\x01\\x00\\x00\\x00\\x02\\x00\\x00\\x00\\x03\\x00\\x00\\x00'
        """
        bytes = super(ArrayRecord, self).to_bytes()
        bytes += self.element.to_bytes()
        bytes += EndElementRecord().to_bytes()
        bytes += struct.pack('<B', self.recordtype)[0]
        bytes += MultiByteInt31(self.count).to_bytes()
        for data in self.data:
            if type(data) == str:
                bytes += data
            else:
                bytes += data.to_bytes()

        return bytes

    @classmethod
    def parse(cls, fp):
        element = struct.unpack('<B', fp.read(1))[0]
        element = __records__[element].parse(fp)
        recordtype = struct.unpack('<B', fp.read(1))[0]
        count = MultiByteInt31.parse(fp).value
        data = []
        for i in range(count):
            data.append(__records__[recordtype-1].parse(fp))
        return cls(element, recordtype, data)

    def __str__(self):
        """
        >>> from wcf.records.elements import ShortElementRecord
        >>> from wcf.records.text import Int32TextRecord
        >>> str(ArrayRecord(ShortElementRecord('item'), 0x8D, [Int32TextRecord(1),Int32TextRecord(2),Int32TextRecord(3)]))
        '<item >1</item><item >2</item><item >3</item>'
        """
        string = ''
        for data in self.data:
            string += str(self.element)
            string += str(data)
            string += '</%s>' % self.element.name

        return string

Record.add_records((EndElementRecord,
        CommentRecord,
        ArrayRecord,))
