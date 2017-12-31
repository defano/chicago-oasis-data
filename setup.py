from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='chicago-oasis-data',
    version='0.1.0',
    description='Chicago Oasis data generation tool.',
    long_description=readme,
    author='Matt DeFano',
    author_email='matt@defano.com',
    url='https://github.com/defano/chicago-oasis-data',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)