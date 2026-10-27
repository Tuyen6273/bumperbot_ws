#!/usr/bin/env python3
"""Static syntax and expanded URDF checks; never starts robot nodes."""
import ast
import os
import re
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET
import yaml

root = Path(__file__).resolve().parents[1]
counts = Counter()
for path in (root / 'src').rglob('*'):
    if not path.is_file() or any(p in {'build', 'install', 'log', '__pycache__', '.pytest_cache'} for p in path.parts):
        continue
    if path.suffix == '.py':
        ast.parse(path.read_text(), filename=str(path))
        counts['Python'] += 1
    elif path.suffix in {'.yaml', '.yml'}:
        yaml.safe_load(path.read_text())
        counts['YAML'] += 1
    elif path.suffix in {'.xml', '.xacro', '.sdf', '.world', '.config'}:
        ET.parse(path)
        counts['XML/Xacro/SDF/world/config'] += 1
print(dict(counts))
program_count = 0
for cmake in (root / 'src').glob('*/CMakeLists.txt'):
    for block in re.findall(r'install\(PROGRAMS(.*?)DESTINATION', cmake.read_text(), re.S):
        for name in block.split():
            name = name.replace('${PROJECT_NAME}', cmake.parent.name)
            program = cmake.parent / name
            assert program.is_file() and os.access(program, os.X_OK), f'Missing executable permission: {program}'
            program_count += 1
print(f'{program_count} install(PROGRAMS) executable permissions PASS')

import xacro
model = root / 'src/bumperbot_description/urdf/bumperbot.urdf.xacro'
for is_sim in ('false', 'true'):
    doc = xacro.process_file(str(model), mappings={'is_sim': is_sim, 'is_ignition': 'false'})
    robot = ET.fromstring(doc.toxml())
    actual_joints = {j.attrib['name'] for j in robot.findall('joint')}
    controls = robot.findall('ros2_control')
    assert len(controls) == 1
    control = controls[0]
    joint_names = [j.attrib['name'] for j in control.findall('joint')]
    assert joint_names == ['wheel_right_base_joint', 'wheel_left_base_joint']
    assert set(joint_names) <= actual_joints
    plugin = control.findtext('hardware/plugin')
    expected = 'gz_ros2_control/GazeboSimSystem' if is_sim == 'true' else 'bumperbot_firmware/BumperbotInterface'
    assert plugin == expected, (plugin, expected)
    for mesh in robot.iter('mesh'):
        uri = mesh.attrib['filename']
        if uri.startswith('package://bumperbot_description/'):
            assert (root / 'src/bumperbot_description' / uri.split('package://bumperbot_description/', 1)[1]).is_file(), uri
    print(f'URDF is_sim={is_sim}: joints, plugin and mesh paths PASS')
print('Static checks PASS; this does not verify Jazzy runtime or physics.')
