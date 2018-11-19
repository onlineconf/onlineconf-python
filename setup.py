from setuptools import setup

setup(
    name='onlineconf',
    version='0.0.4',
    url='https://gitlab.corp.mail.ru/myspb/common/onlineconf',
    author='mail.ru',
    packages=['onlineconf'],
    entry_points={
        'console_scripts': ['fill_config=onlineconf.cli:main'],
    },
    install_requires=[
        'pure-cdb==2.1.0',
        'aiofiles==0.3.2'
    ]
)
