from setuptools import setup, find_packages

setup(
    name="nlp-broker",
    version='0.3.0',
    author="Ubiquitous Knowledge Processing (UKP) Lab",
    author_email="dennis.zyska@tu-darmstadt.de",
    description="A broker for natural language processing tasks",
    long_description="README.md",
    packages=find_packages(),
    install_requires=[
        "python-socketio[client]",
        "python-arango",
        "flask-socketio",
        "pycryptodome",
        "numpy",
    ],
    python_requires=">=3.10",
)
