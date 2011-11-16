from setuptools import setup, find_packages
import sys, os

version = '0.1'
long_description = open("README.txt").read()

setup(name='forrest',
      version=version,
      description="a simple file system db with a restful interface",
      long_description=long_description,
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Maurizio Lupo',
      author_email='maurizio.lupo@gmail.com',
      url='http://sithmel.bplogspot.com',
      license='gpl3',
      test_suite = "forrest.tests.suite",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
#          # -*- Extra requirements: -*-
          'PasteDeploy',
#          'httplib2,',
#          'paste',
      ],
      entry_points="""
      # -*- Entry points: -*-
      [paste.app_factory]
      fs = forrest.resources.fs:make_app_wsgi
      filedict = forrest.resources.filedict:make_app_wsgi
      ramdict = forrest.resources.ramdict:make_app_wsgi
      
      """,
      )
