# commandPort -n "localhost:7001" -stp "mel";
# (connects Maya to VS Code)

import maya.cmds as mc
import maya.mel as mel
from maya.OpenMaya import MVector
import maya.OpenMayaUI as omui
from PySide2.QtWidgets import QVBoxLayout, QWidget, QPushButton, QMainWindow, QHBoxLayout, QGridLayout, QLineEdit, QLabel, QSlider
from PySide2.QtCore import Qt
from shiboken2 import wrapInstance

class TrimSheetBuilder(QWidget):
    def __init__(self):
        mainWindow: QMainWindow = TrimSheetBuilder.GetMayaMainWindow()

        for existing in mainWindow.findChildren(QWidget, TrimSheetBuilder.GetWindowUniqueID()):
            existing.deleteLater()

        super().__init__(parent=mainWindow)

        self.setWindowTitle("Trim Sheet Builder")
        self.setWindowFlags(Qt.Window)
        self.setObjectName(TrimSheetBuilder.GetWindowUniqueID())

        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)

        self.shell = []
        self.CreateInitializationSection()
        self.CreateManipulationSection()

    def FillShellToU1V1(self):
        width, height = self.GetShellSize()
        su = 1 / width
        sv = 1 / height
        self.ScaleShell(su, sv)
        self.MoveShellToOrigin()

    def GetShellSize(self):
        min, max = self.GetShellBounds()
        height = max[1] - min[1]
        width = max[0] - min[0]

        return width, height

    def ScaleShell(self, u, v):
        mc.polyEditUV(self.shell, su = u, sv = v, r=True)

    def MoveShell(self, u, v):
        width, height = self.GetShellSize()
        uAmt = u * width
        vAmt = v * height
        mc.polyEditUV(self.shell, u = uAmt, v = vAmt)


    def CreateManipulationSection(self):
        sectionLayout = QVBoxLayout()
        self.masterLayout.addLayout(sectionLayout)

        turnBtn = QPushButton("Turn")
        turnBtn.clicked.connect(self.TurnShell)
        sectionLayout.addWidget(turnBtn)

        backToOriginBtn = QPushButton("Back to Origin")
        backToOriginBtn.clicked.connect(self.MoveShellToOrigin)
        sectionLayout.addWidget(backToOriginBtn)

        fillU1V1Btn = QPushButton("Fill UV Space")
        fillU1V1Btn.clicked.connect(self.FillShellToU1V1)
        sectionLayout.addWidget(fillU1V1Btn)

        halfUBtn = QPushButton("Half U")
        halfUBtn.clicked.connect(lambda : self.ScaleShell(0.5, 1))
        sectionLayout.addWidget(halfUBtn)

        halfVBtn = QPushButton("Half V")
        halfVBtn.clicked.connect(lambda : self.ScaleShell(1, 0.5))
        sectionLayout.addWidget(halfVBtn)

        doubleUBtn = QPushButton("Double U")
        doubleUBtn.clicked.connect(lambda : self.ScaleShell(2, 1))
        sectionLayout.addWidget(doubleUBtn)

        DoubleVBtn = QPushButton("Double V")
        DoubleVBtn.clicked.connect(lambda : self.ScaleShell(1, 2))
        sectionLayout.addWidget(DoubleVBtn)

        moveSection = QGridLayout()
        sectionLayout.addLayout(moveSection)

        moveUpBtn = QPushButton("^")
        moveUpBtn.clicked.connect(lambda : self.MoveShell(0, 1))
        moveSection.addWidget(moveUpBtn, 0, 1)

        moveDownBtn = QPushButton("v")
        moveDownBtn.clicked.connect(lambda : self.MoveShell(0, -1))
        moveSection.addWidget(moveDownBtn, 2, 1)

        moveLeftBtn = QPushButton("<")
        moveLeftBtn.clicked.connect(lambda : self.MoveShell(-1, 0))
        moveSection.addWidget(moveLeftBtn, 1, 0)

        moveRightBtn = QPushButton(">")
        moveRightBtn.clicked.connect(lambda : self.MoveShell(1, 0))
        moveSection.addWidget(moveRightBtn, 1, 2)

    def GetShellBounds(self):
        uvs = mc.polyListComponentConversion(self.shell, toUV=True)
        uvs = mc.ls(uvs, fl=True)
        firstUV = mc.polyEditUV(uvs[0], q=True)
        minU = firstUV[0]
        maxU = firstUV[0]
        minV = firstUV[1]
        maxV = firstUV[1]

        for uv in uvs:
            uvCoord = mc.polyEditUV(uv, q=True)
            if uvCoord[0] < minU:
                minU = uvCoord[0]
            
            if uvCoord[0] > maxU:
                maxU = uvCoord[0]

            if uvCoord[1] < minV:
                minV = uvCoord[1]

            if uvCoord[1] > maxV:
                maxV = uvCoord[1]
            
        return [minU, minV], [maxU, maxV]


    def MoveShellToOrigin(self):
        minCoord, maxCoord = self.GetShellBounds()
        mc.polyEditUV(self.shell, u=-minCoord[0], v=-minCoord[1])


    def TurnShell(self):
        mc.select(self.shell, r=True)
        mel.eval(f"polyRotateUVs 90 0")

    def CreateInitializationSection(self):
        sectionLayout = QHBoxLayout()
        self.masterLayout.addLayout(sectionLayout)

        selectShellBtn = QPushButton("Select Shell")
        selectShellBtn.clicked.connect(self.SelectShell)
        sectionLayout.addWidget(selectShellBtn)

        unfoldBtn = QPushButton("Unfold")
        unfoldBtn.clicked.connect(self.UnfoldShell)
        sectionLayout.addWidget(unfoldBtn)

        cutAndUnfoldBtn = QPushButton("Cut and Unfold")
        cutAndUnfoldBtn.clicked.connect(self.CutAndUnfoldShell)
        sectionLayout.addWidget(cutAndUnfoldBtn)

        unitizeBtn = QPushButton("Unitize")
        unitizeBtn.clicked.connect(self.UnitizeShell)
        sectionLayout.addWidget(unitizeBtn)

    def UnitizeShell(self):
        edges = mc.polyListComponentConversion(self.shell, toEdge=True)
        edges = mc.ls(edges, fl=True)

        sewedEdges = []
        for edge in edges:
            vertices = mc.polyListComponentConversion(edge, toVertex=True)
            vertices = mc.ls(vertices, fl=True)

            UVs = mc.polyListComponentConversion(edge, toUV=True)
            UVs = mc.ls(UVs, fl=True)

            if len(UVs) == len(vertices):
                sewedEdges.append(edge)

        mc.polyForceUV(self.shell, unitize=True)
        mc.polyMapSewMove(sewedEdges)
        mc.u3dLayout(self.shell)

    def CutAndUnfoldShell(self):
        edges = mc.ls(sl=True)
        mc.polyProjection(self.shell, type="Planar", md="c")
        mc.polyMapCut(edges)
        mc.u3dUnfold(self.shell)
        mel.eval("texOrientShells")

    def UnfoldShell(self):
        mc.polyProjection(self.shell, type="Planar", md="c")
        mc.u3dUnfold(self.shell)
        mel.eval("texOrientShells")

    def SelectShell(self):
        self.shell = mc.ls(sl=True, fl=True)

    @staticmethod
    def GetMayaMainWindow():
        mainWindow = omui.MQtUtil.mainWindow()
        return wrapInstance(int(mainWindow), QMainWindow)
    
    @staticmethod
    def GetWindowUniqueID():
        return "eda093110b94cc2f0e72380fd823dd54"
    
def Run():    
    TrimSheetBuilder().show()