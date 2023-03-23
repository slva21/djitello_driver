from setuptools import setup

setup(
    name='djitello_driver',
    version='0.0.1',
    packages=['djitello_driver'],
    install_requires=[
        'djitellopy'
    ],
    author='Your Name',
    author_email='your_email@example.com',
    description='A ROS driver for the DJI Tello drone using djitellopy library',
    license='MIT',
    keywords='ROS Tello DJI drone',
    url='https://github.com/your_username/djitello_driver',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
