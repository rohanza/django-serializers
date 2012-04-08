from django.test import TestCase
from serializer import Serializer, FieldSerializer


class ExampleObject(object):
    """
    An example class for testing basic serialization.
    """
    def __init__(self):
        self.a = 1
        self.b = 'foo'
        self.c = True
        self._hidden = 'other'


class Person(object):
    """
    An example class for testing serilization of properties and methods.
    """
    CHILD_AGE = 16

    def __init__(self, first_name, last_name, age, **kwargs):
        self.first_name = first_name
        self.last_name = last_name
        self.age = age
        for key, val in kwargs.items():
            setattr(self, key, val)

    @property
    def full_name(self):
        return self.first_name + ' ' + self.last_name

    def is_child(self):
        return self.age < self.CHILD_AGE


class BasicSerializerTests(TestCase):
    def setUp(self):
        self.obj = ExampleObject()

    def test_serialize_basic_object(self):
        """
        Objects are seriaized by converting into dictionaries.
        """
        expected = {
            'a': 1,
            'b': 'foo',
            'c': True
        }

        self.assertEquals(Serializer().serialize(self.obj), expected)

    def test_serialize_fields(self):
        """
        Setting 'Meta.fields' specifies exactly which fields to serialize.
        """
        class CustomSerializer(Serializer):
            class Meta:
                fields = ('a', 'c')

        expected = {
            'a': 1,
            'c': True
        }

        self.assertEquals(CustomSerializer().serialize(self.obj), expected)

    def test_serialize_exclude(self):
        """
        Setting 'Meta.exclude' causes a field to be excluded.
        """
        class CustomSerializer(Serializer):
            class Meta:
                exclude = ('b',)

        expected = {
            'a': 1,
            'c': True
        }

        self.assertEquals(CustomSerializer().serialize(self.obj), expected)

    def test_serialize_include(self):
        """
        Setting 'Meta.include' causes a field to be included.
        """
        class CustomSerializer(Serializer):
            class Meta:
                include = ('_hidden',)

        expected = {
            'a': 1,
            'b': 'foo',
            'c': True,
            '_hidden': 'other'
        }

        self.assertEquals(CustomSerializer().serialize(self.obj), expected)

    def test_serialize_include_and_exclude(self):
        """
        Both 'Meta.include' and 'Meta.exclude' may be set.
        """
        class CustomSerializer(Serializer):
            class Meta:
                include = ('_hidden',)
                exclude = ('b',)

        expected = {
            'a': 1,
            'c': True,
            '_hidden': 'other'
        }

        self.assertEquals(CustomSerializer().serialize(self.obj), expected)

    def test_serialize_fields_and_include_and_exclude(self):
        """
        'Meta.fields' overrides both 'Meta.include' and 'Meta.exclude' if set.
        """
        class CustomSerializer(Serializer):
            class Meta:
                include = ('_hidden',)
                exclude = ('b',)
                fields = ('a', 'b')

        expected = {
            'a': 1,
            'b': 'foo'
        }

        self.assertEquals(CustomSerializer().serialize(self.obj), expected)


class SerializeAttributeTests(TestCase):
    """
    Test covering serialization of different types of attributes on objects.
    """
    def setUp(self):
        self.obj = Person('john', 'doe', 42)

    def test_serialization_only_includes_instance_properties(self):
        """
        By default only serialize instance properties, not class properties.
        """
        expected = {
            'first_name': 'john',
            'last_name': 'doe',
            'age': 42
        }

        self.assertEquals(Serializer().serialize(self.obj), expected)

    def test_serialization_can_include_properties(self):
        """
        Object properties can be included as fields.
        """
        class CustomSerializer(Serializer):
            class Meta:
                fields = ('full_name', 'age')

        expected = {
            'full_name': 'john doe',
            'age': 42
        }

        self.assertEquals(CustomSerializer().serialize(self.obj), expected)

    def test_serialization_can_include_no_arg_methods(self):
        """
        Object methods may be included as fields.
        """
        class CustomSerializer(Serializer):
            class Meta:
                fields = ('full_name', 'is_child')

        expected = {
            'full_name': 'john doe',
            'is_child': False
        }

        self.assertEquals(CustomSerializer().serialize(self.obj), expected)


class SerializerFieldTests(TestCase):
    """
    Tests declaring explicit fields on the serializer.
    """

    def setUp(self):
        self.obj = Person('john', 'doe', 42)

    def test_field_label(self):
        """
        A serializer field can take a 'label' argument, which is used as the
        field key instead of the field's property name.
        """
        class CustomSerializer(Serializer):
            full_name = FieldSerializer(label='Full name')
            age = FieldSerializer(label='Age')

            class Meta:
                fields = ('full_name', 'age')

        expected = {
            'Full name': 'john doe',
            'Age': 42
        }

        self.assertEquals(CustomSerializer().serialize(self.obj), expected)

    def test_field_func(self):
        """
        A serializer field can take a 'serialize' argument, which is used to
        serialize the field value.
        """
        class CustomSerializer(Serializer):
            full_name = FieldSerializer(label='Full name',
                                        serialize=lambda name: 'Mr ' + name.title())
            age = FieldSerializer(label='Age')

            class Meta:
                fields = ('full_name', 'age')

        expected = {
            'Full name': 'Mr John Doe',
            'Age': 42
        }

        self.assertEquals(CustomSerializer().serialize(self.obj), expected)

    def test_serializer_as_field(self):
        """
        A regular serializer can be used as a field serializer, in which case
        the complete object will be used when serializing that field.
        """
        class CustomSerializer(Serializer):
            full_name = FieldSerializer(label='Full name')
            details = Serializer(fields=('first_name', 'last_name'), label='Details')

            class Meta:
                fields = ('full_name', 'details')

        expected = {
            'Full name': 'john doe',
            'Details': {
                'first_name': 'john',
                'last_name': 'doe'
            }
        }

        self.assertEquals(CustomSerializer().serialize(self.obj), expected)

    def test_custom_serializer_as_field(self):
        """
        A regular serializer can be used as a field serializer, in which case
        the complete object will be used when serializing that field.
        """
        class DetailsSerializer(Serializer):
            first_name = FieldSerializer(label='First name')
            last_name = FieldSerializer(label='Last name')

            class Meta:
                fields = ('first_name', 'last_name')

        class CustomSerializer(Serializer):
            full_name = FieldSerializer(label='Full name')
            details = DetailsSerializer(label='Details')

            class Meta:
                fields = ('full_name', 'details')

        expected = {
            'Full name': 'john doe',
            'Details': {
                'First name': 'john',
                'Last name': 'doe'
            }
        }

        self.assertEquals(CustomSerializer().serialize(self.obj), expected)


class NestedSerializationTests(TestCase):
    """
    Tests serialization of nested objects.
    """

    def setUp(self):
        sister = Person('jane', 'doe', 44)
        self.obj = Person('john', 'doe', 42, sister=sister)

    def test_nested_serialization(self):
        """
        By default only serialize instance properties, not class properties.
        """
        expected = {
            'first_name': 'john',
            'last_name': 'doe',
            'age': 42,
            'sister': {
                'first_name': 'jane',
                'last_name': 'doe',
                'age': 44,
            }
        }

        self.assertEquals(Serializer().serialize(self.obj), expected)
