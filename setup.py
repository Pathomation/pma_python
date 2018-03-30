from setuptools import setup

setup(name='pma-python',
      version='0.1',
      description='Python wrapper library for PMA.start',
      url='http://github.com/pathomation/pma-python',
      author='Wim Waelput',
      license='Pathomation',
      packages=['pma-python'],
      install_requires=[
          'PIL', 'requests'
      ],
      zip_safe=False)
