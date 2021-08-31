import bpy
import csv
import numpy as np
from bpy.props import *
from io import StringIO
from itertools import chain
from collections import defaultdict
from animation_nodes . base_types import AnimationNode

writeModeItems = {
    ("ROW", "Write by Row", "Write row by row", "", 0),
    ("COLUMN", "Write by Column", "Write column by column", "", 1)
    }

dialectTypeItems = {
    ("EXCEL", "Excel", "", "", 0),
    ("EXCEL-TAB", "Excel Tabs", "", "", 1),
    ("UNIX", "Unix", "", "", 2),
    ("CUSTOM", "Custom", "", "", 3),
    }

quotingTypeItems = {
    ("QUOTE_ALL", "All", "", "", 0),
    ("QUOTE_MINIMAL", "Minimal", "", "", 1),
    ("QUOTE_NONNUMERIC", "Non-Numeric", "", "", 2),
    ("QUOTE_NONE", "None", "", "", 3),
    }

class BF_CSV_WriterNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_CSV_WriterNode"
    bl_label = "CSV Writer"
    bl_width_default = 160

    textBlock: PointerProperty(name = "Output text block", type = bpy.types.Text)
    writeMode: EnumProperty(name = "Write Mode", default = "ROW", items = writeModeItems, update = AnimationNode.refresh)
    useFrameRange: BoolProperty(name = "Use frame range", description = "Append data in frame range", default = False, update = AnimationNode.refresh)
    startFrame: IntProperty(default = 1, update = AnimationNode.refresh)
    endFrame: IntProperty(default = 100, update = AnimationNode.refresh)
    socketAmount: IntProperty(default = 1, min=1, update = AnimationNode.refresh)

    dialectType: EnumProperty(name = "Dialect", default = "EXCEL", items = dialectTypeItems, update = AnimationNode.refresh)
    delimiter: StringProperty(name = 'Delimiter', default = ';', update = AnimationNode.refresh)
    quoteChar: StringProperty(name = 'Quote Char', default = '"', update = AnimationNode.refresh)
    quoting: EnumProperty(name = "Quoting", default = "QUOTE_MINIMAL", items = quotingTypeItems, update = AnimationNode.refresh)

    nodeCache = defaultdict(None)

    def create(self):
        socketType = "Generic" if self.writeMode == "ROW" else "Generic List"
        for i in range(self.socketAmount):
            self.newInput(socketType, f"Data {i}", f"data_{i}")
        self.newOutput("Text Block", "Text Block", "textBlock")

    def draw(self, layout):
        col = layout.column(align = True)
        row = col.row(align = True)
        if self.textBlock is None:
            self.invokeFunction(row, "createNewTextBlock", icon="ADD")
        row.prop(self, "textBlock", text="")

        col = layout.column(align = True)
        row = col.row(align = True)
        row.prop(self, "writeMode", text = "")
        row.prop(self, "useFrameRange", text = "", icon = "PREVIEW_RANGE")

        if self.useFrameRange:
            col.prop(self, "startFrame", text='Start Frame')
            col.prop(self, "endFrame", text='End Frame')

        col = col.column(align = True)
        col.scale_y = 1.5
        row = col.row(align = True)
        appendFunctionName = "writeCSVRange" if self.useFrameRange else "writeCSV"
        self.invokeFunction(row, appendFunctionName, description="Append input data", text="Append", icon="GREASEPENCIL")
        self.invokeFunction(row, "clearCSV", description="Clear all text", text="Clear", icon="TRASH")

        col = layout.column(align = True)
        row = col.row(align = True)
        row.prop(self, "socketAmount", text="Amount")

    def drawAdvanced(self, layout):
        layout.prop(self, "dialectType")
        if self.dialectType == "CUSTOM":
            layout.prop(self, "delimiter")
            layout.prop(self, "quoteChar")
            layout.prop(self, "quoting")

    def execute(self, *args):
        self.nodeCache[self.identifier] = args
        return self.textBlock

    def createNewTextBlock(self):
        textBlock = bpy.data.texts.new(name = "data")
        self.textBlock = textBlock

    def writeCSV(self):
        data = self.nodeCache.get(self.identifier)
        if data is None or self.textBlock is None:
            return
        settings = [self.delimiter, self.quoteChar, self.quoting]
        data = [np.array(i).tolist() for i in data if i is not None] # convert to python like data
        formatter = ArgsToCSV(writeBy=self.writeMode, dialectType=self.dialectType, customDialect=settings)
        output = ""
        output += formatter.stringify(*data)
        self.textBlock.write(output)

    def writeCSVRange(self):
        start = min(self.startFrame, self.endFrame)
        end = max(self.startFrame, self.endFrame)
        for i in range(start, end + 1):
            bpy.context.scene.frame_set(i)
            self.writeCSV()

    def clearCSV(self):
        if self.textBlock is not None:
            self.textBlock.clear()

# modified from https://gist.github.com/sloev/1625dd0020bb84140afcb2d2cb741ef1
class ArgsToCSV:
    def __init__(self, writeBy="ROW", dialectType="excel", customDialect=None):
        self.buffer = StringIO()
        if dialectType == "CUSTOM":
            self.writer = csv.writer(self.buffer,
                                     delimiter=customDialect[0],
                                     quotechar=customDialect[1],
                                     quoting=eval(f"csv.{customDialect[2]}"))
        else:
            self.writer = csv.writer(self.buffer, dialect = dialectType.lower())
        self.writeBy = writeBy
        self.value = ""

    def writeRow(self, data):
        self.writer.writerow(data)
        value = self.buffer.getvalue().strip("\r\n")
        self.buffer.seek(0)
        self.buffer.truncate(0)
        return value + "\n"

    def stringify(self, *args):
        if self.writeBy == "ROW":
            self.value += self.writeRow(args)
        elif self.writeBy == "COLUMN":
            args = list(chain.from_iterable([args]))
            for row in zip(*args):
                self.value += self.writeRow(row)
        return self.value
