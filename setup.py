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
    install_requires=['psutil',
                      'pysftp',
                      'watchdog',
                      'numpy',
                      'pandas',
                      'cached_property'],
    url='https://github.com/phueb/Ludwig',
    license='',
    author='Philip Huebner',
    author_email='info@philhuebner.com',
    description='Run Python jobs on Ludwig',
    entry_points={
        'console_scripts': [
            'ludwig=ludwig.__main__:submit',
            'ludwig-local=ludwig.__main__:run_on_host',
            'ludwig-stats=ludwig.__main__:stats',
            'ludwig-status=ludwig.__main__:status',
            'ludwig-add-ssh-config=ludwig.__main__:add_ssh_config'
        ]
    }
)