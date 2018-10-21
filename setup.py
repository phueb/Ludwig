from setuptools import setup


setup(
    name='ludwigcluster',
    version='0.1dev',
    packages=['ludwigcluster'],
    install_requires=['psutil',
                      'pysftp',
                      'termcolor'],
    url='https://github.com/languagelearninglab/LudwigCluster',
    license='',
    author='Philip Huebner',
    author_email='info@philhuebner.com',
    description='Train GPU accelerated neural networks on multiple LudwigCluster nodes'
)