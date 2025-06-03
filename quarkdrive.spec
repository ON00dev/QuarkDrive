a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('extensions/*.pyd', 'extensions/'),  # Windows
        ('extensions/*.so', 'extensions/'),   # Linux
    ],
    hiddenimports=['extensions.compression_module', 'extensions.hash_module'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)