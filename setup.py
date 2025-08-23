from setuptools import setup, find_packages

APP = ['src/main.py']  # Main entry point
DATA_FILES = [
    ('src', ['src/__init__.py']),
    ('src/gui', ['src/gui/__init__.py']),
    ('src/gui/music', ['src/gui/music/__init__.py']),
    ('src/notation', ['src/notation/__init__.py']),
    ('src/core', ['src/core/__init__.py']),
    ('src/midi', ['src/midi/__init__.py']),
    ('src/audio', ['src/audio/__init__.py']),
    ('src/plugins', ['src/plugins/__init__.py']),
]

OPTIONS = {
    'argv_emulation': True,
    'iconfile': None,  # You can add a .icns icon here if you have one
    'packages': ['src', 'src.gui', 'src.gui.music', 'src.notation', 'src.core', 'src.midi', 'src.audio', 'src.plugins'],
    'includes': ['PyQt6', 'numpy', 'music21', 'rtmidi', 'osc', 'sounddevice'],
    'plist': {
        'CFBundleName': 'ONOTE',
        'CFBundleDisplayName': 'ONOTE',
        'CFBundleIdentifier': 'com.onote.app',
        'CFBundleVersion': '2.0.0',
        'CFBundleShortVersionString': '2.0.0',
        'NSHighResolutionCapable': True,
    },
}

setup(
    name="ONOTE",
    version="2.0.0",
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    install_requires=[
        "PyQt6>=6.4.0",
        "PyQt6-Qt6>=6.4.0",
        "PyQt6-sip>=13.4.0",
        "python-rtmidi>=1.5.0",
        "numpy>=1.21.0",
        "music21>=9.1.0",
        "python-osc>=1.8.1",
        "sounddevice>=0.4.6",
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "mypy>=1.0.0",
        "black>=22.0.0",
        "flake8>=4.0.0",
    ],
    python_requires=">=3.8",
    author="Gil Dor",
    description="Object-Oriented Music Notation Software",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
) 