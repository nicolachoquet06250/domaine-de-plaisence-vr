"""Reproducible local Blender MCP build of the approved arrival landscape."""
from pathlib import Path
root=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update/scripts')
namespace={'__name__':'__main__'}
for stage in ['stage-1','foliage','stage-2','stage-3','finalize','path-clearance']:
 path=root/('blender-landscape-'+stage+'.py')
 exec(compile(path.read_text(encoding='utf8'),str(path),'exec'),namespace)
for name in ['blender-royal-enclosure.py','blender-royal-estate-copy.py','blender-arrival-coach.py']:
 path=root/name
 exec(compile(path.read_text(encoding='utf8'),str(path),'exec'),namespace)
