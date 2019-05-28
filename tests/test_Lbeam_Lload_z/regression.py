#!/usr/bin/env python
#
# pyBeam, a Beam Solver
#
# Copyright (C) 2018 Ruben Sanchez, Rocco Bombardieri, Rauno Cavallaro
# 
# Developers: Ruben Sanchez (SciComp, TU Kaiserslautern)
#             Rocco Bombardieri, Rauno Cavallaro (Carlos III University Madrid)
#
# This file is part of pyBeam.
#
# pyBeam is free software: you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# pyBeam is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero
# General Public License along with pyBeam.
# If not, see <http://www.gnu.org/licenses/>.
#

import numpy as np
import sys, os
from pyBeamIO import pyBeamConfig as pyConfig
from pyBeamIO import pyBeamInput as pyInput
import pyBeam

# Load running directory
rundir = os.path.dirname(os.path.realpath(__file__))
confFile = rundir + '/config_NL.cfg'

# Parsing Conf file
config = pyConfig.pyBeamConfig(confFile)  # Beam configuration file

# Specifically added for the test
config['B_PROPERTY'] = rundir + '/' + config['B_PROPERTY'][:]
config['B_MESH'] = rundir + '/' + config['B_MESH'][:]

# Parsing mesh file
nDim = pyInput.readDimension(config['B_MESH'])
node_py, nPoint = pyInput.readMesh(config['B_MESH'],nDim)
elem_py, nElem = pyInput.readConnectivity( config['B_MESH'])
Constr, nConstr = pyInput.readConstr(config['B_MESH'])
# Parsing Property file
Prop, nProp = pyInput.readProp(config['B_PROPERTY'])

# Initializing objects
beam = pyBeam.CBeamSolver()
inputs = pyBeam.CInput(nPoint, nElem)

# Sending to CInput object 
pyConfig.parseInput(config, inputs, Constr, nConstr)
# Assigning input values to the input object in C++
inputs.SetParameters()
# Initialize the input in the beam solver
beam.InitializeInput(inputs)

# Assigning values to the CNode objects in C++
node = []  
for i in range(nPoint):
   node.append( pyBeam.CNode(node_py[i].GetID()) )
   for j in range(nDim):
      node[i].SetCoordinate(j , float(node_py[i].GetCoord()[j][0]) )
      node[i].SetCoordinate0(j , float(node_py[i].GetCoord0()[j][0]) )
   beam.InitializeNode(node[i], i)
    
# Assigning property values to the property objects in C++
beam_prop = []
for i in range(nProp):
    beam_prop.append(pyBeam.CProperty(i))
    beam_prop[i].SetSectionProperties( Prop[i].GetA(),  Prop[i].GetIyy(),  Prop[i].GetIzz(),  Prop[i].GetJt())
  
# Assigning element values to the property objects in C++ 
element =[]
for i in range(nElem): 
   element.append(pyBeam.CElement(i))
   #element[i].Initializer(CNode* Node1, CNode* Node2, CProperty* Property, CInput* Input, addouble AuxVector_x, addouble AuxVector_y, addouble AuxVector_z)
   #NB node starts from index 0 and the same happen in beam_prop. But in element_py (connectivity) indexes start from 1 as it is the physical connectivity read from input file
   element[i].Initializer(node[elem_py[i].GetNodes()[0,0] -1], node[elem_py[i].GetNodes()[1,0] -1], beam_prop[elem_py[i].GetProperty() -1], inputs, elem_py[i].GetAuxVector()[0,0], elem_py[i].GetAuxVector()[1,0], elem_py[i].GetAuxVector()[2,0]  )
   beam.InitializeElement(element[i], i)
  
beam.InitializeStructure()

iNode = 20
beam.SetLoads(iNode,2,50000)
beam.Solve(0)

coordinate_X = []
coordinate_Y = []
coordinate_Z = []

coordinate_X0 = []
coordinate_Y0 = []
coordinate_Z0 = []

for jNode in range(0,nPoint):
    
  coordinate_X.append(beam.ExtractCoordinate(jNode, 0))
  coordinate_Y.append(beam.ExtractCoordinate(jNode, 1))
  coordinate_Z.append(beam.ExtractCoordinate(jNode, 2))  
  
  coordinate_X0.append(beam.ExtractCoordinate0(jNode, 0))
  coordinate_Y0.append(beam.ExtractCoordinate0(jNode, 1))
  coordinate_Z0.append(beam.ExtractCoordinate0(jNode, 2))
  
print("Node {} Coord_tip indef= {} {} {}".format(iNode, coordinate_X0[iNode], coordinate_Y0[iNode], coordinate_Z0[iNode]))  
print("Coord_tip= {} {} {}".format(coordinate_X[iNode], coordinate_Y[iNode], coordinate_Z[iNode]))  
print("Displ_tip= {} {} {}".format(coordinate_X[iNode] - coordinate_X0[iNode], coordinate_Y[iNode] - coordinate_Y0[iNode], coordinate_Z[iNode] - coordinate_Z0[iNode]))  
   
test_val = np.sqrt((coordinate_X[20]-19.05326647582835)**2+
                   (coordinate_Y[20]-12.150042136520977)**2+
                   (coordinate_Z[20]-16.32312936016357)**2)

print("Tolerance: ",test_val)
  
# Tolerance is set to 1E-8
if (test_val < 1e-8):
  exit(0)
else:
  exit(1)
