from setuptools import setup, find_packages

setup(
    name="llm_client",
    version="0.1.0",
    description="Ollama-based LLM Chat Web Application",
    author="Tatsuhiko Nakabayashi",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "Flask>=2.3.3,<3.0.0",
        "Flask-SocketIO>=5.3.4,<6.0.0",
        "ollama>=0.1.3,<0.2.0",  # ollama-pythonから名前が変更
        "python-socketio>=5.8.0,<6.0.0",
        "requests>=2.31.0,<3.0.0",  # requestsの依存関係を明示
    ],
    extras_require={
        "test": [
            "pytest>=7.0.0,<8.0.0",
            "pytest-cov>=4.0.0,<5.0.0",  # カバレッジレポート用
            "requests-mock>=1.11.0,<2.0.0",  # HTTPリクエストのモック用
        ],
        "dev": [
            "black>=23.0.0,<24.0.0",  # コードフォーマット用
            "ruff>=0.1.0,<0.2.0",  # リンター用
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Topic :: Communications :: Chat",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
