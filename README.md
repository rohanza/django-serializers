Django Serializers
==================

**Customizable Serialization for Django.**

**Author:** Tom Christie, [Follow me on Twitter][1].

Overview
========

django-serializers provides flexible serialization of objects, models and
querysets.

It is intended to be a potential replacement for the current, inflexible
serialization.  It should be able to support the current `dumpdata` format,
whilst also being easy to override and customise.

Serializers are declared in a simlar format to `Form` and `Model` declarations,
with an inner `Meta` class providing general options, and optionally with a set of `Field` classes being declaring inside the `Serializer` class.

The `Serializer` class itself also implements the `Field` interface, meaning we can represent serialization of nested instances in various different ways. 

Features:

* Supports serialization of arbitrary python objects using the `Serializer` class.
* Supports serialization of models and querysets using `ModelSerializer`.
* Supports serialization to the existing dumpdata format, using `DumpDataSerializer`.
* Supports flat serialization, and nested serialization (to arbitrary depth), and handles recursive relationships.
* Allows for both implicit fields, which are determined at the point of serialization, and explicit fields, which are declared on the serializer class.
* The declaration of the serialization structure is handled independantly of the final encoding used (eg 'json', 'xml' etc…).  This is desirable for eg. APIs which want to support a given dataset being output to a number of different formats.
* Currently supports 'json', 'yaml', 'xml', 'csv'.
* Supports both ordered fields for readablity, and unordered fields for speed.
* Supports both fields that corrospond to Django model fields, and fields that corrospond to other attributes, such as `get_absolute_url`.
* Hooks throughout to allow for complete customization.  Eg. Writing key names using javascript style camel casing.
* Simple, clean API.
* Comprehensive test suite.

Still to do:

* Add natural key support to DumpDataSerializer.
* Add hooks to control which types of model field get serialized by default.  (eg base fields, m2m fields etc…)
* Ensure DumpDataSerializer only serializes base fields, not inherited fields.  (And vice-versa for ModelSerializer)
* Add simple hooks for which field classes should be used by default.  (Eg `flat_field=`, `nested_field=` attributes in `Serializer.Meta`)
* Tests for non-numeric FKs, and FKs with a custom db implementation.
* Tests for many2many FKs with a 'through' model.
* Consider ordering by natural key dependancies for DumpDataSerializer.  
* `django-serializers` currently does not address deserialization.  Replacing
the existing `loaddata` deserialization with a more flexible deserialization
API is considered out of scope, until the serialization API has first been adequatly addressed.
* `django-serializers` current does not provide an API that is backwards compatible
with the existing `dumpdata` serializers.  Need to consider if this is a requirement.  Eg. would this be a replacement to the existing serializers, or an addition to them?
* The base `Field` instances need to be copied on `Serializer` instatiation.  Right now there's some shared state that needs to disappear.
* dumpdata `xml` support is incomplete - needs to include the field types.  This metadata needs to be stored by the serializer on the keys of it's output, and ignored by 'jsonn' and 'yaml'.
* I'd like to add `nested.field` syntax to the `include`, `exclude` and `field` argument, to allow quick declarations of nested representations.
* Add `nested.field` syntax to the `source` argument, to allow quick declarations of serializing nested elements into a flat output structure.
* source='*' should have the effect of passing through `fields`, `include`, `exclude` to the child field, instead of applying to the parent serializer, so eg. DumpDataSerializer will recognise that those arguments apply to the `fields:` level, rather than referring to what should be included at the root level.
* streaming output, rather than loading all the data into memory.
* Better `csv` format.  (Eg nested fields)
* Respect `serialize` property on model fields.


Installation
============

Install using pip:

    pip install django-serializers

Optionally, if you want to include the `django-serializer` tests in your
project, add `serializers` to your `INSTALLED_APPS` setting:

    INSTALLED_APPS = (
        ...
        'seriliazers',
    )

Note that if you have cloned the git repo you can run the tests directly, with
the provided `manage.py` file:

    manage.py test

Examples
========

We'll use the following example class to show some simple examples
of serialization:

    class Person(object):
        def __init__(self, first_name, last_name, age):
            self.first_name = first_name
            self.last_name = last_name
            self.age = age

        @property
        def full_name(self):
            return self.first_name + ' ' + self.last_name

You can serialize arbitrary objects using the `Serializer` class.  Objects are
serialized into dictionaries, containing key value pairs of any non-private
instance attributes on the object:

    >>> from serializers import Serializer
    >>> person = Person('john', 'doe', 42)
    >>> serializer = Serializer()
    >>> print serializer.encode(person, 'json', indent=4)
    {
        'first_name': 'john',
        'last_name': 'doe',
        'age': 42
    }

Let's say we only want to include some specific fields.  We can do so either by
setting those fields when we instantiate the `Serializer`...

    >>> serializer = Serializer(fields=('first_name', 'age'))
    >>> print serializer.encode(person, 'json', indent=4)
    {
        'first_name': 'john',
        'age': 42
    }

...Or by defining a custom `Serializer` class:

    >>> class PersonSerializer(Serializer):
    >>>     class Meta:
    >>>         fields = ('first_name', 'age')
    >>>
    >>> print PersonSerializer().encode(person, 'json', indent=4)
    {
        'first_name': 'john',
        'age': 42
    }

We can also include additional attributes on the object to be serialized, or
exclude existing attributes:

    >>> class PersonSerializer(Serializer):
    >>>     class Meta:
    >>>         exclude = ('first_name', 'last_name')
    >>>         include = 'full_name'
    >>>
    >>> print PersonSerializer().encode(person, 'json', indent=4)
    {
        'full_name': 'john doe',
        'age': 42
    }

To explicitly define how the object fields should be serialized, we declare those fields on the serializer class:

    >>> class PersonSerializer(Serializer):
    >>>    first_name = Field(label='First name')
    >>>    last_name = Field(label='Last name')
    >>>
    >>> print PersonSerializer().encode(person, 'json', indent=4)
    {
        'First name': 'john',
        'Last name': 'doe'
    }

We can also define new types of field and control how they are serialized:

    >>> class ClassNameField(Field):
    >>>     def serialize(self, obj)
    >>>         return obj.__class__.__name__
    >>>
    >>>     def get_field_value(self, obj, field_name):
    >>>         return obj
    >>>
    >>> class ObjectSerializer(Serializer):
    >>>     class_name = ClassNameField(label='class')
    >>>     fields = Serializer(source='*')
    >>>
    >>> print ObjectSerializer().encode(person, 'json', indent=4)
    {
        'class': 'Person',
        'fields': {
            'first_name': 'john',
            'last_name': 'doe',
            'age': 42
        }
    }

django-serializers also handles nested serialization of objects:

    >>> fred = Person('fred', 'bloggs', 41)
    >>> emily = Person('emily', 'doe', 37)
    >>> jane = Person('jane', 'doe', 44, partner=fred)
    >>> john = Person('john', 'doe', 42, siblings=[jane, emily])
    >>> Serializer().serialize(john)
    {
        'first_name': 'john',
        'last_name': 'doe',
        'age': 42,
        'siblings': [
            {
                'first_name': 'jane',
                'last_name': 'doe',
                'age': 44,
                'partner': {
                    'first_name': 'fred',
                    'last_name': 'bloggs',
                    'age': 41,
                }
            },
            {
                'first_name': 'emily',
                'last_name': 'doe',
                'age': 37,
            }
        ]
    }

And handles flat serialization of objects:

    >>> Serializer(depth=0).serialize(john)
    {
        'first_name': 'john',
        'last_name': 'doe',
        'age': 42,
        'siblings': [
            'jane doe',
            'emily doe'
        ]
    }

Similarly model and queryset serialization is supported, and handles either flat or nested serialization of foreign keys, many to many relationships, and one to one relationships, plus reverse relationships:

    >>> class User(models.Model):
    >>>     email = models.EmailField()
    >>>
    >>> class Profile(models.Model):
    >>>     user = models.OneToOneField(User, related_name='profile')
    >>>     country_of_birth = models.CharField(max_length=100)
    >>>     date_of_birth = models.DateTimeField()
    >>>
    >>> ModelSerializer().serialize(profile)
    {
        'id': 1,
        'user': {
            'id': 1,
            'email': 'joe@example.com'
        },
        'country_of_birth': 'UK',
        'date_of_birth': datetime.datetime(day=5, month=4, year=1979)
    }

The existing dumpdata format is (mostly) replicated, and gives a good example of how to declare custom serialization styles:

    >>> class DumpDataSerializer(ModelSerializer):
    >>>     pk = ModelField()
    >>>     model = ModelNameField()
    >>>     fields = ModelSerializer(source='*', exclude='id', depth=0)

Field options
=============

label
-----

If `label` is set it determines the name that should be used as the
key when serializing the field.

source
------

If `source` is set it determines which attribute of the object to
retrieve when serializing the field.

A value of '*' is a special case, which denotes the entire object should be
passed through and serialized by this field.

For example, the following serializer:

    class ClassNameField(Field):
        def serialize(self, obj):
            return obj.__class__.__name__

        def get_field_value(self, obj, field_name):
            return obj

    class CustomSerializer(Serializer):
        class_name = ClassNameField(label='class')
        fields = Serializer(source='*', depth=0)

Would serialize objects into a structure like this:

    {
        "class": "Person"
        "fields": {
            "age": 23, 
            "name": "Frank"
            ...
        }, 
    }

serialize
---------

Provides a simple way to override the default serialization function.
`serialize` should be a function that takes a single argument and returns
the serialized output.

For example:

    class CustomSerializer(Serializer):
        email = Field(serialize=lamda obj: obj.lower())  # Force email fields to lowercase.
        ...


Serializer options
==================

Serializer options may be specified in the class definition, on the `Meta`
inner class, or set when instatiating the `Serializer` object.

For example, using the `Meta` inner class:

    class PersonSerializer(Serializer):
        class Meta:
            fields = ('full_name', 'age')

    serializer = PersonSerializer()

And the same, using arguments when instantiating the serializer.

    serializer = Serializer(fields=('full_name', 'age'))

The serializer class is a subclass of `Field`, so also supports the `Field` API.

include
-------

A list of field names that should be included in the output.  This could
include properties, class attributes, or any other attribute on the object that
would not otherwise be serialized.

exclude
-------

A list of field names that should not be included in the output.

fields
------

The complete list of field names that should be serialized.  If provided
`fields` will override `include` and `exclude`.

depth
-----

The `depth` argument controls how nested objects should be serialized.
The default is `None`, which means serialization should descend into nested
objects.

If `depth` is set to an integer value, serialization will descend that many
levels into nested objects, before starting serialize nested models with a
"flat" value.

For example, setting `depth=0` ensures that only the fields of the top level
object will be serialized, and any nested objects will simply be serialized
as simple string representations of those objects.

include_default_fields
----------------------

The default set of fields on an object are the attributes that will be
serialized if no serializer fields are explicitly specified on the class.

When serializer fields *are* explicitly specified, these will normally be
used instead of the default fields.

If `include_default_fields` is set to `True`, then *both* the explicitly
specified serializer fields *and* the object's default fields will be used.

For example, in this case, only the 'full_name' field will be serialized:

    class CustomSerializer(Serializer):
        full_name = Serializer(label='Full name')

In this case, both the 'full_name' field, and any instance attributes on the
object will be serialized:

    class CustomSerializer(Serializer):
        full_name = Serializer(label='Full name')
        
        class Meta:
            include_default_fields = True

preserve_field_ordering
-----------------------

If set to `True`, objects will be serialized using ordered dictionaries,
which preserve the ordering that the fields are declared in.

flat_field
----------

The class that should be used for serializing flat fields.  (ie. Once the
specified `depth` has been reached.)  Default is `Field`.

nested_field
------------

The class that should be used for serializing nested fields.  (ie Before the
specified `depth` has been reached.)  Default is `None`, which indicate that
the serializer should use another instance of it's own class.

recursive_field
---------------

The class that should be used for serializing fields when a recursion occurs.
Default is `None`, which indicates that it should fall back to whatever is
set for `flat_field`.

Field methods
=============

serialize(self, obj)
--------------------

Returns a native python datatype representing the given object.

If you are writing a custom field, overiding `serialize()` will let
you customise how the output is generated.

get_field_value(self, obj, field_name)
--------------------------------------

Determines how the attribute that should be serialized is retrieved from the object.

If you are writing a custom `Field`and need to control exactly which attributes
of the object are serialized, you will need to override this method.  (For example if you are writing a`datetime` serializer which combines information
from two seperate `date` and `time` attributes on an object.)

serialize_field(self, obj, field_name)
--------------------------------------

The main entry point into field serialization, which handles calling `get_field_value` and `serialize`, and ensures the `source` arguemnt is used to determine which attribute to fetch from the object.

You won't typically need to override this method.


Serializer methods
==================

encode(self, obj, format=None, **opts)
--------------------------------------

The main entry point into serializers.

`format` should be a string representing the desired encoding.  Valid choices
are `json`, `yaml` and `xml`.  If format is left as `None`, the object will be
serialized into a python object in the desired structure, but will not be
rendered into a final output format.

`opts` may be any additional options specific to the encoding.

Internally serialization is a two-step process.  The first step calls the
`serialize()` method, which serializes the object into the desired structure,
limited to a set of primative python datatypes.  The second step calls the
`render()` method, which renders that structure into the final output string
or bytestream.

get_field_key(self, obj, field_name, field)
--------------------------------------------------

Returns a native python object representing the key for the given field name.
By default this will be the serializer's `label` if it has one specified,
or the `field_name` string otherwise.

get_default_field_names(self, obj)
----------------------------------

Return the default set of field names that should be serialized for an object.
If a serializer has no `Serializer` classes declared as fields, then this will be the set of
fields names that will be serialized.

get_default_field_serializer(self, obj, field_name)
---------------------------------------------------

Returns the Field or Serializer instance that should be used for a field if there was no explicitly declared `Field` for the given `field_name`.  A return value of `None` indicates that the existing class should be used to serialize the field, resulting in nested serialization.

By default this method will call one of `get_flat_serializer()`, `get_recursive_serializer()` or `get_nested_serializer()`.

render(self, data, format, **opts)
----------------------------------

Performs the final part of the serialization, translating a simple python
object into the output format.

The `data` argument is provided by the return value of the
`serialize()` method.

`format` and `**opts` are the arguments as passed through by the
`encode()` method.


Changelog
=========

0.3.2
-----

* Fix csv for python 2.6

0.3.1
-----

* Fix import error when yaml not installed

0.3.0
-----

* Initial support for CSV.

0.2.0
-----

* First proper release. Properly working model relationships etc…

0.1.0
-----

* Initial release

License
=======

Copyright © Tom Christie.

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.
Redistributions in binary form must reproduce the above copyright notice, this
list of conditions and the following disclaimer in the documentation and/or
other materials provided with the distribution.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

[1]: http://twitter.com/_tomchristie
