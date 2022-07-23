import os
import re
from setuptools import setup, find_packages


here = os.path.abspath(os.path.dirname(__file__))
project = 'restsh'


with open('requirements/requirements.txt') as f:
    requirements = f.readlines()


info_regex = {
    'version': r"^__version__ = ['\"]([^'\"]*)['\"]",
    'author': r"^__author__ = ['\"]([^'\"]*)['\"]",
    'email': r"^__email__ = ['\"]([^'\"]*)['\"]",
}


def read(*parts):
    with open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()


def find_info(info_var, *file_paths):
    version_file = read(*file_paths)
    version_match = re.search(info_regex[info_var], version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find {} string.'.format(info_var))


setup(
    name=project,
    description='REST and RPC processing, scriptable, shell',
    long_description='REST and RPC processing, scriptable, shell',
    version="1.0.0",
    author='Ray Wallace',
    author_email='the.faboo@gmail.com',
    packages=find_packages(),
    zip_safe=True,
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "restsh = restsh.__main__:main"
        ]
    },
)
