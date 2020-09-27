#!/usr/bin/env python3

import codecs, os, glob, sys, shutil

ROOTDIR = os.path.abspath(os.path.dirname(__file__))

import setuptools
print('using setuptools v%s'%setuptools.__version__)
from setuptools import setup, find_packages

# Classifiers come from PyPi's official list https://pypi.org/classifiers/
PLATFORMS_CLASSIFIERS = [
	"Operating System :: OS Independent",
	"Operating System :: Microsoft :: Windows",
	"Operating System :: POSIX :: Linux",
	"Operating System :: MacOS",
]
LICENSE_CLASSIFIER = "License :: Public Domain"

CLASSIFIERS = [
	LICENSE_CLASSIFIER,
	"Development Status :: 4 - Beta",

	"Intended Audience :: Developers",
	"Environment :: Plugins",

	"Intended Audience :: Developers",
	"Topic :: Software Development :: Quality Assurance",
	"Topic :: Software Development :: Testing",
	"Topic :: Software Development :: Testing :: Unit",
	"Topic :: Education :: Testing",

	"Programming Language :: Python",
	"Programming Language :: Python :: 3.6", 
	"Programming Language :: Python :: 3.7", 
	"Programming Language :: Python :: 3.8", # see also python_requires
	"Programming Language :: Python :: Implementation :: CPython",

	"Natural Language :: English",
]+PLATFORMS_CLASSIFIERS
KEYWORDS = ['pysys', 'java', 'junit']

with codecs.open(ROOTDIR+'/docs/ProjectOverview.rst', "r", encoding="ascii") as f:
	long_description = f.read()

with codecs.open(ROOTDIR+'/VERSION', "r", encoding="ascii") as f:
	version = f.read().strip()

REPO_URL = "https://github.com/ben-spiller/pysysjava"

setup(
	name='PySys-Java',
	description='Java plugins for the PySys System Test Framework',
	
	url=REPO_URL,
	project_urls={ 
		'Repository': REPO_URL,
		'Sample':REPO_URL+'/tree/main/sample',
		'Documentation': 'https://ben-spiller.github.io/pysysjava/',
	},

	author='Ben Spiller', 

	version=version,
	license=LICENSE_CLASSIFIER.split('::')[-1].strip(),
	keywords=KEYWORDS,
	classifiers=CLASSIFIERS,
	platforms=PLATFORMS_CLASSIFIERS,
	long_description=long_description,
	long_description_content_type='text/x-rst',

	python_requires=">=3.6, <4",

	install_requires=[
		"PySys >= 1.6.2"
	],
	
	packages=setuptools.find_packages(),
	include_package_data=True,

)
	