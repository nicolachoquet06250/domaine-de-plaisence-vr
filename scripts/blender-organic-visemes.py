from pathlib import Path
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
src=(ROOT/'scripts/blender-natural-visemes.py').read_text(encoding='utf-8-sig').replace("artifacts/avatars/natural","artifacts/avatars/organic").replace('scene.cycles.samples=12','scene.cycles.samples=6')
exec(compile(src,'organic-visemes','exec'))
