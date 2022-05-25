from setuptools import find_packages, setup

from onlineconf import __version__ as version

setup(
    name="onlineconf",
    version=version,
    url="https://github.com/onlineconf/onlineconf-python",
    author="VK Group",
    packages=find_packages(),
    entry_points={
        "console_scripts": ["fill_config=onlineconf.cli:main"],
    },
    install_requires=[
        "pure-cdb>=2.2.0",
        "aiofiles>=0.4.0",
        "PyYAML>=5.1"
    ]
)
