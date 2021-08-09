import bpy
from .. utils . module_util import installModule

class BF_InstallModule(bpy.types.Operator):
    bl_idname = 'an_bluefox_extension.install_module'
    bl_label = 'Install Python Module'
    bl_description = 'Installs given Python module with pip'
    bl_options = {'INTERNAL'}

    name: bpy.props.StringProperty(
        name = 'Module Name',
        description = 'Installs the given module')

    options: bpy.props.StringProperty(
        name = 'Command line options',
        description = 'Command line options for pip (e.g. "--no-deps -r")',
        default = '')

    reload_scripts: bpy.props.BoolProperty(
        name = 'Reload Scripts',
        description = 'Reloads Blender scripts upon successful installation',
        default = True)

    def execute(self, context):
        if len(self.name) > 0 and installModule(self.name, self.options):
            self.report({'INFO'}, f'Installed Python module: {self.name}')
            if self.reload_scripts:
                bpy.ops.script.reload()
        else:
            self.report({'ERROR'}, f'Unable to install Python module: {self.name}')
        return {'FINISHED'}
