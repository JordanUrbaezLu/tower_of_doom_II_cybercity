"""Upstream Blender MCP, with a bounded response window for multi-still reviews.

Keep the upstream MCP protocol, command lock and error handling unchanged.
Only its hardcoded180second receive timeout is extended to600seconds, matching
the dedicated client's authoring window. Vendor/other-map files are read-only.
"""
from blender_mcp import server

original_receive = server.BlenderConnection.receive_full_response

class RenderResponseSocket:
    def __init__(self, socket):
        self.socket = socket

    def settimeout(self, seconds):
        self.socket.settimeout(600.0)

    def __getattr__(self, name):
        return getattr(self.socket, name)

def receive_render_response(self, socket, buffer_size=8192):
    return original_receive(self, RenderResponseSocket(socket), buffer_size)

server.BlenderConnection.receive_full_response = receive_render_response
server.main()
