import os
from pdf2image import convert_from_path
import shutil
import numpy as np

def save_detections(title_blocks, image):
    x_1, y_1, x_2, y_2 = title_blocks[0].block.x_1, title_blocks[0].block.y_1, title_blocks[0].block.x_2, title_blocks[0].block.y_2
    cropped = image[int(y_1):int(y_2), int(x_1):int(x_2)]
    text = pytesseract.image_to_string(cropped, lang='eng',config= '--psm 3 --oem 1')
    return text

def inference(image):
    image = image[..., ::-1]
    layout = model.detect(image)

    # Extracting Tables
    title_blocks = lp.Layout([b for b in layout if b.type=="Title"])

    h, w = image.shape[:2]

    left_interval = lp.Interval(0, w/2*1.05, axis='x').put_on_canvas(image)

    left_blocks = title_blocks.filter_by(left_interval, center=True)
    left_blocks.sort(key = lambda b:b.coordinates[1])

    right_blocks = [b for b in title_blocks if b not in left_blocks]
    right_blocks.sort(key = lambda b:b.coordinates[1])

    # And finally combine the two list and add the index
    # according to the order
    title_blocks.sort(key = lambda b:b.coordinates[1])
    title_blocks = lp.Layout([b.set(id = idx) for idx, b in enumerate(title_blocks)])
    return save_detections(title_blocks, image)

def inference2(pages):
    return 0

def pdf_inference(path):
    pages = convert_from_path(path, dpi=100, grayscale=False)
    image = np.array(pages[0])
    title = inference(image)
    return title

def pdf_inference2(path):
    pages = convert_from_path(path, dpi=100, grayscale=True)
    images = inference2(pages)
    return images