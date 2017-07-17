import boto3

from webvtt.generic import GenericReader, GenericWriter
import os
from io import StringIO


class FileReader(GenericReader):
    def __init__(self, filename):
        self.filename = filename

    def readlines(self):
        with open(self.filename) as f:
            return [line.rstrip() for line in f.readlines()]


class FileWriter(GenericWriter):
    def __init__(self, folder):
        output_folder = os.path.join(os.getcwd(), folder)
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        self.folder = output_folder

    def open(self, name):
        file_path = os.path.join(self.folder, name)
        return open(file_path, 'w')


class StringReader(GenericReader):
    def __init__(self, filename):
        self.content = filename

    def readlines(self):
        return [line.rstrip() for line in StringIO(self.content).readlines()]


class S3FileLike(object):

    def __init__(self, bucket, key, client, headers, ACL='private'):
        self.bucket, self.key, self.client = bucket, key, client
        self.content = []
        self.headers = headers
        self.ACL = ACL

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.Object(self.bucket, self.key).put(
            Body=''.join(self.content),
            ACL=self.ACL,
            **self.headers
        )

    def write(self, content):
        self.content.append(content)

    def writelines(self, content):
        for f in content:
            self.content.append(f+'\n')


class S3ObjectWriter(GenericWriter):

    def __init__(self, bucket, key_prefix, ACL='private'):
        super(S3ObjectWriter, self).__init__()
        self.bucket = bucket
        self.key_prefix = key_prefix
        self.client = boto3.resource('s3')
        self.ACL = ACL

    def open(self, key, ACL=None):
        file_type = key.split(".")[-1]
        headers = {} if file_type not in self.type_map else self.type_map[file_type]
        if ACL is None:
            ACL = self.ACL
        return S3FileLike(self.bucket, '{}/{}'.format(self.key_prefix, key), self.client, headers, ACL)
