import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'robotriage_core'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='gxl077',
    maintainer_email='gxl077@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'decision_publisher_node = robotriage_core.decision_publisher_node:main',
            'task_planner_node = robotriage_core.task_planner_node:main',
            'execution_manager_node = robotriage_core.execution_manager_node:main',
            'evaluation_node = robotriage_core.evaluation_node:main',
            'experiment_logger_node = robotriage_core.experiment_logger_node:main',
        ],
    },
)
