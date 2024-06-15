from setuptools import setup, find_packages

setup(
    name='call-tracer',
    version='1.0.0',
    author='FloweryK',
    author_email='flowerk94@gmail.com',description='A library for tracing function calls with depth control and filtering.',
    # long_description=open('README.md').read(),
    # long_description_content_type='text/markdown',
    url='https://github.com/FloweryK/call-tracer',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
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