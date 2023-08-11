from pathlib import Path
from typing import Optional, Union

from PIL import Image, ImageDraw

from xmlobj import get_xml_obj
from xmlobj.xmlmapping import XMLMixin


class DrawBoxesMixin:
    def draw_box(self, image) -> Image.Image:
        p1 = (self.object.bndbox.xmin, self.object.bndbox.ymin)
        p2 = (self.object.bndbox.xmax, self.object.bndbox.ymax)
        img_draw = ImageDraw.Draw(image)
        img_draw.text(p1, self.object.name, align="left")
        img_draw.rectangle([p1, p2])
        return image


def draw_annotation_fabric(
    file_path: Union[str, Path], attr_type_spec: Optional[dict] = None
) -> Union[XMLMixin, DrawBoxesMixin]:
    """
    Crate object with draw_box function

    Parameters
    ----------
    file: path to xml file
    attr_type_spec: dict, optional
        specify attribute types to explicitly cast attribute values

    Returns
    -------
    Drawable object
    """
    return get_xml_obj(
        file_path, mixin_cls=DrawBoxesMixin, attr_type_spec=attr_type_spec
    )


if __name__ == "__main__":
    pascal_annotation = Path("samples/000027.xml")  # sample from VOCtest_06-Nov-2007
    img_file = "samples/000027.jpg"
    annotation = draw_annotation_fabric(pascal_annotation)
    img = Image.open(img_file)
    img = annotation.draw_box(img)
    img.show()
