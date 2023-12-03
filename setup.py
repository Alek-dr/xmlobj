import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="xmlobj",
    version="1.2.2",
    author="Alexander Barmin",
    author_email="barmin1@mail.ru",
    description="xmlobj is simple utility to map xml file to python object",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    install_requires=["xmltodict>=0.13.0", "Jinja2>=3.1"],
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
