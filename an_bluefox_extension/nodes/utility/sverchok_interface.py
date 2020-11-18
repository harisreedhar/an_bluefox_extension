import bpy
from bpy.props import *
from collections import defaultdict
from animation_nodes . sockets.info import toIdName
from animation_nodes . base_types import AnimationNode

dataByIdentifier = defaultdict(None)

dataDirectionItems = {
    ("IMPORT", "Sverchok Import", "Receive data from Sverchok", "IMPORT", 0),
    ("EXPORT", "Sverchok Export", "Send data to Sverchok", "EXPORT", 1) }

class BF_SverchokInterfaceNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_SverchokInterfaceNode"
    bl_label = "SV_Data"
    bl_width_default = 180
    dynamicLabelType = "ALWAYS"
    errorHandlingType = "EXCEPTION"

    def checkedPropertiesChanged(self, context):
        if self.getTextObject() is not None:
            self.generateScript()
        AnimationNode.refresh(self)

    onlySearchTags = True
    searchTags = [(name, {"dataDirection" : repr(type)}) for type, name, _,_,_ in dataDirectionItems]

    dataDirection: EnumProperty(name = "Data Direction", default = "IMPORT",
        items = dataDirectionItems, update = checkedPropertiesChanged)

    amount: IntProperty(name = "Amount", default = 1, min = 1, update = checkedPropertiesChanged)

    def create(self):
        if self.dataDirection == "IMPORT":
            self.newOutput("Generic", "Raw List", "value", hide = True)
            for i in range(self.amount):
                self.newOutput("Generic", f"data_{i}", f"data_{i}")
        if self.dataDirection == "EXPORT":
            for i in range(self.amount):
                self.newInput("Generic", f"data_{i}", f"data_{i}")

    def draw(self, layout):
        layout.prop(self, "dataDirection", text = "")
        layout.prop(self, "amount", text = "Amount")
        row2 = layout.row(align = True)
        if self.getTextObject() is None:
            self.invokeFunction(row2, "generateTextFile", text = "Generate Script",
                    description = "Generate script for sverchok", icon = "TEXT")
        else:
            row2.label(text = self.getTextName(), icon = "TEXT")

    def drawLabel(self):
        for item in dataDirectionItems:
            if self.dataDirection == item[0]: return item[1]

    def generateScript(self):
        nodeTreeName = str(self.id_data.name)
        nodeName = str(self.name)
        code = ""

        if self.dataDirection == "IMPORT":
            code = '"""\n'
            for i in range(self.amount):
                code += f"in data_{i} s\n"
            code += '"""\n'
            code += "container = ["
            for i in range(self.amount):
                if i == self.amount - 1:
                    code += f"data_{i}"
                else:
                    code += f"data_{i}, "
            code += "]\n"
            code += f'anTree = bpy.data.node_groups.get("{nodeTreeName}")\n'
            code += 'if anTree:\n'
            code += f'\tanNode = anTree.nodes.get("{nodeName}")\n'
            code += '\tif anNode:\n'
            code += '\t\tanNode.setValue(container)\n'

        elif self.dataDirection == "EXPORT":
            code = '"""\n'
            code += 'in input s\n'
            for i in range(self.amount):
                code += f"out data_{i} s\n"
            code += '"""\n\n'
            for i in range(self.amount):
                code += f'data_{i} = []\n'
            code += f'\nanTree = bpy.data.node_groups.get("{nodeTreeName}")\n'
            code += 'if anTree:\n'
            code += f'\tanNode = anTree.nodes.get("{nodeName}")\n'
            code += '\tif anNode:\n'
            code += '\t\tcontainer = anNode.getValue()\n'
            code += '\t\tif container:\n'
            for i in range(self.amount):
                code += f'\t\t\tdata_{i} = [container[{i}]]\n'

        text = self.getTextObject()
        if text is not None:
            text.clear()
            text.write(code)
            return True
        else:
            self.raiseErrorMessage("No Script Found")
            return False

    def generateTextFile(self):
        bpy.data.texts.new(self.getTextName())
        return self.generateScript()

    def getTextObject(self):
        return bpy.data.texts.get(self.getTextName())

    def getTextName(self):
        if self.dataDirection == "IMPORT":
            return "Import_Script_" + self.name + ".py"
        elif self.dataDirection == "EXPORT":
            return "Export_Script_" + self.name + ".py"

    def execute(self, *args):
        if self.dataDirection == "IMPORT":
            value = self.getValue()
            result = [value]
            for i in range(self.amount):
                result.append(self.processImportedValue(value, i))
            return tuple(result)
        elif self.dataDirection == "EXPORT":
            self.setValue(args)

    def processImportedValue(self, value, index):
        try:
            if type(value[index][0]) is list:
                flat_list = [item for i in value[index] for item in i]
                return flat_list
            return value[index]
        except:
            return None

    def delete(self):
        textObject = self.getTextObject()
        if textObject is not None:
            bpy.data.texts.remove(textObject)

    def setValue(self, value):
        dataByIdentifier[self.identifier] = value

    def getValue(self):
        return dataByIdentifier.get(self.identifier)

    @property
    def value(self):
        return self.getValue()

    @value.setter
    def value(self, value):
        self.setValue(value)
