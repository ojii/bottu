from setuptools import setup

setup(
    name='bottu',
    version='0.1',
    packages=['bottu'],
    url='',
    license='BSD',
    author='Jonas Obrist',
    author_email='ojiidotch@gmail.com',
    description='',
    install_requires=[
        'PyYAML==3.10',
        'Twisted',
        'argparse==1.2.1',
        'wsgiref==0.1.2',
        'zope.interface',
        'redis',
        'docopt'
    ],
    entry_points = {
        'console_scripts': [
            'bottu = bottu.cli:run',
        ],
    }
)
