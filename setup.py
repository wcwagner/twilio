from setuptools import setup

setup(
    name='twiliobd',
    packages=['twiliobd'],
    include_package_data=True,
    install_requires=[
        'flask',
    ],
    setup_requires=[
        'pytest-runner',
        'icalendar',
    ],
    tests_require=[
        'pytest',
    ],
)
