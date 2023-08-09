from pathlib import Path

from xmlobj.xmlmapping import get_xml_obj

attr_types = {
    "price": int,
    "segmented": bool
}

if __name__ == '__main__':
    samples = Path("./samples")
    for file in samples.glob("*.xml"):
        obj = get_xml_obj(file, attr_types)
        print(obj)
