from setuptools import find_packages, setup
setup(
    name='nso-api',
    packages=find_packages(include=['nso_api']),
    version='0.9.1',
    description='Nintendo Switch Online API Python Library',
    author='jetsurf#8514, Andy#3003',
    license='GPL',
    install_requires=['requests'],
    setup_requires=[],
    tests_require=[''],
)
