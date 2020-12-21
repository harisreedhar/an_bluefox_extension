import bpy
from bpy.props import *
from animation_nodes . utils.depsgraph import getEvaluatedID
from animation_nodes . base_types import AnimationNode, VectorizedSocket

collisionShapeItems = [
    ("BOX", "Box", "", "NONE", 0),
    ("SPHERE", "Sphere", "", "NONE", 1),
    ("CAPSULE", "Capsule", "", "NONE", 2),
    ("CYLINDER", "Cylinder", "", "NONE", 3),
    ("CONE", "Cone", "", "NONE", 4),
    ("CONVEX_HULL", "Convex Hull", "", "NONE", 5),
    ("MESH", "Mesh", "", "NONE", 6)
]

class BF_RigidBodyTriggerNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_bf_RigidBodyTriggerNode"
    bl_label = "Rigidbody Trigger"
    bl_width_default = 160
    errorHandlingType = "EXCEPTION"
    codeEffects = [VectorizedSocket.CodeEffect]

    for attr in ["Object", "Enabled", "Threshold","Mass","Bounciness","Friction","LinearDamping",
                 "AngularDamping","CollisionMargin"]:
        exec("use{}List: VectorizedSocket.newProperty()".format(attr), globals(), locals())

    collisionShape: EnumProperty(name = "Collision Shape", default = "CONVEX_HULL",
        items = collisionShapeItems, update = AnimationNode.refresh)
    enableShape: BoolProperty(name = "Is Used", default = False, update = AnimationNode.refresh)
    enableDepsgraph: BoolProperty(name = "Depsgraph evaluation", default = False, update = AnimationNode.refresh)

    def create(self):
        self.newInput(VectorizedSocket("Object", "useObjectList",
            ("Object", "object", dict(defaultDrawType = "PROPERTY_ONLY")),
            ("Objects", "objects"), codeProperties = dict(allowListExtension = False)))
        toProp = lambda prop: [prop, "useObjectList"]

        self.newInput("Falloff", "Falloff", "falloff")
        self.newInput(VectorizedSocket("Float", toProp("useThresholdList"),
            ("Threshold", "threshold", dict(value = 0.5)),
            ("Thresholds", "thresholds")))

        self.newInput(VectorizedSocket("Boolean", toProp("useEnabledList"),
            ("Dynamic", "enable", dict(value = 1)),
            ("Dynamics", "enables")))
        self.newInput(VectorizedSocket("Float", toProp("useMassList"),
            ("Mass", "mass", dict(value = 1)),
            ("Masses", "mass")))
        self.newInput(VectorizedSocket("Float", toProp("useBouncinessList"),
            ("Bounciness", "bounciness", dict(value = 0)),
            ("Bouncinesses", "bounciness")))
        self.newInput(VectorizedSocket("Float", toProp("useFrictionList"),
            ("Friction", "friction", dict(value = 0.5)),
            ("Frictions", "friction")))
        self.newInput(VectorizedSocket("Float", toProp("useLinearDampingList"),
            ("Linear Damping", "linear_damping", dict(value = 0.040)),
            ("Linear Dampings", "linear_damping")))
        self.newInput(VectorizedSocket("Float", toProp("useAngularDampingList"),
            ("Angular Damping", "angular_damping", dict(value = 0.1)),
            ("Angular Dampings", "angular_damping")))
        self.newInput(VectorizedSocket("Float", toProp("useCollisionMarginList"),
            ("Collision Margin", "collision_margin", dict(value = 0.04)),
            ("Collision Margins", "collision_margin")))
        self.newInput("Boolean List", "Collections (20)", "collections")

        self.newOutput(VectorizedSocket("Object", "useObjectList",
            ("Object", "object", dict(defaultDrawType = "PROPERTY_ONLY")),
            ("Objects", "objects"), codeProperties = dict(allowListExtension = False)))

        for socket in self.inputs[3:]:
            socket.useIsUsedProperty = True
            socket.isUsed = False
        for socket in self.inputs[3:]:
            socket.hide = True

    def draw(self, layout):
        row = layout.row(align = True)
        row.prop(self, "collisionShape", text = "")
        row2 = row.row(align = True)
        testIcon = "LAYER_USED"
        if self.enableShape:
            testIcon = "LAYER_ACTIVE"
        row2.prop(self, "enableShape", text = "", icon = testIcon)
        row.active = self.enableShape

    def drawAdvanced(self, layout):
        layout.prop(self, "enableDepsgraph")

    def getExecutionCode(self, required):
        yield "rigid_body = self.getRigidBodyObject(object)"
        yield "if rigid_body is not None:"
        yield "    influence = self.evaluateFalloff(falloff, object)"
        yield "    rigid_body.kinematic = threshold >= influence"
        if self.enableShape: yield "    rigid_body.collision_shape = self.collisionShape"
        s = self.inputs[2:]
        if s[1].isUsed: yield "    rigid_body.enabled = enable"
        if s[2].isUsed: yield "    rigid_body.mass = mass"
        if s[3].isUsed: yield "    rigid_body.restitution = bounciness"
        if s[4].isUsed: yield "    rigid_body.friction = friction"
        if s[5].isUsed: yield "    rigid_body.linear_damping = linear_damping"
        if s[6].isUsed: yield "    rigid_body.angular_damping = angular_damping"
        if s[7].isUsed:
            yield "    bools = AN.data_structures.VirtualBooleanList.create(collections, False).materialize(20)"
            yield "    if bools.allFalse(): bools[0] = True"
            yield "    rigid_body.collision_collections = bools"

    def getRigidBodyObject(self, object):
        if object is None:
            return None
        if object.type != 'MESH':
            self.setErrorMessage('Object is not Mesh type')
        else:
            rigid_body = object.rigid_body
            if rigid_body is None:
                self.setErrorMessage('Object must contain rigidbody attribute')
                return None
            return rigid_body

    objectIndex = 0
    def evaluateFalloff(self, falloff, object):
        location = (0,0,0)
        if self.enableDepsgraph:
            location = getEvaluatedID(object).location
        else:
            location = object.location
        falloffEvaluator = self.getFalloffEvaluator(falloff)
        influence = falloffEvaluator(location, self.objectIndex)
        self.objectIndex += 1
        return influence

    def getFalloffEvaluator(self, falloff):
        try: return falloff.getEvaluator("LOCATION")
        except: self.raiseErrorMessage("This falloff cannot be evaluated for vectors")
