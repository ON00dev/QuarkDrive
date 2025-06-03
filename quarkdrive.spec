a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('extensions/*.pyd', 'extensions/'),
        ('lib/*.pyd', 'lib/'),  # Incluir o novo módulo
        ('gui/icons/*', 'gui/icons/'),
    ],
    hiddenimports=[
        'extensions.compression_module', 
        'extensions.hash_module',
        'windows_vfs_module',  # Novo módulo
        'platform'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)