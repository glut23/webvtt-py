import io
import re
from setuptools import setup, find_packages

with io.open('README.rst', 'r', encoding='utf-8') as f:
    readme = f.read()

with io.open('webvtt/__init__.py', 'rt', encoding='utf-8') as f:
    version = re.search(r'__version__ = \'(.*?)\'', f.read()).group(1)


setup(
    name='webvtt-py',
    version=version,
    description='WebVTT reader, writer and segmenter',
    long_description=readme,
    author='Alejandro Mendez',
    author_email='amendez23@gmail.com',
    url='https://github.com/glut23/webvtt-py',
    packages=find_packages('.', exclude=['tests']),
    include_package_data=True,
    install_requires=[
        'docopt'
    ],
    entry_points={
        'console_scripts': [
            'webvtt=webvtt.cli:main'
        ]
    },
    license='MIT',
    python_requires='>=3.4',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='webvtt captions',
)
