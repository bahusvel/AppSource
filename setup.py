from setuptools import setup

setup(
    name='apps',
    version='0.1',
    py_modules=['apps', 'installer', 'gitcontroller'],
    install_requires=[
        'Click',
        'PyGithub'
    ],
    entry_points='''
        [console_scripts]
        apps=apps:apps
    ''',
)