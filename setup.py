import setuptools


with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="amazon-kinesis-analytics-realtime-anomaly-detection",
    version="1.0.0",

    description="An empty CDK Python app",
    long_description="Sample for the German article Anomalie-Erkennung für Echtzeit-Datenströme by Constantin Gonzalez and Florian Mair published in Big Data Insider.",
    long_description_content_type="text/markdown",

    author="Florian Mair",

    package_dir={"": "amazon-kinesis-analytics-realtime-anomaly-detection"},
    packages=setuptools.find_packages(where="amazon-kinesis-analytics-realtime-anomaly-detection"),

    install_requires=[
        "aws-cdk.core==1.65.0",

    ],

    python_requires=">=3.6",

    classifiers=[
        "Development Status :: 4 - Beta",

        "Intended Audience :: Developers",

        "License :: OSI Approved :: Apache Software License",

        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",

        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",

        "Typing :: Typed",
    ],
)
