import io
from setuptools import setup

from webvtt import __version__


def readme():
    with io.open('README.rst', 'r', encoding='utf-8') as f:
        return f.read()

setup(
    name='webvtt-py',
    version=__version__,
    description='WebVTT reader, writer and segmenter',
    long_description=readme(),
    author='Alejandro Mendez',
    author_email='amendez23@gmail.com',
    url='https://github.com/glut23/webvtt-py',
    packages=[
        'webvtt',
    ],
    include_package_data=True,
    install_requires=['docopt', 'chardet'],
    entry_points={
        'console_scripts': [
            'webvtt=webvtt.cli:main'
        ]
    },
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='webvtt captions',
    test_suite='tests'
)