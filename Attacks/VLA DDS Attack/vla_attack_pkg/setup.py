from setuptools import find_packages, setup

package_name = 'vla_attack_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='cyse-492-group13',
    maintainer_email='cyse-492-group13@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'attack_publisher = vla_attack_pkg.VLA_attack_publisher:main',
            'victim_subscriber = vla_attack_pkg.VLA_victim_subscriber:main',
        ],
    },
)
