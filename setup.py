from setuptools import setup


setup(
    name='ludwigcluster',
    version='0.2',
    packages=['ludwigcluster'],
    install_requires=['psutil',
                      'pysftp',
                      'watchdog'],
    url='https://github.com/languagelearninglab/LudwigCluster',
    license='',
    author='Philip Huebner',
    author_email='info@philhuebner.com',
    description='Run Python jobs on multiple LudwigCluster nodes',
    entry_points={
        'console_scripts': [
            'ludwig=submit:main'
        ]
    }
)