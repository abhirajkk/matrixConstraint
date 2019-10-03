"""
author: abhirajkk@gmial.com
version: 0.01

Basic version of constraints in maya using matrix nodes

ToDo:
    add weight attribute to on/off/control constraints
    multiple constraint to one target and able to use by its individual weight
    change offset attribute to source to avoid cyclic dependency for parallel evaluation

How to use:
    import matrixConstraints
    #reload(matrixConstraints)
    matrixConstraints.ui()

"""

import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
from shiboken2 import wrapInstance
from maya import OpenMayaUI as OpenMayaUI
from PySide2 import QtGui, QtCore, QtWidgets

ptr = OpenMayaUI.MQtUtil.mainWindow()
widget = wrapInstance(long(ptr), QtWidgets.QWidget)


class ConstraintUI(QtWidgets.QDialog):
    def __init__(self, parent=widget):
        super(ConstraintUI, self).__init__(parent=parent)

        self.setWindowTitle('matrix Constraint_v_01')
        self.setGeometry(100, 100, 280, 100)
        self.setLayout(QtWidgets.QVBoxLayout())

        main_grp_box = QtWidgets.QGroupBox('constraints')
        self.parent = QtWidgets.QRadioButton('parent')
        self.parent.setChecked(True)
        self.point = QtWidgets.QRadioButton('point')
        self.orient = QtWidgets.QRadioButton('orient')
        self.scale = QtWidgets.QRadioButton('scale')

        constraint_layout = QtWidgets.QHBoxLayout()
        constraint_layout.addWidget(self.parent)
        constraint_layout.addWidget(self.point)
        constraint_layout.addWidget(self.orient)
        constraint_layout.addWidget(self.scale)

        apply_btn = QtWidgets.QPushButton('apply')
        apply_btn.clicked.connect(self.apply_constraint)

        main_grp_box.setLayout(constraint_layout)
        self.offset_cb = QtWidgets.QCheckBox('maintain Offset')
        self.offset_cb.setChecked(True)

        self.layout().addWidget(main_grp_box)
        self.layout().addWidget(self.offset_cb)
        self.layout().addWidget(apply_btn)

    def apply_constraint(self):
        sel = cmds.ls(sl=1)
        if not sel and sel > 1:
            error = QtWidgets.QMessageBox(self)
            error.setWindowTitle('Error !!')
            error.setText('Please select two objects !!')
            error.exec_()
            return

        maintain_offset = self.offset_cb.isChecked()
        if self.parent.isChecked():
            x = Matrix(sel[0], sel[1])
            x.add_constraint('parent', mo=maintain_offset)

        elif self.point.isChecked():
            x = Matrix(sel[0], sel[1])
            x.add_constraint('point', mo=maintain_offset)

        elif self.orient.isChecked():
            x = Matrix(sel[0], sel[1])
            x.add_constraint('orient', mo=maintain_offset)
        else:
            x = Matrix(sel[0], sel[1])
            x.add_constraint('scale', mo=maintain_offset)


class Matrix(object):
    def __init__(self, source, target):
        self.source = source
        self.target = target

    def get_dag_path(self, node):
        sel = OpenMaya.MSelectionList()
        sel.add(node)
        d = OpenMaya.MDagPath()
        sel.getDagPath(0, d)
        return d

    def offset_matrix(self):
        parentWorldMatrix = self.get_dag_path(self.source).inclusiveMatrix()
        childWorldMatrix = self.get_dag_path(self.target).inclusiveMatrix()
        offset = childWorldMatrix * parentWorldMatrix.inverse()
        if cmds.attributeQuery('offset', n=self.target, ex=1):
            cmds.setAttr('{}.offset'.format(self.target), [offset(i, j) for i in range(4) for j in range(4)],
                         type='matrix')
        else:
            cmds.addAttr(self.target, ln='offset', attributeType='matrix')
            cmds.setAttr('{}.offset'.format(self.target), [offset(i, j) for i in range(4) for j in range(4)], type='matrix')

    def add_constraint(self, constraint_type=None, mo=False):

        constraints = {'parent': ['translate', 'rotate'], 'orient': ['rotate'], 'point': ['translate'], 'scale': ['scale']}

        decompose = cmds.createNode('decomposeMatrix')
        if mo:
            mult_matrix = cmds.createNode('multMatrix')
            self.offset_matrix()
            cmds.connectAttr('{}.offset'.format(self.target), '{}.matrixIn[0]'.format(mult_matrix))
            cmds.connectAttr('{}.worldMatrix'.format(self.source), '{}.matrixIn[1]'.format(mult_matrix))
            cmds.connectAttr('{}.matrixSum'.format(mult_matrix), '{}.inputMatrix'.format(decompose))
        else:
            cmds.connectAttr('{}.worldMatrix'.format(self.source), '{}.inputMatrix'.format(decompose))

        for each in constraints.get(constraint_type, constraints['parent']):
            cmds.connectAttr('{}.output{}'.format(decompose, each.capitalize()), '{}.{}'.format(self.target, each))


def ui():
    app = ConstraintUI()
    app.show()
