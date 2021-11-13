from setuptools import setup

setup(
    name='sc8850-browser',
    version='0.0.1',    
    description='console based instruments browser for the Roland SC-8850.',
    url='https://github.com/SambaGodschynski/sc-8850',
    author='Samba Godschynski',
    author_email='johannes.unger@vstforx.de',
    license='MIT',
    packages=['.'],
    package_data={'': ['instruments-map.sc8850.json']},
    install_requires=['python-rtmidi',
                      'blessed',                     
                      ],

    classifiers=[
    ],
)