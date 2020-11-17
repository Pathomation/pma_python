import os
from setuptools import setup

def read(file_name):
    with open(os.path.join(os.path.dirname(__file__), file_name)) as f:
        return f.read()

def extract_version(v):
    idx1 = v.find("'")
    idx2 = v.rfind("'")
    id = ""
    if (idx1 > 0 and idx2 > 0):
        id = v[(idx1+1):]
        l = idx2 - idx1
        id = id[0:l-1]
    else:
        idx1 = v.find('"')
        idx2 = v.rfind('"')
        id = v[(idx1+1):]
        l = idx2 - idx1
        id = id[0:l-1]
    return id
	
setup(name='pma_python',
      version=extract_version(read("pma_python/version.py")),
      description='Universal viewing of digital microscopy, whole slide imaging and digital pathology data',
      long_description=read('long_desc.txt'),
      url='http://github.com/pathomation/pma_python',
      author='Pathomation',
      author_email='info@pathomation.com',
      license='http://free.pathomation.com/eula/',
      packages=['pma_python'],
      data_files=[('', ['long_desc.txt'])],
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Programming Language :: Python :: 3'],
      keywords='wsi whole slide imaging gigapixel microscopy histology pathology',
      install_requires=['pillow', 'requests', 'requests_toolbelt'],
      python_requires='>=3',  # assume this only works in Python 3
      zip_safe=False)

