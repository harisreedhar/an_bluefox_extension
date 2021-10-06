import bpy
from bpy.props import *
from animation_nodes . base_types import AnimationNode, VectorizedSocket

dataByIdentifier = {}

class BF_AlembicExporterNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_AlembicExporterNode"
    bl_label = "Alembic Exporter"
    bl_width_default = 160
    errorHandlingType = "EXCEPTION"

    useObjectList  : VectorizedSocket.newProperty()

    filePath           : StringProperty(name = "File Path", subtype ='FILE_PATH', default = "/tmp/my_cache", update = AnimationNode.refresh)
    executeFlag        : BoolProperty(default = False, update = AnimationNode.refresh)
    showSettings       : BoolProperty(name = "Settings", default = False, update = AnimationNode.refresh)
    startFrame         : IntProperty(name = "Start Frame", default = 1, update = AnimationNode.refresh)
    endFrame           : IntProperty(name = "End Frame", default = 250, update = AnimationNode.refresh)
    sequence           : BoolProperty(name = "As Sequence", default = False, update= AnimationNode.refresh)
    exportUVs          : BoolProperty(name = "UVs", default = True, update = AnimationNode.refresh)
    exportNormals      : BoolProperty(name = "Normals", default = True, update = AnimationNode.refresh)
    exportVertexColors : BoolProperty(name = "Vertex Colors", default = True, update = AnimationNode.refresh)
    applySubdivisions  : BoolProperty(name = "Apply Subdivisions", default = False, update = AnimationNode.refresh)
    curveAsMesh        : BoolProperty(name = "Curves as Mesh", default = False, update = AnimationNode.refresh)
    packUVs            : BoolProperty(name = "Pack UV islands", default = True, update = AnimationNode.refresh)

    def create(self):
        self.newInput(VectorizedSocket("Object", "useObjectList",
            ("Object", "object", dict(defaultDrawType = "PROPERTY_ONLY")),
            ("Objects", "object")))

    def draw(self, layout):
        col = layout.column(align = True)
        col.scale_y = 1.5
        row = col.row(align = True)
        self.invokeFunction(row, "invokeExportAlembic", description = "Export", text= "Export")

        col = layout.column(align = True)
        row = col.row(align = True)
        row.prop(self, "filePath", text="")
        row.prop(self, "showSettings", text = "", icon = "PREFERENCES")
        col.prop(self, "startFrame")
        col.prop(self, "endFrame")
        col.prop(self, "sequence")

        if self.showSettings:
            col = layout.column(align = True)
            for item in ["exportUVs", "exportNormals", "exportVertexColors",
                    "applySubdivisions", "curveAsMesh", "packUVs"]:
                col.prop(self, item)

    def execute(self, object):
        if self.executeFlag:
            dataByIdentifier[self.identifier] = object if self.useObjectList else [object]

    def invokeExportAlembic(self):
        self.executeFlag = True
        self.id_data.execute()

        object = dataByIdentifier.get(self.identifier)
        if object is not None:
            parameters = {
                'start': self.startFrame,
                'end': self.endFrame,
                'uvs': self.exportUVs,
                'packuv': self.packUVs,
                'normals': self.exportNormals,
                'vcolors': self.exportVertexColors,
                'apply_subdiv': self.applySubdivisions,
                'curves_as_mesh': self.curveAsMesh,
                'check_existing': False,
                'selected': True,
                'as_background_job': False,
                'visible_objects_only': False
            }
            exportAlembic(self.filePath, object, parameters, sequence = self.sequence)

        self.executeFlag = False
        self.delete()

    def delete(self):
        keys = list(dataByIdentifier.keys())
        for key in keys:
            if key.startswith(self.identifier):
                dataByIdentifier.pop(key)

def exportAlembic(filePath, objects, parameters, sequence = False):
    wm = bpy.context.window_manager
    wm.progress_begin(0, 100)
    currentSelected = bpy.context.selected_objects
    selectObjects(objects)

    if sequence:
        startFrame = parameters.get('start')
        endFrame = parameters.get('end')
        totalFrames = endFrame - startFrame + 1
        for frame in range(startFrame, endFrame + 1):
            _filePath = filePath + f"_{str(frame).zfill(4)}.abc"
            parameters['filepath'] = _filePath
            parameters['start'] = frame
            parameters['end'] = frame
            bpy.context.scene.frame_set(frame)
            bpy.ops.wm.alembic_export(**parameters)
            progress = int((frame / totalFrames) * 100)
            wm.progress_update(progress)
    else:
        wm.progress_update(99)
        _filePath = filePath + ".abc"
        parameters['filepath'] = _filePath
        bpy.ops.wm.alembic_export(**parameters)

    selectObjects(currentSelected)
    wm.progress_end()

def selectObjects(objects):
    bpy.ops.object.select_all(action = "DESELECT")
    if len(objects) == 0:
        bpy.context.view_layer.objects.active = None
    else:
        bpy.context.view_layer.objects.active = objects[0]
    for object in objects:
        object.select_set(True)
