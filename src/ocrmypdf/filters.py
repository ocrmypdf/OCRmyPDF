import PIL.ImageOps
from PIL import Image


def invert(im):
    return PIL.ImageOps.invert(im.convert('L'))


def whiteout(im):
    return Image.new(im.mode, im.size)
