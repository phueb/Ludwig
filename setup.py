from setuptools import setup

from src import PROJECT_NAME

setup(
    name=PROJECT_NAME.lower(),
    version='0.1',
    packages=['src'],
    url='https://github.com/languagelearninglab/LudwigCluster',
    license='',
    author='Philip Huebner',
    author_email='',
    description='Boilerplate for training neural networks on LudwigCluster'
)
