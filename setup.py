from setuptools import setup

with open('long_desc.txt') as file:
    long_description = file.read()
	  
setup(name='pma_python',
      version='2.0.0.33',
      description='Universal viewing of digital microscopy, whole slide imaging and digital pathology data',
	  long_description=long_description,
      url='http://github.com/pathomation/pma_python',
      author='Pathomation',
	  author_email='info@pathomation.com',
      license='http://free.pathomation.com/eula/',
      packages=['pma_python'],
	  classifiers = [
		'Development Status :: 3 - Alpha', 
		'Programming Language :: Python :: 3'],
	  keywords='wsi whole slide imaging gigapixel microscopy histology pathology',
	  install_requires=['pillow', 'requests'],
	  python_requires='>=3',	# assume this only works in Python 3
      zip_safe=False)
