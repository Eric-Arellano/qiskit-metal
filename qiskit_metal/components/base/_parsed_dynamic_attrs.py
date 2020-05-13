# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
Parsed dynamic attributes.

@author: Zlatko Minev
@date: 2020
"""
import  pprint
from typing import List
from typing import TYPE_CHECKING
#from ...toolbox_python.utility_functions import log_error_easy
if TYPE_CHECKING:
    from .base import BaseComponent

def is_ipython_magic(check_attribute: str) -> bool:
    """Ignore the following checks by jupyter """
    return check_attribute in {
        '_ipython_canary_method_should_not_exist_',
        '_ipython_display_',
        '_repr_mimebundle_',
        '_repr_html_',
        '_repr_markdown_',
        '_repr_svg_',
        '_repr_png_',
        '_repr_pdf_',
        '_repr_jpeg_',
        '_repr_latex_',
        '_repr_json_',
        '_repr_javascript_',
        '_rapped',
        '__wrapped__',
        '__call__',
    }

class ParsedDynamicAttributes_Component():
    """
    Provides a parsing view of the component options.

    When accessed, returns parse versions of the user options.
    Works with nested options too.

    Example:
        component.options = {'x':'1nm'}
        print(component.p.x)
            >> float(1e7)
    """

    """
    Ask Zlatko for explanation.
    Special method names:
        See Python Data Module for Objects:
            https://docs.python.org/3/reference/datamodel.html
            https://docs.python.org/3/library/stdtypes.html#object.__dict__
            https://python-reference.readthedocs.io/en/latest/docs/dunderattr/index.html
            https://rszalski.github.io/magicmethods/

        __getattribute__:        Called unconditionally to implement attribute accesses for instances of the class.
        __getattr__:        Called when an attribute lookup has not found the attribute in the usual places.
        __setattr__:        Called when an attribute assignment is attempted.
        __delattr__:        Called when an attribute deletion is attempted.
    """

    def __init__(self, component: 'BaseComponent', key_list: List[str] = None):
        #print(f'*** Created with {key_list}')
        # These names must have __xx__ or else they will go to getattr instead of getattribute

        self.__component__ = component
        # self.__d__ = component.options
        self.__keylist__ = key_list or []  # lis tot get current value

        self.__parse__ = component.design.parse_value         # function

    def __dir__(self):
        # For autocompletion
        return list(self.__get_dict__().keys())

    def __repr__(self):
        return self.__getdict__().__repr__()

    # def _repr_html_(self):
    #    return self.__d__._repr_html_()

    def __str__(self):
        return self.__getdict__().__str__()

    def __getdict__(self) -> dict:
        return get_nested_dict_item(self.__component__.options, self.__keylist__)

    def __getattr__(self, name: str):
        """
        Delegating Attribute Access
        After regular attribute access, try looking up the name
        This allows simpler access to columns for interactive use.
        """
        #### Note: obj.x will always call obj.__getattribute__('x') prior to
        # calling obj.__getattr__('x').
        #
        #### Former issues:
        # These two only come up when trying to use in ipython /jupyter environemtn
        # and acessing a sub dictionary in the past
        # Exmaple:
        #   xx = ParsedDynamicAttributes(self, ['c'])
        #   xx
        # if name.startswith('_repr') or name.startswith('_ipython'):
        #    return

        #print(f'__getattr__ NAME = {name};  dict=',self.__getdict__())
        return self.__getitem__(name)

    def __getitem__(self, name: str):

        # print('__getitem__')

        dic = self.__getdict__()

        if name not in dic:
            if not is_ipython_magic(name):
                # log_error_easy(self.__component__.logger, post_text=
                xx = self.__keylist__
                xx = ".".join(xx) + "." + name if len(xx) > 0 else name
                self.__component__.logger.error('\nWarning: User tried to access a variable in the parse options'
                                                f' that is not there!\n Component name = `{self.__component__.name}`\n'
                                                f' Option name    = `{xx}`')
                return None
            else:
                # IPython checking methods
                # https://github.com/jupyter/notebook/issues/2014
                raise AttributeError(name)

        else:
            val = dic.get(name)
            #print(f'val = {val}')
            if isinstance(val, dict):
                #print(f'  -> Going to create a new {self.__keylist__ + [name]}')
                return ParsedDynamicAttributes_Component(self.__component__, key_list=self.__keylist__ + [name])
            else:
                return self.__parse__(val)

    ####### SERIALIZATION

    def __getstate__(self):
        #  "I'm being pickled"
        return self.__dict__

    def __setstate__(self, d):
        #  f"I'm being unpickled with these values: {d}"
        self.__dict__ = d

    def __repr__(self):
        """For viewing. Just return the whole parse dictionary
        """
        b = '\033[94m\033[1m'
        e = '\033[0m'

        c = self.__component__
        parsed = c.parse_value(c.options)
        parsed_text = pprint.pformat(parsed, indent=1)
        text = f"""{b}Current parsed *view* of options for {c.name}:{e}
 (Units are parsed to floats in default design units.)
 {parsed_text}"""
        return text


# TESTING code:
"""
from qiskit_metal.components.base.base import BaseComponent
from qiskit_metal import DEFAULT_OPTIONS

class Test(BaseComponent):
    def make(self):
        pass
DEFAULT_OPTIONS['Test'] = {
    'a' : '1mm',
    'b' : '1um',
    'c' : {
        'd' : '15um',
        'e' : '10um',
        }
    }
self = Test(design, 'test')
self.p = ParsedDynamicAttributes(self)
self.p
self.p.a
self.p.a.c
"""


def get_nested_dict_item(dic: dict, key_list: list, level=0):
    """
        level {int} -- internal for recussion

    Example use:

        .. code-block: python

            myDict = Dict(
                aa=Dict(
                    x1={
                        'dda': '34fF'
                    },
                    y1='Y',
                    z='10um'
                ),
                bb=Dict(
                    x2=5,
                    y2='YYYsdg',
                    z='100um'
                ),
                cc='100nm'
            )
            key_list = ['cc']
            print(get_nested_dict_item(myDict, key_list))

            key_list = ['aa', 'x1', 'dda']
            print(get_nested_dict_item(myDict, key_list))

        Results in
            >> 100nm
            >> 34fF
    """
    if not key_list:  # get the root
        return dic

    if level < len(key_list)-1:
        return get_nested_dict_item(dic[key_list[level]], key_list, level+1)
    else:
        return dic[key_list[level]]


# Example use
"""
myDict = Dict(
    aa=Dict(
        x1={
            'dda': '34fF'
        },
        y1='Y',
        z='10um'
    ),
    bb=Dict(
        x2=5,
        y2='YYYsdg',
        z='100um'
    ),
    cc='100nm'
)
key_list = ['cc']
print(get_nested_dict_item(myDict, key_list))

key_list = ['aa', 'x1', 'dda']
print(get_nested_dict_item(myDict, key_list))

print(get_nested_dict_item(myDict, ['aa']))
"""
