from pathlib import Path

from PIL import Image, ImageDraw

from xmlobj import get_xml_obj


class DrawBoxesMixin:
    def draw_box(self, image) -> Image.Image:
        p1 = (self.object.bndbox.xmin, self.object.bndbox.ymin)
        p2 = (self.object.bndbox.xmax, self.object.bndbox.ymax)
        img_draw = ImageDraw.Draw(image)
        img_draw.text(p1, self.object.name, align="left")
        img_draw.rectangle([p1, p2])
        return image


def sample_1():
    """
    Read and print objects
    """
    samples = Path("./samples")
    for file in samples.glob("*.xml"):
        obj = get_xml_obj(file)
        print(obj)
        print("---------------------------------")


def sample_2():
    """
    Convert attributes
    """
    attr_types = {
        "segmented": bool,
        "difficult": bool,
        "truncated": bool,
    }
    pascal_annotation = Path("samples/000027.xml")
    obj = get_xml_obj(pascal_annotation, attr_type_spec=attr_types)
    print(obj)


def sample_3():
    """
    Add functionality with mixin class
    """
    pascal_annotation = Path("samples/000027.xml") # sample from VOCtest_06-Nov-2007
    img_file = "samples/000027.jpg"
    img = Image.open(img_file)
    obj = get_xml_obj(pascal_annotation, mixin_cls=DrawBoxesMixin)
    rendered_img = obj.draw_box(img.copy())
    rendered_img.show()


if __name__ == "__main__":
    sample_3()
