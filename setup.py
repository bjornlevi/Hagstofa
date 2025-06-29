from setuptools import setup, find_packages

setup(
    name='Hagstofan',
    version='0.1.0',
    description='Access and analyze data from the Hagstofan API',
    author='Björn Leví Gunnarsson',
    packages=find_packages(),
    install_requires=[
        'requests',
        'python-dateutil',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)
