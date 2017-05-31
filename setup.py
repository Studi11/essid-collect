from setuptools import setup

setup(
    name="essid-collect",
    version="0.1",
    py_modules=["collect"],
    install_requires=[
        "Click",
    ],
    entry_points='''
        [console_scripts]
        collect=collect:main
    ''',
)
