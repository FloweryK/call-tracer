from setuptools import setup, find_packages

setup(
    name='callTracer',
    version='0.0.1',
    packages=find_packages(),
    install_requires=[
        'colorama',
    ],
    extras_require={
        'dev': [
            'pytest',
        ],
    },
)