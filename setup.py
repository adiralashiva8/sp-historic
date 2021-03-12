from setuptools import find_packages, setup

setup(
      name='sp-historic',
      version="0.1.1",
      author='Shiva Prasad Adirala',
      author_email='adiralashiva8@gmail.com',
      url='https://github.com/adiralashiva8/sp-historic',
      license='MIT',

      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,

      install_requires=[
          'robotframework',
          'config',
          'flask',
          'flask-mysqldb'
      ],
      entry_points={
          'console_scripts': [
              'sphistoric=sp_historic.app:main',
              'sphistoricsetup=sp_historic.setupargs:main',
              'sphistoricparser=sp_historic.parserargs:main',
          ]
      },
)
