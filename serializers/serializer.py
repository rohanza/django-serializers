from decimal import Decimal
from django.utils.datastructures import SortedDict
import copy
import datetime
import inspect
import types
from serializers.renderers import (
    JSONRenderer,
    YAMLRenderer,
    XMLRenderer,
    CSVRenderer,
    DumpDataXMLRenderer
)
from serializers.fields import *
from serializers.utils import DictWithMetadata, SortedDictWithMetadata


def _remove_items(seq, exclude):
    """
    Remove duplicates and items in 'exclude' from list (preserving order).
    """
    seen = set()
    result = []
    for item in seq:
        if (item in seen) or (item in exclude):
            continue
        seen.add(item)
        result.append(item)
    return result


def _get_declared_fields(bases, attrs):
    """
    Create a list of serializer field instances from the passed in 'attrs',
    plus any similar fields on the base classes (in 'bases').

    Note that all fields from the base classes are used.
    """
    fields = [(field_name, attrs.pop(field_name))
              for field_name, obj in attrs.items()
              if isinstance(obj, Field)]
    fields.sort(key=lambda x: x[1].creation_counter)

    # If this class is subclassing another Serializer, add that Serializer's
    # fields.  Note that we loop over the bases in *reverse*. This is necessary
    # in order to the correct order of fields.
    for base in bases[::-1]:
        if hasattr(base, 'base_fields'):
            fields = base.base_fields.items() + fields

    return SortedDict(fields)


def _get_option(name, kwargs, meta, default):
    return kwargs.get(name, getattr(meta, name, default))


class SerializerOptions(object):
    def __init__(self, meta, **kwargs):
        self.depth = _get_option('depth', kwargs, meta, None)
        self.include = _get_option('include', kwargs, meta, ())
        self.exclude = _get_option('exclude', kwargs, meta, ())
        self.fields = _get_option('fields', kwargs, meta, ())
        self.include_default_fields = _get_option(
            'include_default_fields', kwargs, meta, False
        )
        self.flat_field = _get_option('flat_field', kwargs, meta, Field)
        self.recursive_field = _get_option('recursive_field', kwargs, meta, None)
        self.nested_field = _get_option('nested_field', kwargs, meta, None)


class ModelSerializerOptions(SerializerOptions):
    def __init__(self, meta, **kwargs):
        super(ModelSerializerOptions, self).__init__(meta, **kwargs)
        self.model_field_types = _get_option('model_field_types', kwargs, meta, None)
        self.model_field = _get_option('model_field', kwargs, meta, ModelField)
        self.related_field = _get_option('related_field', kwargs, meta, PrimaryKeyRelatedField)


class SerializerMetaclass(type):
    def __new__(cls, name, bases, attrs):
        attrs['base_fields'] = _get_declared_fields(bases, attrs)
        return super(SerializerMetaclass, cls).__new__(cls, name, bases, attrs)


class BaseSerializer(Field):
    class Meta(object):
        pass

    renderer_classes = {
        'xml': XMLRenderer,
        'json': JSONRenderer,
        'yaml': YAMLRenderer,
        'csv': CSVRenderer,
    }

    options_class = SerializerOptions
    _use_sorted_dict = True

    def __init__(self, **kwargs):
        source = kwargs.get('source', None)
        label = kwargs.get('label', None)
        serialize = kwargs.get('serialize', None)
        super(BaseSerializer, self).__init__(source=source, label=label, serialize=serialize)

        self.opts = self.options_class(self.Meta, **kwargs)
        self.stack = []
        self.fields = SortedDict((key, copy.copy(field))
                           for key, field in self.base_fields.items())

    def get_flat_serializer(self, obj, field_name):
        return self.opts.flat_field()

    def get_recursive_serializer(self, obj, field_name):
        if self.opts.recursive_field:
            return self.opts.recursive_field()
        return self.get_flat_serializer(obj, field_name)

    def get_nested_serializer(self, obj, field_name):
        return (self.opts.nested_field or self.__class__)()

    def _is_protected_type(self, obj):
        """
        True if the object is a native datatype that does not need to
        be serialized further.
        """
        return isinstance(obj, (
            types.NoneType,
            int, long,
            datetime.datetime, datetime.date, datetime.time,
            float, Decimal,
            basestring)
        )

    def _is_simple_callable(self, obj):
        """
        True if the object is a callable that takes no arguments.
        """
        return (
            (inspect.isfunction(obj) and not inspect.getargspec(obj)[0]) or
            (inspect.ismethod(obj) and len(inspect.getargspec(obj)[0]) <= 1)
        )

    def _get_field_names(self, obj):
        """
        Given an object, return the set of field names to serialize.
        """
        opts = self.opts
        if opts.fields:
            return opts.fields
        else:
            fields = self.fields.keys()
            if opts.include_default_fields or not self.fields:
                fields += self.get_default_field_names(obj)
            fields += list(opts.include)
            return _remove_items(fields, opts.exclude)

    def _get_field_serializer(self, obj, field_name):
        """
        Given an object and a field name, return the serializer instance that
        should be used to serialize that field.
        """
        try:
            return self.fields[field_name]
        except KeyError:
            return self._get_default_field_serializer(obj, field_name)

    def _get_default_field_serializer(self, obj, field_name):
        """
        If a field does not have an explicitly declared serializer, return the
        default serializer instance that should be used for that field.
        """
        if self.opts.depth is not None and self.opts.depth <= 0:
            return self.get_flat_serializer(obj, field_name)
        return self.get_nested_serializer(obj, field_name)

    def get_default_field_names(self, obj):
        """
        Given an object, return the default set of field names to serialize.
        This is what would be serialized if no explicit `Serializer` fields
        are declared.
        """
        return sorted([key for key in obj.__dict__.keys()
                       if not(key.startswith('_'))])

    def get_field_key(self, obj, field_name, field):
        """
        Return the key that should be used for a given field.
        """
        if getattr(field, 'label', None):
            return field.label
        return field_name

    def _serialize_field(self, obj, field_name, parent):
        """
        Same behaviour as usual Field, except that we need to keep track
        of state so that we can deal with handling maximum depth and recursion.
        """
        self.parent = parent
        self.orig_obj = obj
        self.orig_field_name = field_name

        self.stack = parent.stack[:]
        if parent.opts.depth is not None:
            self.opts.depth = parent.opts.depth - 1

        return super(BaseSerializer, self)._serialize_field(obj, field_name, parent)

    def serialize_object(self, obj):
        if self.source != '*' and obj in self.stack:
            serializer = self.get_recursive_serializer(self.orig_obj,
                                                       self.orig_field_name)
            return serializer._serialize_field(self.orig_obj,
                                               self.orig_field_name,
                                               self)
        self.stack.append(obj)

        if self._use_sorted_dict:
            ret = SortedDictWithMetadata()
        else:
            ret = DictWithMetadata()

        for field_name in self._get_field_names(obj):
            field = self._get_field_serializer(obj, field_name)
            key = self.get_field_key(obj, field_name, field)
            value = field._serialize_field(obj, field_name, self)
            ret.set_with_metadata(key, value, field)
        return ret

    def serialize(self, obj):
        if self._is_protected_type(obj):
            return obj
        elif self._is_simple_callable(obj):
            return self.serialize(obj())
        elif hasattr(obj, '__iter__'):
            return [self.serialize(item) for item in obj]
        return self.serialize_object(obj)

    def encode(self, obj, format=None, **opts):
        data = self.serialize(obj)
        if format:
            return self.render(data, format, **opts)
        return data

    def render(self, data, format, **opts):
        renderer = self.renderer_classes[format]()
        return renderer.render(data, **opts)


class Serializer(BaseSerializer):
    __metaclass__ = SerializerMetaclass


class ModelSerializer(Serializer):
    """
    A serializer that deals with model instances and querysets.
    """
    options_class = ModelSerializerOptions

    class Meta:
        related_field = PrimaryKeyRelatedField
        model_field_types = ('pk', 'fields', 'many_to_many')

    def get_default_field_names(self, obj):
        fields = []
        concrete_model = obj._meta.concrete_model

        for field_type in self.opts.model_field_types:
            if field_type == 'pk':
                # Add pk field, descending into inherited pk if needed
                pk_field = concrete_model._meta.pk
                while pk_field.rel:
                    pk_field = pk_field.rel.to._meta.pk
                fields.append(pk_field)
            else:
                # Add any non-pk field types
                fields.extend([
                    field for field in
                    getattr(concrete_model._meta, field_type)
                    if field.serialize
                ])
        return [field.name for field in fields]

    def get_related_serializer(self, obj, field_name):
        return self.opts.related_field()

    def get_flat_serializer(self, obj, field_name):
        try:
            field = obj._meta.get_field_by_name(field_name)[0]
            if isinstance(field, RelatedObject) or field.rel:
                return self.get_related_serializer(obj, field_name)
            return self.opts.model_field()
        except FieldDoesNotExist:
            return self.opts.flat_field()

    def serialize(self, obj):
        if self._is_protected_type(obj):
            return obj
        elif self._is_simple_callable(obj):
            return self.serialize(obj())
        elif hasattr(obj, 'all') and self._is_simple_callable(obj.all):
            return [self.serialize(item) for item in obj.all()]
        elif hasattr(obj, '__iter__'):
            return [self.serialize(item) for item in obj]
        return self.serialize_object(obj)


class DumpDataFields(ModelSerializer):
    _use_sorted_dict = False

    class Meta:
        depth = 0
        model_field_types = ('local_fields', 'many_to_many')


class DumpDataSerializer(ModelSerializer):
    """
    A serializer that is intended to produce dumpdata formatted structures.
    """
    _use_sorted_dict = False

    renderer_classes = {
        'xml': DumpDataXMLRenderer,
        'json': JSONRenderer,
        'yaml': YAMLRenderer,
    }

    pk = Field()
    model = ModelNameField()
    fields = DumpDataFields(source='*')

    def encode(self, obj, format=None, **opts):
        if opts.get('use_natural_keys', None):
            self.fields['fields'] = DumpDataFields(source='*', related_field=NaturalKeyRelatedField)
        return super(DumpDataSerializer, self).encode(obj, format, **opts)
