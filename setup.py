from setuptools import setup

from ludwig import __name__, __version__

setup(
    name=__name__,
    version=__version__,
    packages=[__name__],
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        'Intended Audience :: Science/Research'],
    pyython_requires='>=3.6.8',
    install_requires=['psutil==5.8.0',
                      'pysftp==0.2.9',
                      'PyNaCl==1.4.0',
                      'cryptography==39.0.1',
                      'watchdog==2.0.1',
                      'paramiko==2.10.1',
                      'numpy',
                      'pandas',
                      'cached_property',
                      'PyYAML==5.4.1',
                      ],
    url='https://github.com/phueb/Ludwig',
    license='',
    author='Philip Huebner',
    author_email='info@philhuebner.com',
    description='Run Python jobs on UIUC Language Learning Lab machines',
    entry_points={
        'console_scripts': [
            'ludwig=ludwig.__main__:submit',
            'ludwig-status=ludwig.__main__:status',
        ]
    }
)