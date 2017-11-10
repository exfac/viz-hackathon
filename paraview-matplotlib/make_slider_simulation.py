"""
Author : Julien Lhermitte
To be eventually merged into ScatterSim:
    http://www.github.com/CFN-SoftBio/ScatterSim

==========================================
Using VTK and matplotlib in a QT interface
==========================================
This example creates two images:
    top image : the small angle x-ray scattering
    bottom image : A 3D view of the sample (a cylinder)

The GUI window contains a slider which allows the rotation of the sample.
Moving the slider rotates the sample and also updates the scattering.
"""


from __future__ import print_function

import sys

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)


from PyQt5 import QtWidgets, QtCore

import vtk

from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

UnitTrans = np.array([[1, 0, 0, 0],
                      [0, 1, 0, 0],
                      [0, 0, 1, 0],
                      [0, 0, 0, 1],
                      ], dtype=float)


def make_vtk_cylinder(radius, height):

    # Create source
    source = vtk.vtkCylinderSource()
    source.SetCenter(0, 0, 0)
    source.SetRadius(radius)
    source.SetHeight(height)

    # Create a mapper
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(source.GetOutputPort())

    # Create an actor
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    return actor


class AppForm(QtWidgets.QMainWindow):
    def __init__(self, radius, height, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.cyl_obj = Cylinder(radius=radius, height=radius)
        self.radius = radius
        self.height = height

        self.create_main_frame()

    def create_main_frame(self):
        self.main_frame = QtWidgets.QWidget()

        self.fig = Figure((5.0, 4.0), dpi=100)
        ax = self.fig.gca()
        self.im = ax.imshow(self.cyl_obj.scat, vmin=0, vmax=.01)
        self.fig.colorbar(self.im, ax=ax)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)
        self.canvas.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.canvas.setFocus()

        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.canvas)  # the matplotlib canvas
        vbox.addWidget(self.mpl_toolbar)

        # make the vtk widget
        self.frame = QtWidgets.QFrame()
        self.vl = QtWidgets.QVBoxLayout()
        self.vtkWidget = QVTKRenderWindowInteractor(self.frame)
        vbox.addWidget(self.vtkWidget)

        self.ren = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()

        self.cyl = make_vtk_cylinder(self.radius, self.height)
        self.ren.AddActor(self.cyl)
        # self.pln = make_vtk_plane()
        # self.ren.AddActor(self.pln)

        # trick to get camera to start in a different position
        # first change position then Reset to get object in view
        self.ren.GetActiveCamera().SetPosition(0, 1, 0)
        self.ren.ResetCamera()

        self.slider_z = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_z.setMinimum(0)
        self.slider_z.setMaximum(360)
        vbox.addWidget(self.slider_z)

        def rotate_cylinder_z(theta):
            # create transform and then set it for cylinder
            # TODO : check if we can just update existing transform
            tran = vtk.vtkTransform()
            tran.SetMatrix(rotmat3D(theta, axis=3).ravel())
            self.cyl.SetUserTransform(tran)
            self.im.set_array(self.cyl_obj.compute_scattering(theta))
            self.vtkWidget.update()
            self.canvas.draw_idle()

        self.slider_z.valueChanged.connect(rotate_cylinder_z)

        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)

        self.show()
        self.iren.Initialize()


class Cylinder:
    def __init__(self, radius, height):
        self.radius = radius
        self.height = height
        self.setup_grid()
        # z rotationo in degrees
        self.z_rotation = 0

    def setup_grid(self):
        ''' quick setup of an x-y projection grid.'''
        # TODO : To generalize. extremely quickly written just for a
        # demonstration
        # some sensible limits (assume radius smallest)
        qx = np.linspace(-2*np.pi/self.radius*3, 2*np.pi/self.radius*3, 1000)
        QX, QY = np.meshgrid(qx, qx)
        QZ = QX*0
        self.qvec = np.array([QX, QY, QZ, np.ones_like(QZ)])
        self.scat = self.cyl_scattering(self.qvec[:3])

    def cyl_form_factor(self, qvec):
        """
            Calculation of a cylinder form factor
            Simplified.
        """
        import numpy as np
        # cylndrical and spherical Bessel functions
        from scipy.special import j1

        qx, qy, qz = qvec

        R = self.radius
        H = self.height

        qr = np.hypot(qx, qy)

        F = 2 * np.sinc(qz * H / 2. / np.pi) * j1(qr * R) / qr / R + 1j * 0

        return F

    def cyl_scattering(self, qvec):
        return np.abs(self.cyl_form_factor(qvec))**2

    def compute_scattering(self, angle):
        qvec = self.qvec
        # TODO : fix the offset between rotation of object and scattering
        rotation_matrix = rotmat3D(angle, axis=2)
        qvec = np.tensordot(rotation_matrix, qvec, axes=(1, 0))
        return self.cyl_scattering(qvec[:3])


def rotmat3D(phi, axis=3):
    '''3D rotation matrix about z axis.

        phi : in degrees

        Counter-clockwise rotation is positive.
        axis: choose either:
            1 - x axis
            2 - y axis
            3 - z axis
    '''
    phi = np.radians(phi)
    if axis == 3:
        return np.array([
            [np.cos(phi), np.sin(phi), 0, 0],
            [-np.sin(phi), np.cos(phi), 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
    elif axis == 2:
        return np.array([
            [np.cos(phi), 0, np.sin(phi), 0],
            [0, 1, 0, 0],
            [-np.sin(phi), 0, np.cos(phi), 0],
            [0, 0, 0, 1]
        ])
    elif axis == 1:
        return np.array([
            [1, 0, 0, 0],
            [0, np.cos(phi), np.sin(phi), 0],
            [0, -np.sin(phi), np.cos(phi), 0],
            [0, 0, 0, 1]
        ])
    else:
        print("Error, not a good axis specified. Specified: {}".format(axis))


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    form = AppForm(radius=2, height=10)
    sys.exit(app.exec_())
