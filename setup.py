from setuptools import setup, find_packages

setup(
    name="llm_client",
    version="0.1.0",
    description="Ollama-based LLM Chat Web Application",
    author="Tatsuhiko Nakabayashi",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "Flask>=2.3.3",
        "Flask-SocketIO>=5.3.4",
        "ollama-python>=0.1.2",
        "python-socketio>=5.8.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Communications :: Chat",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
