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
        'Twisted==12.1.0',
        'argparse==1.2.1',
        'distribute==0.6.24',
        'wsgiref==0.1.2',
        'zope.interface==4.0.1',
        'redis',
    ],
    entry_points = {
        'console_scripts': [
            'bottu = bottu.cli:run',
        ],
    }
)
