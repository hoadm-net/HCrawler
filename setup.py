from setuptools import setup, find_packages

setup(
    name='hmd',
    version='0.0.1',
    packages=find_packages(
        where='hmd',
    ),
    package_dir={"": "hmd"}
)
