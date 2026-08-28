# -*- mode: python -*-
import sys
sys.setrecursionlimit(50000)
block_cipher = None


a = Analysis(['String_line4.py'],
             pathex=['C:\\Users\\Insitu\\Documents\\GitHub\\String_line_ui'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='StringLineUI',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False )
