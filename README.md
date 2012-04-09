Django Serializers
==================

**Customizable Serialization for Django.**

**Author:** Tom Christie, [@_tomchristie][1].

Overview
========

django-serializers provides flexible serialization of objects, models and
querysets.

It is intended to be a potential replacement for the current, inflexible
serialization.  It should be able to support the current `dumpdata` format,
whilst also being easy to override and customise.

Serializers are declared in a simlar format to `Form` and `Model` declarations,
with an inner `Meta` class providing general options, and individual fields being specified by declaring `FieldSerializer` instances on the class.

Arbitrary python objects are serialized using the general `Serializer` class, model instances and querysets may be serialized using the `ModelSerializer` class.

The declaration of the serialization structure is independant of the encoding 
eg. 'json', 'yaml', 'xml'. that is used to produce the final output.  This is desirable, as it means you can declare the serialization structure, without being bound to a given output format.

`django-serializers` intentionally does not address deserialization.  Replacing the existing `loaddata` deserialization with a more flexible deserialization API is considered out of scope.

`django-serializers` also does not provide an API that is backwards compatible with the existing `dumpdata` serializers.  This may happen at some point in the future. 

Installation
============

Install using pip:

    pip install django-serializers

Optionally, if you want to include the `django-serializer` tests in your project, add `serializers` to your `INSTALLED_APPS` setting:

    INSTALLED_APPS = (
    	...
    	'seriliazers',
    )

Note that if you have cloned the git repo you can run the tests directly, with the provided `manage.py` file:

	manage.py test

Quick Start
===========

We'll use the following example class to show some simple example of serialization:

    class Person(object):
        def __init__(self, first_name, last_name, age):
            self.first_name = first_name
            self.last_name = last_name
            self.age = age

        @property
        def full_name(self):
            return self.first_name + ' ' + self.last_name

You can serialize arbitrary objects using the `Serializer` class.  Objects are serialized into dictionaries, containing key value pairs of any non-private instance attributes on the object:

    >>> from serializers import Serializer
    >>> person = Person('john', 'doe', 42)
    >>> serializer = Serializer()
    >>> serializer.encode(person, 'json', indent=4)
    {
        'first_name': 'john',
        'last_name': 'doe',
        'age': 42
    }
    
Let's say we only want to include some specific fields.  We can do so either by setting those fields when we instantiate the `Serializer`...

    >>> serializer = Serializer(fields=('first_name', 'age'))
    >>> serializer.encode(person, 'json', indent=4)
    {
        'first_name': 'john',
        'age': 42
    }

...Or by defining a custom `Serializer` class:

    >>> class PersonSerializer(Serializer):
    >>>     class Meta:
    >>>         fields = ('first_name', 'age')
    >>>
    >>> PersonSerializer().encode(person, 'json', indent=4)
    {
        'first_name': 'john',
        'age': 42
    }

We can also include additional attributes on the object to be serialized:

    >>> class PersonSerializer(Serializer):
    >>>     class Meta:
    >>>         exclude = ('first_name', 'last_name')
    >>>         include = 'full_name'
    >>>
    >>> PersonSerializer().encode(person, 'json', indent=4)
    {
        'full_name': 'john doe',
        'age': 42
    }

Redefine how existing fields should be serialized:

    >>> class PersonSerializer(Serializer):
    >>>    first_name = FieldSerializer(label='First name')
    >>>    last_name = FieldSerializer(label='Last name')
    >>>    class Meta:
    >>>        fields = ('first_name', 'last_name')
    >>>
    >>> PersonSerializer().encode(person, 'json', indent=4)
    {
        'First name': 'john',
        'Last name': 'doe'
    }

Add new fields to be serialized:

    >>> class PersonSerializer(Serializer):
    >>>    proper_name = FieldSerializer(serialize=lambda obj: 'Mr' + obj.proper())
    >>>    class Meta:
    >>>        fields = ('proper_name', 'age')
    >>>
    >>> PersonSerializer().encode(person, 'json', indent=4)
    {
        'proper_name': 'Mr John Doe',
        'age': 42
    }

Or define new field classes, which we can reuse in different serializers:

    >>> class ClassNameField(FieldSerializer):
    >>>     def serialize_field_value(self, obj, field_name)
    >>>         return obj.__class__.__name__
    >>>
    >>> class ObjectSerializer(Serializer):
    >>>     class_name = ClassNameField(label='class')
    >>>     fields = Serializer()
    >>>
    >>> ObjectSerializer().encode(person, 'json', indent=4)
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
Any FieldSerializers defined on the class will automatically be added to the
list of included fields.

exclude
-------

A list of field names that should not be included in the output.

fields
------

The complete list of field names that should be serialized.  If provided
`fields` will override `include` and `exclude`.

label
-----

The `label` option is only relevant if the serializer is used as a field
serializer.  If `label` is set it is used determines the as the key when
serializing the field.

serialize
---------

Provides an simple way to specify the serialization function for a field.
`serialize` should be a function that takes a single argument and returns
the serialized output.

FieldSerializer declarations
============================

Serialization of individual fields may be explicitly controlled by defining `FieldSerializer` instances on the `Serializer` class.

For instance:

    class CustomSerializer(object):
        full_name = FieldSerializer(label='Full name')
        age = FieldSerializer(label='Age')

        class Meta:
            fields = ('full_name', 'age')

The `Serializer` class itself provides the `FieldSerializer` interface, so may be used in the same way:

    class CustomSerializer(object):
        full_name = FieldSerializer(label='Full name')
        details = Serializer()

        class Meta:
            fields = ('full_name', 'details')

Any declared `FieldSerializer` classes are automatically added to the list of attributes that should be included on the output.  (See also the `include` option.)  By default the full list of fields to serialize will be the list of all the instance attributes set on the model, plus all the explictly declared `FieldSerializer` classes.


Serializer methods
==================

encode(obj, format=None, **opts)
--------------------------------

The main entry point into serializers.

`format` should be a string representing the desired encoding.  Valid choices are `json`, `yaml` and `xml`.  If format is left as `None`, the object will be serialized into a python object in the desired structure, but will not be rendered into a final output format.

`opts` may be any additional options specific to the encoding.

Internally serialization is a two-step process.  The first step serializes the object into the desired structure, limited to a set of primative python datatypes.  The second step renders that structure into the final output string or bytestream.

serialize(obj)
--------------

Returns a native python datatype representing the given object.

If you are writing a custom field serializer, overiding `serialize()` will let you customise how the output is generated.

serialize_field_name(obj, field_name)
-------------------------------------

Returns a native python object representing the key for the given field name.
By default this will be the serializer's `label` if it has one specified,
or the `field_name` string otherwise.


serialize_field_value(obj, field_name)
--------------------------------------

Returns a native python datatype representing the value for the given field name.

For a `FieldSerializer` this will default to calling `serialize()` on the attribute given by `getattr(obj, fieldname)`, which means it will serialize only the given field.

For a `Serializer` this will default to call `serialize()` on the entire object.

If you are writing a custom `FieldSerializer` and need to control exactly which attributes of the object are serialized, you will need to override `serialize_field_value()`.  (For example if you are writing a `datetime` serializer which combines information from two seperate `date` and `time` attributes on an object.)

get_field_names(obj)
--------------------

Return the set of field names that should be serialized for an object.
By default this method takes into account the set of fields returned by `get_default_field_names()`, plus any explicitly declared `FieldSerializer` classes, as well as the `include`, `exclude`, and `fields` options.

get_default_field_names(obj)
----------------------------

Return the set of default field names that should be serialized for an object.
If a serializer has no `FieldSerializer` classes declared, and nothing set for the `include`, `exclude` and `fields` options, then this will be the 

get_field_serializer(obj, field_name)
-------------------------------------

Returns the serializer instance that should be used for a field.
By default this checks to see if there is an explicitly defined `FieldSerializer`
for the given name, and if not, falls back to `get_default_field_serializer`.

get_default_field_serializer(obj, field_name)
---------------------------------------------

Returns the serializer instance that should be used for a field if there was no explicitly declared `FieldSerializer` class for the given `field_name`.

render(data, format, **opts)
----------------------------

Performs the final part of the serialization, translating a simple python object into the output format.

The `data` argument is provided by the return value of the `serialize()` method.

`format` and `**opts` are the arguments as passed through by the `encode()` method.

TODO
====

* Depth
* Recursion
* Cyclical serialization declarations


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
