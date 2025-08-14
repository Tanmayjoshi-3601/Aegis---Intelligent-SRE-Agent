from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="aegis-sre-agent",
    version="1.0.0",
    author="Aegis SRE Team",
    author_email="sre-support@yourcompany.com",
    description="An intelligent Site Reliability Engineering (SRE) agent with ML-powered anomaly detection and automated mitigation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourcompany/aegis-sre-agent",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Systems Administration",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.2.0",
            "pytest-cov>=3.0.0",
            "pytest-mock>=3.6.0",
            "black>=21.0.0",
            "flake8>=4.0.0",
            "mypy>=0.910",
            "pre-commit>=2.15.0",
        ],
        "dashboard": [
            "streamlit>=1.30.0",
            "plotly>=5.18.0",
            "altair>=5.2.0",
        ],
        "ml": [
            "tensorflow>=2.8.0",
            "torch>=1.10.0",
            "xgboost>=1.5.0",
            "lightgbm>=3.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "aegis-dashboard=dashboard_server_simple:main",
            "aegis-agent=sre_agent_orchestrator:main",
            "aegis-stream=streaming_integration:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.yaml", "*.yml", "*.sql", "*.html", "*.css", "*.js"],
    },
    keywords="sre, site reliability engineering, anomaly detection, machine learning, monitoring, automation",
    project_urls={
        "Bug Reports": "https://github.com/yourcompany/aegis-sre-agent/issues",
        "Source": "https://github.com/yourcompany/aegis-sre-agent",
        "Documentation": "https://github.com/yourcompany/aegis-sre-agent/docs",
    },
) 