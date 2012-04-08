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

* Serializers are declared in a simlar format to `Form` and `Model` declarations.
* Declaration of the structure to serialize into is independant of the encoding 
  eg. json, yaml, xml. that is used to produce the final output.
* Arbitrary python objects may be serialized using the `Serializer` class,
  Model instances and querysets may be serialized using the `ModelSerializer` class.

django-serializers intentionally does not address deserialization, as it is
out of scope.

Serializer options
==================

Serializer options may be specified in the class definition, on the `Meta`
inner class, or set when instatiating the `Serializer` object.

For example, using the `Meta` inner class:

    class PersonSerializer(Serializer):
        class Meta:
            fields = ('full_name', 'age')

    PersonSerializer().serialize(person)

And the same, using arguments when instantiating the serializer.

    person_serializer = Serializer(fields=('full_name', 'age'))
    person_serializer.serialize(person)


include
-------

A list of field names that should be included in the output.  This could
include properties, class attributes, or any other attribute on the object that
would not otherwise be serialized.
Any FieldSerializers defined on the class will automatically be added to the
list of included fields.

For example:

    class Person(object):
        def __init__(self, first_name, last_name, age, **kwargs):
            self.first_name = first_name
            self.last_name = last_name
            self.age = age

        @property
        def full_name(self):
            return self.first_name + ' ' + self.last_name

    class CustomSerializer(Serializer):
        class Meta:
            include = ('full_name',)

    CustomSerializer().serialize(Person('john', 'doe', 42))
    {
        'full_name': 'john doe',
        'first_name': 'john',
        'last_name': 'doe',
        'age': 42
    }

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

For example:

    class CustomSerializer(Serializer):
        full_name = FieldSerializer(label='Full name')
        age = FieldSerializer(label='Age')
        class Meta:
            fields = ('full_name', 'age')

    CustomSerializer().serialize(Person('john', 'doe', 42))
    {
        'Full name': 'john doe',
        'Age': 42
    }

serialize
---------

Provides an simple way to specify the serialization function for a field.
`serialize` should be a function that takes a single argument and returns
the serialized output.

TODO
====

* Depth
* Recursion
* Cyclical serialization declarations

Installation
============

Install using pip:

    pip install django-serializers

Running the tests
=================

If you have cloned the git repo you can run the tests directly, otherwise
you'll need to add the 'serialize' app to an existing project:

    ./manage.py test

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
