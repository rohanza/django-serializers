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
with an inner `Meta` class providing general options, and individual fields
being specified by declaring other, nested `Serializer` instances on the class.

Arbitrary python objects are serialized using the general `Serializer` class,
model instances and querysets may be serialized using the `ModelSerializer` class.

The declaration of the serialization structure is independant of the encoding 
eg. 'json', 'yaml', 'xml'. that is used to produce the final output.  This is
desirable, as it means you can declare the serialization structure, without
being bound to a given output format.

`django-serializers` intentionally does not address deserialization.  Replacing
the existing `loaddata` deserialization with a more flexible deserialization
API is considered out of scope.

`django-serializers` also does not provide an API that is backwards compatible
with the existing `dumpdata` serializers.  This may happen at some point in
the future.

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

Quick Start
===========

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

We can also explicitly define how the object fields should be serialized:

    >>> class PersonSerializer(Serializer):
    >>>    first_name = Serializer(label='First name')
    >>>    last_name = Serializer(label='Last name')
    >>>
    >>> print PersonSerializer().encode(person, 'json', indent=4)
    {
        'First name': 'john',
        'Last name': 'doe'
    }

We can also define new types of field and control how they are serialized:

    >>> class ClassNameField(Serializer):
    >>>     def serialize_field_value(self, obj, field_name)
    >>>         return obj.__class__.__name__
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

**TODO:**

* Outline nested serialization - full and flat fields
* Outline model and queryset serialization

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

label
-----

The `label` option is only relevant if the serializer is used as a serializer
field.  If `label` is set it determines the name that should be used as the
key when serializing the field.

source
------

The `source` option is only relevant if the serializer is used as a serializer
field.  If `source` is set it determines which attribute of the object to
retrieve when serializing the field.

A value of '*' is a special case, which denotes the entire object should be
passed through and serialized by this field.

For example, the following serializer:

    class ClassNameSerializer(Serializer):
        def serialize_field_value(self, obj, field_name):
            return obj.__class__.__name__

    class CustomSerializer(Serializer):
        class_name = ClassNameSerializer(label='class')
        fields = Serializer(source='*')

Would serialize objects into a structure like this:

    {
        "class": "Person"
        "fields": {
            "age": 23, 
            "name": "Frank"
            ...
        }, 
    }

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

serialize
---------

Provides a simple way to override the default serialization function.
`serialize` should be a function that takes a single argument and returns
the serialized output.

For example:

    class CustomSerializer(Serializer):
        email = Serializer(serialize=lamda obj: obj.lower())  # Force email fields to lowercase.
        ...

preserve_field_ordering
-----------------------

If set to `True`, objects will be serialized using ordered dictionaries,
which preserve the ordering that the fields are declared in.


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

serialize(self, obj)
--------------------

Returns a native python datatype representing the given object.

If you are writing a custom serializer field, overiding `serialize()` will let
you customise how the output is generated.

serialize_field_name(self, obj, field_name)
-------------------------------------------

Returns a native python object representing the key for the given field name.
By default this will be the serializer's `label` if it has one specified,
or the `field_name` string otherwise.


serialize_field_value(self, obj, field_name)
--------------------------------------------

Returns a native python datatype representing the value for the given
field name.

This will default to calling `serialize()` on the attribute given by
`getattr(obj, field_name)`, which means it will serialize the given field.

If the `source` argument has been specified, that will be used instead of
the `field_name` argument.

If you are writing a custom `Serializer` for use as a field and need to control
exactly which attributes of the object are serialized, you will need to
override `serialize_field_value()`.  (For example if you are writing a
`datetime` serializer which combines information from two seperate `date` and
`time` attributes on an object.)

get_default_field_names(self, obj)
----------------------------------

Return the default set of field names that should be serialized for an object.
If a serializer has no `Serializer` classes declared as fields, then this will be the set of
fields names that will be serialized.

get_default_field_serializer(self, obj, field_name)
---------------------------------------------------

Returns the serializer instance that should be used for a field if there was no
explicitly declared `Serializer` field for the given `field_name`.

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
