from setuptools import setup


setup(
    name='ludwig',
    version='1.0.1',
    packages=['src'],
    install_requires=['psutil',
                      'pysftp',
                      'watchdog',
                      'numpy',
                      'pandas'],
    url='https://github.com/languagelearninglab/Ludwig',
    license='',
    author='Philip Huebner',
    author_email='info@philhuebner.com',
    description='Run Python jobs on Ludwig',
    entry_points={
        'console_scripts': [
            'ludwig=src.__main__:submit',
            'ludwig-local=src.__main__:run_on_host',
            'ludwig-stats=src.__main__:stats',
            'ludwig-status=src.__main__:status'
        ]
    }
)