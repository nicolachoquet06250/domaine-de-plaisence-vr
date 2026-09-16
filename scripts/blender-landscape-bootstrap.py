import bpy, importlib.util, os
from pathlib import Path
path=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/scripts/addons/blender_mcp.py'
spec=importlib.util.spec_from_file_location('landscape_mcp',str(path));addon=importlib.util.module_from_spec(spec);spec.loader.exec_module(addon)
addon.register()
print('Landscape Blender MCP ready',flush=True)
