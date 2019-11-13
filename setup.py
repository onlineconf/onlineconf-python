from setuptools import setup

setup(
    name='onlineconf',
    version='0.0.9',
    url='https://github.com/onlineconf/onlineconf-python',
    author='Mail.Ru Group',
    packages=['onlineconf'],
    entry_points={
        'console_scripts': ['fill_config=onlineconf.cli:main'],
    },
    install_requires=[
        'pure-cdb>=2.2.0,<3.0.0',
        'aiofiles>=0.4.0,<1.0.0',
        'PyYAML>=5.1,<6.0'
    ]
)
