import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='python-aiotor',
    version='0.5.1',
    author='Davy Wybiral',
    author_email="davy.wybiral@gmail.com",
    description='asyncio Tor controller library',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wybiral/aiotor",
    packages=['aiotor'],
    install_requires=['cryptography'],
    license='MIT',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
