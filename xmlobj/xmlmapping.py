from pathlib import Path
import re
from typing import Any, Union, Optional

from xmltodict import parse

ds_path = Path("/media/alexander/D/datasets/Public/VOCtest_06-Nov-2007/VOCdevkit/VOC2007")
img_src = ds_path / "JPEGImages"
ann_src = ds_path / "Annotations"


def mixin_factory(name, base, mixin):
    """
    https://stackoverflow.com/questions/9087072/how-do-i-create-a-mixin-factory-in-python
    """
    return type(name, (base, mixin), {})


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
        if attr_value == "true" or attr_value == "True":
            return bool
    return str


class XMLMixin:

    def simple_attr(self):
        for attribute, value in self.__dict__.items():
            if type(value) in [int, float, bool, str]:
                yield attribute

    def obj_type_attr(self):
        for attribute, value in self.__dict__.items():
            if isinstance(value, XMLMixin):
                yield attribute

    def list_type_attr(self):
        for attribute, value in self.__dict__.items():
            if type(value) is list:
                yield attribute

    def __str__(self):
        head = []
        root_name = self.__class__.__name__
        for attr_name in self.simple_attr():
            attr_val = getattr(self, attr_name)
            head.append(f"\n\t<{attr_name}>{attr_val}</{attr_name}>")
        attr_list = []
        for attr_name in self.list_type_attr():
            attr_val = getattr(self, attr_name)
            objects_ = []
            for obj in attr_val:
                sobj = str(obj)
                parts = sobj.split("\n")
                sobj = "\n".join([f"\t{line}" for line in parts])
                objects_.append(sobj + "\n")
                s_objects = "".join(objects_)
                attr_list.append(s_objects)
        for attr_name in self.obj_type_attr():
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
        s = f"<{root_name}>{header}\n</{root_name}>"
        return s


def object_from_data(key: str, value: Any, attr_type_spec: Optional[dict]) -> type:
    tmp_cls = type(key, (), {})
    attr_cls = mixin_factory(key, tmp_cls, XMLMixin)
    obj = attr_cls()
    for ks, vs in value.items():
        attr_type = get_attr_type(vs)
        if attr_type in [str, int, float, bool]:
            setattr(obj, ks, attr_type(vs))
            if attr_type_spec is not None:
                if ks in attr_type_spec:
                    attr_type = attr_type_spec.get(ks)
                    attr_val = getattr(obj, ks)
                    setattr(obj, ks, attr_type(attr_val))
        elif attr_type is dict:
            attr = object_from_data(ks, vs, attr_type_spec)
            setattr(obj, ks, attr)
        elif attr_type is list:
            setattr(obj, ks, list())
            for list_obj in vs:
                sub_obj = object_from_data(ks, list_obj, attr_type_spec)
                getattr(obj, ks).append(sub_obj)
        else:
            raise Exception(f"Cannot parse key-value: {str(key)} - {str(value)}")
    return obj


def get_xml_obj(file: Union[str, Path], attr_type_spec: Optional[dict] = None, mixin_cls: Optional = None) -> type:
    with open(file, "r") as f:
        xml = f.read()
    data = parse(xml)
    assert len(data) == 1
    root_key = list(data.keys())[0]
    root_val = data.get(root_key)
    return object_from_data(root_key, root_val, attr_type_spec)
