#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import codecs

import pathlib
import setuptools


if sys.version_info < (3, 6):
    raise RuntimeError('SirBot requires Python 3.6+')

LONG_DESCRIPTION = pathlib.Path('README.rst').read_text('utf-8')


def find_version():
    with open("sirbot/__version__.py") as f:
        version = f.readlines()[-1].split('=')[-1].strip().strip("'").strip('"')
        if not version:
            raise RuntimeError('No version found')

    return version


def parse_reqs(req_path='./requirements/requirements.txt'):
    """Recursively parse requirements from nested pip files."""
    install_requires = []
    with codecs.open(req_path, 'r') as handle:
        # remove comments and empty lines
        lines = (line.strip() for line in handle if line.strip() and not line.startswith('#'))
        install_requires.extend(lines)
    return install_requires


setuptools.setup(
    long_description=LONG_DESCRIPTION,
    keywords=[
        'sirbot',
        'chatbot',
        'bot',
        'slack',
    ],
    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and
    # allow pip to create the appropriate form of executable for the
    # target platform.
    # entry_points={
    #     'console_scripts': [
    #         'sirbot=sirbot.cli:main'
    #     ]
    # },
    include_package_data=True,
    install_requires=parse_reqs('requirements.txt'),
    python_requires='~=3.6',
    tests_require=[
        'pytest-runner',
        'pytest-cov',
        'pytest-aiohttp',
        'pytest',
    ],
    # See: http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Environment :: Console',
    ],
    author=(
        'Ovv <contact@ovv.wtf>',
    ),
    author_email='pythondev.slack@gmail.com',
    description='The good Sir Bot-a-lot. An asynchronous python bot framework.',
    license='MIT',
    name='sir-bot-a-lot',
    url='https://github.com/pyslackers/sir-bot-a-lot',
    version=find_version(),
)
