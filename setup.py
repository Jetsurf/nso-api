from setuptools import find_packages, setup
setup(
    name='pynso',
    packages=find_packages(include=['pynso']),
    version='0.1.0',
    description='Nintendo Switch Online API Python Lirary',
    author='Connor Meade',
    license='GPL',
    install_requires=[],
    setup_requires=['requests'],
    tests_require=[''],
    #test_suite='tests',
)
