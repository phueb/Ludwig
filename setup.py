from setuptools import setup


setup(
    name='ludwig',
    version='1.0.0',
    packages=['ludwig'],
    install_requires=['psutil',
                      'pysftp',
                      'watchdog',
                      'numpy',
                      'pandas',
                      'cached_property'],
    url='https://github.com/languagelearninglab/Ludwig',
    license='',
    author='Philip Huebner',
    author_email='info@philhuebner.com',
    description='Run Python jobs on Ludwig',
    entry_points={
        'console_scripts': [
            'ludwig=ludwig.__main__:submit',
            'ludwig-local=ludwig.__main__:run_on_host',
            'ludwig-stats=ludwig.__main__:stats',
            'ludwig-status=ludwig.__main__:status'
        ]
    }
)