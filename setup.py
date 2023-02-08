from setuptools import find_packages, setup

with open('nso_api/version.py') as f:
	exec(f.read())

setup(
    name='nso-api',
    packages=find_packages(include=['nso_api']),
    version = __version__,
    description='Nintendo Switch Online API Python Library',
    author='jetsurf#8514, Andy#3003',
    license='GPL',
    install_requires=['requests'],
    setup_requires=[],
    tests_require=[''],
)
