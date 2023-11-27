import re
import xml.etree.ElementTree as xml
from pathlib import Path
from typing import List, Optional, Union

from xmltodict import parse


def mixin_factory(name, base, mixin):
    """
    https://stackoverflow.com/questions/9087072/how-do-i-create-a-mixin-factory-in-python
    """
    return type(name, (base, *mixin), {})


_BOOL_STR = ("True", "true", "false", "False")


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


class XMLMixin:
    """
    Class provides to_xml function and xml-style str output
    """

    def _simple_attr(self):
        for attribute, value in self.__dict__.items():
            if type(value) in [int, float, bool, str]:
                yield attribute

    def _obj_type_attr(self):
        for attribute, value in self.__dict__.items():
            if isinstance(value, XMLMixin):
                yield attribute

    def _list_type_attr(self):
        for attribute, value in self.__dict__.items():
            if type(value) is list:
                yield attribute

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

    def __str__(self):
        head = []
        root_name = self.__class__.__name__
        for attr_name in self._simple_attr():
            attr_val = getattr(self, attr_name)
            attr_name = attr_name.lower()
            head.append(f"\n\t<{attr_name}>{attr_val}</{attr_name}>")
        attr_list = []
        for attr_name in self._list_type_attr():
            attr_val = getattr(self, attr_name)
            objects_ = []
            for obj in attr_val:
                sobj = str(obj)
                parts = sobj.split("\n")
                sobj = "\n".join([f"\t{line}" for line in parts])
                objects_.append(sobj + "\n")
                s_objects = "".join(objects_)
                attr_list.append(s_objects)
        for attr_name in self._obj_type_attr():
            attr_val = getattr(self, attr_name)
            parts = str(attr_val).split("\n")
            sobj = "\n".join([f"\t{line}" for line in parts])
            attr_list.append(sobj)
        if len(attr_list):
            for i in range(len(attr_list)):
                if attr_list[i][-1] == "\n":
                    attr_list[i] = "\n" + attr_list[i][:-1]
                elif attr_list[i][-1] == ">":
                    attr_list[i] = "\n" + attr_list[i]
            head.append("".join(attr_list))
        header = "".join(head)
        root_name = root_name.lower()
        s = f"<{root_name}>{header}\n</{root_name}>"
        return s


def object_from_data(
    base_obj: XMLMixin, attributes: dict, attr_type_spec: Optional[dict]
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
            attr_name = ks.lower()
            cls_name = ks.capitalize()
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
