from setuptools import setup

setup(
    name='flutter',
    maintainer='Andrew Aldridge',
    maintainer_email='i80and@foxquill.com',
    description='A magical PEP-484 type-checking deserialization library for Python',
    long_description=open('README.rst').read(),
    version='0.0+dev',
    license='ISC',
    url='https://github.com/i80and/flutter',
    install_requires=['typing_extensions'],
    packages=['flutter'],
    package_data={'flutter': ['py.typed']},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)'
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Object Brokering'
    ]
)
