from pathlib import Path
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
code=(ROOT/'scripts/blender-refined-export.py').read_text(encoding='utf-8-sig')
code=code.replace('artifacts/avatars/refined','artifacts/avatars/francois').replace('renaissance-refined.blend','renaissance-francois.blend')
exec(compile(code,'francois-export','exec'))
