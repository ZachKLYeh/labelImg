#!/usr/bin/env python
# -*- coding: utf8 -*-
import json
from pathlib import Path

from libs.constants import DEFAULT_ENCODING
from libs.io_abstract_class import FileReader, FileWriter
import os

JSON_EXT = '.json'
ENCODE_METHOD = DEFAULT_ENCODING


class CreateMLWriter(FileWriter):

    def __init__(self, img_folder_name, img_file_name,
                 img_shape, shapes, filename):
        super().__init__(img_folder_name, 
                img_file_name, img_shape, shapes, filename)

    def save(self, target_file=None, class_list=None):
        if os.path.isfile(self.output_file):
            with open(self.output_file, "r") as file:
                input_data = file.read()
                output_dict = json.loads(input_data)
        else:
            output_dict = []

        output_image_dict = {
            "image": self.filename,
            "verified": self.verified,
            "annotations": []
        }

        for shape in self.shapes:
            points = shape["points"]

            x1 = points[0][0]
            y1 = points[0][1]
            x2 = points[1][0]
            y2 = points[2][1]

            height, width, x, y = self.calculate_coordinates(x1, x2, y1, y2)

            shape_dict = {
                "label": shape["label"],
                "coordinates": {
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height
                }
            }
            output_image_dict["annotations"].append(shape_dict)

        # check if image already in output
        exists = False
        for i in range(0, len(output_dict)):
            if output_dict[i]["image"] == output_image_dict["image"]:
                exists = True
                output_dict[i] = output_image_dict
                break

        if not exists:
            output_dict.append(output_image_dict)

        Path(self.output_file).write_text(json.dumps(output_dict), ENCODE_METHOD)

    def calculate_coordinates(self, x1, x2, y1, y2):
        if x1 < x2:
            x_min = x1
            x_max = x2
        else:
            x_min = x2
            x_max = x1
        if y1 < y2:
            y_min = y1
            y_max = y2
        else:
            y_min = y2
            y_max = y1
        width = x_max - x_min
        if width < 0:
            width = width * -1
        height = y_max - y_min
        # x and y from center of rect
        x = x_min + width / 2
        y = y_min + height / 2
        return height, width, x, y


class CreateMLReader(FileReader):

    def __init__(self, json_path, file_path):
        self.json_path = json_path
        self.filename = os.path.basename(json_path)
        super().__init__(file_path)

    def parse_file(self):
        with open(self.json_path, "r") as file:
            input_data = file.read()

        # Returns a list
        output_list = json.loads(input_data)

        if output_list:
            self.verified = output_list[0].get("verified", False)

        if len(self.shapes) > 0:
            self.shapes = []
        for image in output_list:
            #if os.path.splitext(image["image"])[0] == os.path.splitext(self.filename)[0]:
            for shape in image["annotations"]:
                self.add_shape(shape["label"], shape["coordinates"])

    def add_shape(self, label, bnd_box):
        x_min = bnd_box["x"] - (bnd_box["width"] / 2)
        y_min = bnd_box["y"] - (bnd_box["height"] / 2)

        x_max = bnd_box["x"] + (bnd_box["width"] / 2)
        y_max = bnd_box["y"] + (bnd_box["height"] / 2)

        points = [(x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max)]
        self.shapes.append((label, points, None, None, True))

