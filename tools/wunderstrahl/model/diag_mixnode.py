"""MCP diagnostic (read-only): how ShaderNodeMix sockets resolve by name in this Blender build."""
import bpy
mat = bpy.data.materials.new('diag mix'); mat.use_nodes = True
n = mat.node_tree.nodes.new('ShaderNodeMix'); n.data_type = 'RGBA'
print('inputs', [(s.name, s.identifier, s.type, s.enabled) for s in n.inputs])
print('outputs', [(s.name, s.identifier, s.type, s.enabled) for s in n.outputs])
print("inputs['A'] ->", n.inputs['A'].identifier, n.inputs['A'].type, "outputs['Result'] ->", n.outputs['Result'].identifier)
bpy.data.materials.remove(mat)
