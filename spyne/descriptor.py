
#
# spyne - Copyright (C) Spyne contributors.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
#

import logging
logger = logging.getLogger('spyne')

from spyne import LogicError
from spyne.util import six
from spyne.util import DefaultAttrDict
from spyne.service import ServiceBase
from spyne.const.xml_ns import DEFAULT_NS


class BODY_STYLE_WRAPPED: pass
class BODY_STYLE_EMPTY: pass
class BODY_STYLE_BARE: pass
class BODY_STYLE_OUT_BARE: pass
class BODY_STYLE_EMPTY_OUT_BARE: pass


class MethodDescriptor(object):
    """This class represents the method signature of an exposed service. It is
    produced by the :func:`spyne.decorator.srpc` decorator.
    """

    def __init__(self, function, in_message, out_message, doc,
                 is_callback, is_async, mtom, in_header, out_header, faults,
                 parent_class, port_type, no_ctx, udd, class_key, aux, patterns,
                 body_style, args, operation_name, no_self, translations,
                 when, static_when, service_class, href, internal_key_suffix,
                 default_on_null):

        self.__real_function = function
        """The original callable for the user code."""

        self.reset_function()

        self.operation_name = operation_name
        """The base name of an operation without the request suffix, as
        generated by the ``@srpc`` decorator."""

        self.internal_key_suffix = internal_key_suffix
        """A string that is appended to the internal key string. Helpful when
        generating services programmatically."""

        self.in_message = in_message
        """A :class:`spyne.model.complex.ComplexModel` subclass that defines the
        input signature of the user function and that was automatically
        generated by the ``@srpc`` decorator."""

        self.name = None
        """The public name of the function. Equals to the type_name of the
        in_message."""

        if body_style is BODY_STYLE_BARE:
            self.name = in_message.Attributes.sub_name

        if self.name is None:
            self.name = self.in_message.get_type_name()

        self.out_message = out_message
        """A :class:`spyne.model.complex.ComplexModel` subclass that defines the
        output signature of the user function and that was automatically
        generated by the ``@srpc`` decorator."""

        self.doc = doc
        """The function docstring."""

        # these are not working, so they are not documented.
        self.is_callback = is_callback
        self.is_async = is_async
        self.mtom = mtom
        #"""Flag to indicate whether to use MTOM transport with SOAP."""
        self.port_type = port_type
        #"""The portType this function belongs to."""

        self.in_header = in_header
        """An iterable of :class:`spyne.model.complex.ComplexModel`
        subclasses to denote the types of header objects that this method can
        accept."""

        self.out_header = out_header
        """An iterable of :class:`spyne.model.complex.ComplexModel`
        subclasses to denote the types of header objects that this method can
        emit along with its return value."""

        self.faults = faults
        """An iterable of :class:`spyne.model.fault.Fault` subclasses to denote
        the types of exceptions that this method can throw."""

        self.no_ctx = no_ctx
        """no_ctx: Boolean flag to denote whether the user code gets an
        implicit :class:`spyne.MethodContext` instance as first argument."""

        self.udd = DefaultAttrDict(**udd)
        """Short for "User Defined Data", this is an empty DefaultAttrDict that
        can be updated by the user to pass arbitrary metadata via the ``@rpc``
        decorator."""

        self.class_key = class_key
        """ The identifier of this method in its parent
        :class:`spyne.service.ServiceBase` subclass."""

        self.aux = aux
        """Value to indicate what kind of auxiliary method this is. (None means
        primary)

        Primary methods block the request as long as they're running. Their
        return values are returned to the client. Auxiliary ones execute
        asyncronously after the primary method returns, and their return values
        are ignored by the rpc layer.
        """

        self.patterns = patterns
        """This list stores patterns which will match this callable using
        various elements of the request protocol.

        Currently, the only object supported here is the
        :class:`spyne.protocol.http.HttpPattern` object.
        """

        self.body_style = body_style
        """One of (BODY_STYLE_EMPTY, BODY_STYLE_BARE, BODY_STYLE_WRAPPED)."""

        self.args = args
        """A sequence of the names of the exposed arguments, or None."""

        # FIXME: docstring yo.
        self.no_self = no_self
        """FIXME: docstring yo."""

        self.service_class = service_class
        """The ServiceBase subclass the method belongs to, if there's any."""

        self.parent_class = parent_class
        """The ComplexModel subclass the method belongs to. Only set for @mrpc
        methods."""

        self.default_on_null = default_on_null
        if default_on_null is not None and parent_class is None:
            raise LogicError("default_on_null is only to be used inside @mrpc")

        # HATEOAS Stuff
        self.translations = translations
        """None or a dict of locale-translation pairs."""

        self.href = href
        """None or a dict of locale-translation pairs."""

        self.when = when
        """None or a callable that takes object instance and returns a
        boolean value. If true, the object can process that action.
        """

        self.static_when = static_when
        """None or a callable that takes the object instance and returns a
        boolean value. If true, the object can process that action.
        """

    def translate(self, locale, default):
        """
        :param locale: locale string
        :param default: default string if no translation found
        :returns: translated string
        """

        if locale is None:
            locale = 'en_US'
        if self.translations is not None:
            return self.translations.get(locale, default)
        return default

    @property
    def key(self):
        """The function identifier in '{namespace}name' form."""

        assert not (self.in_message.get_namespace() is DEFAULT_NS)

        return '{%s}%s' % (
            self.in_message.get_namespace(), self.in_message.get_type_name())

    @property
    def internal_key(self):
        """The internal function identifier in '{namespace}name' form."""

        sc = self.service_class
        if sc is not None:
            return '{%s}%s%s' % (sc.get_internal_key(),
                                    six.get_function_name(self.function),
                                                       self.internal_key_suffix)

        pc = self.parent_class
        if pc is not None:
            mn = pc.__module__
            on = pc.__name__

            dn = self.name
            # prevent duplicate class name. this happens when the class is a
            # direct subclass of ComplexModel
            if dn.split('.', 1)[0] != on:
                return "{%s}%s.%s" % (mn, on, dn)

            return "{%s}%s" % (mn, dn)

    @staticmethod
    def get_owner_name(cls):
        if issubclass(cls, ServiceBase):
            return cls.get_service_name()
        return cls.__name__

    def gen_interface_key(self, cls):
        # this is a regular service method decorated by @rpc
        if issubclass(cls, ServiceBase):
            return '{}.{}.{}'.format(cls.__module__,
                                            self.get_owner_name(cls), self.name)

        # this is a member method decorated by @mrpc
        else:
            mn = cls.get_namespace() or '__nons__'
            on = cls.get_type_name()

            dn = self.name
            # prevent duplicate class name. this happens when the class is a
            # direct subclass of ComplexModel
            if dn.split('.', 1)[0] != on:
                return '.'.join( (mn, on, dn) )

            return '.'.join( (mn, dn) )

    @staticmethod
    def _get_class_module_name(cls):
        return '.'.join([frag for frag in cls.__module__.split('.')
                                                   if not frag.startswith('_')])

    def is_out_bare(self):
        return self.body_style in (BODY_STYLE_EMPTY_OUT_BARE,
                                   BODY_STYLE_EMPTY,
                                   BODY_STYLE_BARE,
                                   BODY_STYLE_OUT_BARE)

    def reset_function(self, val=None):
        if val != None:
            self.__real_function = val
        self.function = self.__real_function

    @property
    def in_header(self):
        return self.__in_header

    @in_header.setter
    def in_header(self, in_header):
        from spyne.model._base import ModelBase
        try:
            is_model = issubclass(in_header, ModelBase)
        except TypeError:
            is_model = False

        if is_model:
            in_header = (in_header,)

        assert in_header is None or isinstance(in_header, tuple)
        self.__in_header = in_header

    @property
    def out_header(self):
        return self.__out_header

    @out_header.setter
    def out_header(self, out_header):
        from spyne.model._base import ModelBase
        try:
            is_model = issubclass(out_header, ModelBase)
        except TypeError:
            is_model = False

        if is_model:
            out_header = (out_header,)

        assert out_header is None or isinstance(out_header, tuple)
        self.__out_header = out_header
