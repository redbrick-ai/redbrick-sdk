"""Handle Datamuro interactions."""
import json
from tqdm import tqdm
import os
from termcolor import colored
import datetime
import cv2


class Datum:
    """High level class for handling datamuro interactions"""

    def __init__(self, label_format, labelset):
        """Constructor."""
        self.format = label_format
        self.labelset = labelset

        # Create a cache directory
        time = str(datetime.datetime.now())
        self.cache_dir = ".RB_Cache_%s" % time
        self.export_dir = 'RB_Export_%s' % time

    def cache(self):
        """Cache the labels and data in an internal format"""
        os.mkdir(self.cache_dir)

        if self.labelset.task_type == "SEGMENTATION":
            self.cache_segment()

        if self.labelset.task_type == "BBOX":
            self.cache_bbox()

        print(
            colored("[INFO]", "blue"),
            colored("Export Completed.", "green"),
            "stored in ./%s" % self.cache_dir,
        )

    def export(self):
        """Export the data to a specified format."""
        # Cache labels in internal format
        self.cache()

        if self.labelset.task_type == 'BBOX':
            pass

    def cache_bbox(self):
        """Cache bounding box labels, convert from internal formal to YOLO."""
        # Create YOLO style meta data files
        num_classes = len(list(self.labelset.taxonomy.keys()))
        train_file = 'train.txt'
        names_file = 'names.txt'
        data_file = 'obj.data'
        backup_dir = 'backup/'

        # obj.data
        with open(self.cache_dir + '/' + data_file, 'w+') as file:
            file.write('classes = %s' % num_classes)
            file.write('\n')
            file.write('train = %s' % ('data' + '/' + train_file))
            file.write('\n')
            file.write('names = %s' % ('data' + '/' + names_file))
            file.write('\n')
            file.write('backup = %s' % backup_dir)

        # names.txt
        with open(self.cache_dir + '/' + names_file, 'w+') as file:
            class_names = list(self.labelset.taxonomy.keys())
            for name in class_names:
                file.write(name + '\n')

        # obj_train_data/
        os.mkdir(os.path.join(self.cache_dir, 'obj_train_data'))
        taxonomy_mapper = {name: idx for idx,
                           name in enumerate(list(self.labelset.taxonomy.keys()))}
        image_filepaths = []

        for i in tqdm(range(len(self.labelset.dp_ids))):
            dp = self.labelset.__getitem__(i)
            dp_entry = {}
            dp_entry["url"] = dp.image_url_not_signed
            dp_entry["labels"] = []

            # write image data to file
            image_filepath = os.path.join(self.cache_dir, 'obj_train_data',
                                          str(dp.image_url_not_signed).replace("/", "_"))
            image_filepaths.append(image_filepath)
            cv2.imwrite(image_filepath, dp.image)  # pylint: disable=no-member

            # create the label file name
            filext_idx = image_filepath.rfind('.')
            if not filext_idx:
                filext_idx = 0
            label_filepath = image_filepath[0:filext_idx] + '.txt'

            # write labels to the txt file
            with open(label_filepath, 'w+') as file:
                for label in dp.gt._labels:
                    class_idx = taxonomy_mapper[list(label._class.keys())[0]]
                    file.write('%d %.6f %.6f %.6f %.6f \n' % (
                               class_idx, label._xnorm, label._ynorm, label._wnorm, label._hnorm))

        # create train.txt file
        with open(os.path.join(self.cache_dir, train_file), 'w+') as file:
            for filename in image_filepaths:
                file.write(filename + '\n')

    def cache_segment(self):
        """Cache segmentation labels."""
        # Save png of masks
        for i in tqdm(range(len(self.labelset.dp_ids))):
            dp = self.labelset.__getitem__(i)
            dp.gt._mask.dump(
                self.cache_dir + "/" +
                str(dp.image_url_not_signed).replace("/", "_") + ".dat"
            )

        # Save the class-mapping (taxonomy) in json format in the folder
        with open("%s/class-mapping.json" % self.cache_dir, "w+") as file:
            json.dump(dp.taxonomy, file, indent=2)
