"""webvtt-py setuptools configuration."""

import re
import pathlib

from setuptools import setup, find_packages

version, author, author_email = (
    re.search(
        rf'__{name}__ = \'(.*?)\'',
        pathlib.Path('webvtt/__init__.py').read_text()
        ).group(1)
    for name in ('version', 'author', 'author_email')
    )

setup(
    name='webvtt-py',
    version=version,
    description='WebVTT reader, writer and segmenter',
    long_description=pathlib.Path('README.rst').read_text(),
    long_description_content_type='text/x-rst',
    author=author,
    author_email=author_email,
    url='https://github.com/glut23/webvtt-py',
    packages=find_packages('.', exclude=['tests']),
    include_package_data=True,
    data_files=[('share/man/man1', ['man/webvtt.1'])],
    entry_points={
        'console_scripts': [
            'webvtt=webvtt.cli:main'
        ]
    },
    license='MIT',
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        'Programming Language :: Python :: 3.15',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='webvtt captions',
)
