from setuptools import setup, find_packages

setup(
    name="kararadar",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "dnspython",
        "pyyaml",
        "colorama",
        "pyfiglet",
    ],
    extras_require={"ai": ["ollama"]},
    entry_points={"console_scripts": ["kararadar=kararadar.main:main"]},
    python_requires=">=3.12",
    license="MIT",
)