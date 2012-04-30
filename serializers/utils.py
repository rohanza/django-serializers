# -*- coding: utf-8 -*-
from django.utils.datastructures import SortedDict
import csv


try:
    import yaml
except ImportError:
    DjangoSafeDumper = None
    OrderedSafeDumper = None
else:
    # Adapted from http://pyyaml.org/attachment/ticket/161/use_ordered_dict.py
    class DjangoSafeDumper(yaml.SafeDumper):
        def represent_decimal(self, data):
            return self.represent_scalar('tag:yaml.org,2002:str', str(data))

    class OrderedSafeDumper(DjangoSafeDumper):
        def represent_decimal(self, data):
            return self.represent_scalar('tag:yaml.org,2002:str', str(data))

        def represent_mapping(self, tag, mapping, flow_style=None):
            value = []
            node = yaml.MappingNode(tag, value, flow_style=flow_style)
            if self.alias_key is not None:
                self.represented_objects[self.alias_key] = node
            best_style = True
            if hasattr(mapping, 'items'):
                mapping = list(mapping.items())
            for item_key, item_value in mapping:
                node_key = self.represent_data(item_key)
                node_value = self.represent_data(item_value)
                if not (isinstance(node_key, yaml.ScalarNode) and not node_key.style):
                    best_style = False
                if not (isinstance(node_value, yaml.ScalarNode) and not node_value.style):
                    best_style = False
                value.append((node_key, node_value))
            if flow_style is None:
                if self.default_flow_style is not None:
                    node.flow_style = self.default_flow_style
                else:
                    node.flow_style = best_style
            return node

    OrderedSafeDumper.add_representer(SortedDict,
            yaml.representer.SafeRepresenter.represent_dict)


class DictWriter(csv.DictWriter):
    """
    >>> from cStringIO import StringIO
    >>> f = StringIO()
    >>> w = DictWriter(f, ['a', 'b'], restval=u'î')
    >>> w.writerow({'a':'1'})
    >>> w.writerow({'a':'1', 'b':u'ø'})
    >>> w.writerow({'a':u'é'})
    >>> f.seek(0)
    >>> r = DictReader(f, fieldnames=['a'], restkey='r')
    >>> r.next() == {'a':u'1', 'r':[u"î"]}
    True
    >>> r.next() == {'a':u'1', 'r':[u"ø"]}
    True
    >>> r.next() == {'a':u'é', 'r':[u"î"]}
    """
    def __init__(self, csvfile, fieldnames, restval='', extrasaction='raise', dialect='excel', encoding='utf-8', *args, **kwds):
        self.fieldnames = fieldnames
        self.encoding = encoding
        self.restval = restval
        self.writer = csv.DictWriter(csvfile, fieldnames, restval, extrasaction, dialect, *args, **kwds)

    def _stringify(self, s, encoding):
        if type(s) == unicode:
            return s.encode(encoding)
        elif isinstance(s, (int, float)):
            pass  # let csv.QUOTE_NONNUMERIC do its thing.
        elif type(s) != str:
            s = str(s)
        return s

    def writerow(self, d):
        for fieldname in self.fieldnames:
            if fieldname in d:
                d[fieldname] = self._stringify(d[fieldname], self.encoding)
            else:
                d[fieldname] = self._stringify(self.restval, self.encoding)
        self.writer.writerow(d)
