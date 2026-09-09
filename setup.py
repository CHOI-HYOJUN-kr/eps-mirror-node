from setuptools import find_packages, setup

setup(
    name="eps_mirror",
    version="0.2.0",
    packages=find_packages("src"),
    package_dir={"": "src"},
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/eps_mirror"]),
        ("share/eps_mirror", ["package.xml", "LICENSE"]),
        ("share/eps_mirror/launch", ["launch/mirror.launch.py"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Hyojun Choi",
    maintainer_email="CHOI-HYOJUN-kr@users.noreply.github.com",
    description="EPS Kinova trajectory routing",
    license="MIT",
    entry_points={"console_scripts": ["mirror_node = eps_mirror.mirror_node:main"]},
)
