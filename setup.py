import os
import re
from setuptools import setup, find_packages

project = 'restsh'

with open('requirements/requirements.txt') as f:
    requirements = f.readlines()


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
