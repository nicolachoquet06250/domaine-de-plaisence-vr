"""Geometry-only authoring checks; does not import or execute Blender."""
import ast, math, random
from pathlib import Path

path = Path(__file__).with_name('blender-vegetation-relief.py')
module = ast.parse(path.read_text())
names = {'vr_rect_distance', 'vr_estate_clearance', 'vr_height', 'vr_blade', 'vr_grass', 'vr_arrival_clearance'}
namespace = {'math': math, 'random': random, 'vr_stats': {}, 'vr_blade_mat': None}
geometry = {}


def mesh(asset, name, vertices, faces, material, colors=None):
    geometry.setdefault(asset, []).append((vertices, faces, colors))


namespace['vr_mesh'] = mesh
exec(compile(ast.Module(body=[n for n in module.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[]), str(path), 'exec'), namespace)
clearance = namespace['vr_estate_clearance']
for point in [(0, 0), (0, -25), (-12, -10), (12, 10), (14, -28), (0, 24), (-23, -18), (30, 0)]:
    assert clearance(*point) <= 0, ('hardscape must exclude grass', point)
for point in [(-33, 30), (33, -45), (26, 10), (10, 30), (-10, -42), (4.4, 8), (20.5, 12)]:
    assert clearance(*point) > 0, ('every separated lawn region must remain covered', point)

for asset, bounds, mask, seed, step, size in [
    ('estateLawnRelief', (-35, 35, -51, 39), clearance, 204709, .32, 18),
    ('arrivalLawnRelief', (-20, 20, -20, 20), namespace['vr_arrival_clearance'], 204710, .26, 20),
]:
    namespace['vr_grass'](asset, bounds, mask, seed, step, size)
    stats = namespace['vr_stats'][asset]
    assert stats['bladeCount'] > 9000
    assert stats['grassTiles'] <= 20
    assert stats['bladeTriangles'] < (175000 if asset.startswith('estate') else 70000)
    for vertices, faces, colors in geometry[asset]:
        assert len(vertices) % 7 == 0 and len(faces) % 6 == 0
        for i in range(0, len(vertices), 7):
            base, tip = vertices[i], vertices[i + 6]
            assert .0649 <= tip[1] - base[1] <= .1281
            for v in vertices[i:i + 7]:
                assert all(math.isfinite(n) for n in v)
                assert mask(v[0], v[2]) > 0, ('grass intersects hardscape', asset, v)
    print(asset, stats['bladeCount'], 'folded blades;', stats['bladeTriangles'], 'triangles;', stats['grassTiles'], 'chunks')

for x,z in [(-33,30),(33,-45),(26,10),(10,30),(-10,-42),(4.4,8),(20.5,12)]:
    assert any(abs(v[0]-x)<.75 and abs(v[2]-z)<.75 for chunk in geometry['estateLawnRelief'] for v in chunk[0][::7]), ('uncovered lawn',x,z)
print('Lawn regions, blade geometry, hardscape clearances and triangle budgets pass.')
