from glob import glob

from setuptools import find_packages, setup

package_name = "robotics_sim"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
        ("share/" + package_name + "/config", glob("config/*.yaml")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Repository maintainers",
    maintainer_email="maintainers@example.org",
    description="Simulation-only safety gate and fake wheeled base",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "safety_gate = robotics_sim.safety_gate:main",
            "fake_base = robotics_sim.fake_base:main",
            "sim_environment = robotics_sim.sim_environment:main",
        ],
    },
)
