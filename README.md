### Description
xmlobj is simple utility to map xml file to python object

xmlobj also allows you to add functionality to mapped object by adding mixin class

### A Simple Example
```
from pathlib import Path

from PIL import Image, ImageDraw

from xmlobj.xmlmapping import get_xml_obj


class DrawBoxesMixin:
    def draw_box(self, image) -> Image.Image:
        p1 = (self.object.bndbox.xmin, self.object.bndbox.ymin)
        p2 = (self.object.bndbox.xmax, self.object.bndbox.ymax)
        img_draw = ImageDraw.Draw(image)
        img_draw.text(p1, self.object.name, align="left")
        img_draw.rectangle([p1, p2])
        return image


if __name__ == "__main__":
    pascal_annotation = Path("samples/000027.xml")
    img_file = "samples/000027.jpg"
    img = Image.open(img_file)
    obj = get_xml_obj(pascal_annotation, mixin_cls=DrawBoxesMixin)
    rendered_img = obj.draw_box(img.copy())
    rendered_img.show()

```