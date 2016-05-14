from setuptools import setup


def get_version():
    return open('cfpp/_version.py').readline().strip().strip('"')


setup(
    name='cfpp',
    version=get_version(),
    description='Adds helpful "extrinsic" functions to CloudFormation templates.',
    long_description=open('README.rst').read(),
    author='Doug Coker',
    author_email='dcoker@gmail.com',
    url='https://github.com/dcoker/cfpp/',
    include_package_data=False,
    license='https://www.apache.org/licenses/LICENSE-2.0',
    packages=[
        'cfpp'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2.7'
    ],
    zip_safe=False,
    install_requires=[
        'boto3>=1.3.0',
    ],
    test_suite='tests.test_cfpp',
    entry_points={
        'console_scripts': [
            'cfpp=cfpp.__main__:main'
        ]
    },
)
