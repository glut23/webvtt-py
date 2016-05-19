from setuptools import setup, find_packages


def readme():
    with open('README.rst', 'r', encoding='utf-8') as f:
        return f.read()

setup(
    name='webvtt-py',
    version='0.1',
    description='WebVTT reader, writer and segmenter',
    long_description=readme(),
    author='Alejandro Mendez',
    author_email='amendez23@gmail.com',
    url='https://github.com/glut23/webvtt-py',
    packages=find_packages(),
    include_package_data=True,
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
        'Topic :: Utilities',
    ],
    test_suite='tests'
)