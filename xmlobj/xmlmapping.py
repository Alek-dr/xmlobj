import re
import xml.etree.ElementTree as xml
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

from jinja2 import Template
from xmltodict import parse


def mixin_factory(name, base, mixin):
    """
    https://stackoverflow.com/questions/9087072/how-do-i-create-a-mixin-factory-in-python
    """
    return type(name, (base, *mixin), {})


_BOOL_STR = ("True", "true", "false", "False")

_SIMPLE_TEMPLATE = """
<{{- root_name }}>
    {%- for attr_name, attr_val in data.items() %}
    <{{ attr_name }}>{{ attr_val }}</{{ attr_name }}>
{%- endfor %}
</{{ root_name }}>
    """

_MULTI_LINE_TEMPLATE = """
<{{ root_name }}>
{%- for attr_name, attr_val in data.items() %}
    {%- for line in attr_val._to_str().split("\n") %}
    {{ line }}
{%- endfor %}
{%- endfor %}
</{{ root_name }}>
    """

_COMPLEX_ATTR = """
<{{- attr_name }}>
{%- for line in attr_val.split("\n") %}
    {{ line }}
{%- endfor %}
</{{ attr_name }}>
    """


def get_attr_type(attr_value) -> type:
    if isinstance(attr_value, dict):
        return dict
    elif isinstance(attr_value, list):
        return list
    elif isinstance(attr_value, set):
        return set
    elif isinstance(attr_value, str):
        if re.search("^\d+\.\d+", attr_value):
            return float
        if all(char.isnumeric() for char in attr_value):
            return int
        if attr_value in _BOOL_STR:
            return bool
    return str


def to_list(cls_name: str, value: Any) -> Tuple[str, List[Any]]:
    if isinstance(value, dict) and len(value) == 1:
        attr_name = list(value.keys())[0]
        data = value.pop(attr_name)
        cls_name = attr_name.capitalize()
        if isinstance(data, dict):
            return cls_name, [data]
        elif isinstance(data, list):
            return cls_name, data
    return cls_name, value


def is_simple(value) -> bool:
    return type(value) in [int, float, bool, str]


def simple_attr_to_str(attr_name: str, attr_val: Any) -> str:
    template = """<{{ attr_name }}>{{ attr_val}}</{{ attr_name }}>"""
    j2_template = Template(template)
    attrs = {
        "attr_name": attr_name.lower(),
        "attr_val": attr_val,
    }
    return j2_template.render(attrs)


def complex_attr_to_str(attr_name: str, attr_val: Any) -> str:
    j2_template = Template(_COMPLEX_ATTR, lstrip_blocks=True)
    attrs = {
        "attr_name": attr_name.lower(),
        "attr_val": attr_val,
    }
    return j2_template.render(attrs).strip()


class XMLMixin:
    """
    Class provides to_xml function and xml-style str output
    """

    def _is_simple(self) -> bool:
        return all(
            [type(value) in [int, float, bool, str] for value in self.__dict__.values()]
        )

    def _attr_to_str(self) -> str:
        root_name = self.__class__.__name__.lower()
        template = _SIMPLE_TEMPLATE if self._is_simple() else _MULTI_LINE_TEMPLATE
        attrs = {"root_name": root_name, "data": self.__dict__}
        j2_template = Template(template, lstrip_blocks=True, newline_sequence="\n")
        return j2_template.render(attrs).strip()

    def to_xml(self):
        root_name = self.__class__.__name__.lower()
        root = xml.Element(root_name)
        for k, v in self.__dict__.items():
            if isinstance(v, XMLMixin):
                elem = v.to_xml()
                root.append(elem)
            elif isinstance(v, list):
                for item in v:
                    xml_item = item.to_xml()
                    root.append(xml_item)
            else:
                elem = xml.Element(k)
                elem.text = str(v)
                root.append(elem)
        return root

    def _to_str(self, level=0) -> str:
        elements = []
        for attr_name in self.__dict__.keys():
            attr_val = getattr(self, attr_name)
            if is_simple(attr_val):
                elements.append(simple_attr_to_str(attr_name, attr_val))
            elif isinstance(attr_val, list):
                objects = []
                for obj in attr_val:
                    if level == 0:
                        attr_name = obj.__class__.__name__.lower()
                    if isinstance(obj, XMLMixin):
                        c = obj._to_str(level=level + 1)
                        c = complex_attr_to_str(attr_name, c)
                        objects.append(c)
                obj_str = "\n".join(objects)
                if level > 0:
                    obj_str = "\n".join(objects)
                    obj_str = complex_attr_to_str(attr_name, obj_str)
                obj_str = obj_str.strip()
                elements.append(obj_str)
            else:
                if attr_val._is_simple():
                    c = attr_val._attr_to_str()
                else:
                    c = attr_val._to_str(level=level + 1)
                    c = complex_attr_to_str(attr_name, c)
                elements.append(c)
        return "\n".join(elements)

    def __str__(self):
        c = self._to_str()
        name = self.__class__.__name__.lower()
        return complex_attr_to_str(name, c).strip()


def object_from_data(
    base_obj: XMLMixin,
    attributes: dict,
    attr_type_spec: Optional[dict],
) -> XMLMixin:
    """
    Add attributes to base_obj

    Parameters
    ----------
    base_obj: base obj to add attributes
    attributes: dict of attr and values
    attr_type_spec: specify attribute types to explicitly cast attribute values
    Returns
    -------
        object with attributes from attributes
    """
    container_attr_name = None
    for ks, vs in attributes.items():
        attr_type = get_attr_type(vs)
        if attr_type in [str, int, float, bool]:
            if ks.startswith("@"):
                ks = ks.replace("@", "")
            if vs in _BOOL_STR:
                vs = eval(vs)
            setattr(base_obj, ks, attr_type(vs))
            if attr_type_spec is not None:
                if ks in attr_type_spec:
                    attr_type = attr_type_spec.get(ks)
                    attr_val = getattr(base_obj, ks)
                    setattr(base_obj, ks, attr_type(attr_val))
        elif attr_type is dict:
            cls_name = ks.capitalize()
            attr_name = ks.lower()
            cls_ = type(cls_name, (), {})
            ext_cls = mixin_factory(cls_name, cls_, [XMLMixin])
            sub_cls_instance = ext_cls()
            attr = object_from_data(sub_cls_instance, vs, attr_type_spec)
            setattr(base_obj, attr_name, attr)
        elif attr_type is list:
            cls_name = (
                container_attr_name
                if container_attr_name is not None
                else ks.capitalize()
            )
            attr_name = ks.lower()
            cls_ = type(cls_name, (), {})
            ext_cls = mixin_factory(cls_name, cls_, [XMLMixin])
            objects_ = []
            for list_obj in vs:
                sub_cls_instance = ext_cls()
                sub_obj = object_from_data(sub_cls_instance, list_obj, attr_type_spec)
                objects_.append(sub_obj)
            setattr(base_obj, attr_name, objects_)
        else:
            raise Exception(f"Cannot parse key-value: {str(ks)} - {str(vs)}")
    return base_obj


def get_xml_obj(
    file: Union[str, Path],
    attr_type_spec: Optional[dict] = None,
    mixin_clsasses: Optional[List[type]] = None,
) -> XMLMixin:
    """
    Map xml file to python object

    Parameters
    ----------
    file: path to xml file
    attr_type_spec: dict, optional
        specify attribute types to explicitly cast attribute values
    mixin_clsasses: list of types
        classes to provide additional functionality
    Returns
    -------
        instance of mapped xml object
    """
    with open(file, "r") as f:
        xml = f.read()
    data = parse(xml)
    assert len(data) == 1
    root_key = list(data.keys())[0]
    root_val = data.get(root_key)
    assert isinstance(root_val, dict)
    root_key = root_key.capitalize()
    cls_ = type(root_key, (), {})
    if mixin_clsasses is None:
        ext_cls = mixin_factory(root_key, cls_, [XMLMixin])
    else:
        ext_cls = mixin_factory(root_key, cls_, [XMLMixin, *mixin_clsasses])
    base_cls_instance = ext_cls()
    return object_from_data(base_cls_instance, root_val, attr_type_spec)
