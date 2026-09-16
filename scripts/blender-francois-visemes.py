from pathlib import Path
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
code=(ROOT/'scripts/blender-natural-visemes.py').read_text(encoding='utf-8-sig').replace('artifacts/avatars/natural','artifacts/avatars/francois')
exec(compile(code,'francois-visemes','exec'))
