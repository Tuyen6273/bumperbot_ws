from glob import glob
from setuptools import find_packages, setup

package_name = 'bumberbot_py_examples'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch',
        glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='tuyen',
    maintainer_email='tuyen@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'simple_publisher = bumberbot_py_examples.simple_publisher:main',
            'simple_subcriber = bumberbot_py_examples.simple_subcriber:main',
            'simple_parameter = bumberbot_py_examples.param_examples:main',
            'simple_turtle_kinematics = bumberbot_py_examples.simple_turtle_kinematics:main',
            'joystick_publisher = bumberbot_py_examples.joystick_publisher:main',
            'simple_tf_kinematics = bumberbot_py_examples.simple_tf_kinematics:main',
            'simple_service_server = bumberbot_py_examples.simple_service_server:main',
            'simple_service_client = bumberbot_py_examples.simple_service_client:main',
            'gemini_voice_controller = bumberbot_py_examples.gemini_voice_controller:main',
            'simple_lifecycle_node = bumberbot_py_examples.simple_lifecycle_node:main',
        ],
    },
)
