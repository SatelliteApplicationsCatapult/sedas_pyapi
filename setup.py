

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('HISTORY.md') as history_file:
    history = history_file.read()

requirements = []

setup(
    author="Wil Selwood",
    author_email="wil.selwood@sa.catapult.org.uk",
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.7',
    ],
    description="client library to easily access the SeDAS API",
    long_description=readme + '\n\n' + history,
    version='0.1.0',
    keywords='SeDAS API Client',
    name='getthestuff',
    packages=find_packages(include=['getthestuff']),
    install_requires=requirements,
    setup_requires=[],
    tests_require=['nose2', 'coverage'],
    test_suite='nose2.collector.collector',
    url='https://bitbucket.satapps.org/projects/SEN/repos/get_the_stuff',
)
