from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='ocean_hazard_monitoring',
    version='0.1.0',
    description='Integrated platform for real-time, community-powered ocean hazard monitoring with AI/NLP analytics',
    author='Ocean Hazard Monitoring Team',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=7.3.0',
            'flake8>=6.0.0',
            'black>=23.3.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'ohm-run=ocean_hazard_monitoring.main:run',
        ],
    },
    python_requires='>=3.9',
)