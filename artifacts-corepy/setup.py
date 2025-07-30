# coding=utf-8

# Always prefer setuptools over distutils
from codecs import open
import glob
from os import path
import sys

from setuptools import setup, find_packages, Extension

# To use a consistent encoding
here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()
with open(path.join(here, 'VERSION'), encoding='utf-8') as f:
    version = f.read()
with open(path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    requirements = [
        line.strip() for line in f
        if line.strip() and not line.strip().startswith('--') and not line.strip().startswith('#')
    ]

data_files = []

cmdclass = {}
ext_modules = []

setup(
    name='artifacts_corepy',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=version,
    description='Falcon Base API Framework',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/wecube team/artifacts_corepy',

    # Author details
    author='wecube team',
    author_email='roywu@webank.com',

    # Choose your license
    license='Apache License 2.0',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 5 - Production/Stable ',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License ',
        'Topic :: Software Development :: Libraries',
        'Framework :: Falcon',
        'Framework :: SQLAlchemy',
        'Framework :: Celery',
        'Framework :: Talos',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Operating System :: OS Independent'
    ],

    # What does your project relate to?
    keywords='',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['docs', 'tests']),
    py_modules=['synchronized_diff_variable'],  # 新增：包含根目录的单独模块

    # Alternatively, if you want to distribute just a my_module.py, uncomment
    # this:
    #   py_modules=["my_module"],

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=requirements,

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[testing]
    extras_require={'testing': ['pytest', 'pytest-runner', 'pytest-html', 'pytest-cov', 'pytest-mock']},

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    package_data={},

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    data_files=data_files,
    zip_safe=False,
    cmdclass=cmdclass,
    ext_modules=ext_modules,

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'artifacts_corepy_server=artifacts_corepy.server.simple_server:main',
            'artifacts_corepy_scheduler=artifacts_corepy.server.scheduler:main',
            'artifacts_sync_diff_vars=synchronized_diff_variable:main', 
        ],
    },
)
