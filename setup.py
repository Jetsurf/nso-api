from setuptools import find_packages, setup
setup(
    name='pynso',
    packages=find_packages(include=['pynso']),
    version='1.0.0',
    description='Nintendo Switch Online API Python Lirary',
    author='jetsurf#8514, Andy#3003',
    license='GPL',
    install_requires=['requests'],
    setup_requires=[],
    tests_require=[''],
)
