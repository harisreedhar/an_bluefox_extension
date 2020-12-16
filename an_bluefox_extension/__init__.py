'''
Copyright (C) 2020 <Harisreedhar>
<bluefoxcreationz@gmail.com>

Created by <Harisreedhar>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

bl_info = {
    "name": "AN Bluefox extension",
    "author": "Harisreedhar",
    "version": (1, 0, 0),
    "blender": (2, 90, 0),
    "location": "Animation Nodes",
    "description": "Extension For Animation Nodes.",
    "warning": "This addon is still in development",
    "doc_url": "",
    "tracker_url": "",
    "category": "Nodes",
}

import bpy
import addon_utils
from . import auto_load

try: import animation_nodes
except:
    animation_nodes = addon_utils.enable("animation_nodes", default_set = False, persistent = True)
    if not animation_nodes:
        raise Exception("Could not load Animation Nodes.")

auto_load.init()

animation_nodes.sockets.info.updateSocketInfo()

def register():
    auto_load.register()

def unregister():
    auto_load.unregister()
