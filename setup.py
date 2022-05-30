from setuptools import find_packages, setup

__version__ = "0.1.0"

setup(
    name="onlineconf",
    version=__version__,
    url="https://github.com/onlineconf/onlineconf-python",
    author="VK Group",
    packages=find_packages(),
    entry_points={
        "console_scripts": ["fill_config=onlineconf.cli:main"],
    },
    install_requires=["pure-cdb>=2.2.0", "aiofiles>=0.4.0", "PyYAML>=5.1"],
)
