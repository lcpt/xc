# -*- coding: utf-8 -*-
from __future__ import print_function
# home made test
'''vector2d_uniform_load_global function verification.'''

import xc_base
import geom
import xc
from solution import predefined_solutions
from model import predefined_spaces
from materials import typical_materials
import math

__author__= "Luis C. Pérez Tato (LCPT) and Ana Ortega (AOO)"
__copyright__= "Copyright 2015, LCPT and AOO"
__license__= "GPL"
__version__= "3.0"
__email__= "l.pereztato@gmail.com"

# Geometry
width= .05
depth= .1
nDivIJ= 5
nDivJK= 10
y0= 0
z0= 0
L= 2.0 # Bar length (m)
Iy= width*depth**3/12 # Cross section moment of inertia (m4)
Iz= depth*width**3/12 # Cross section moment of inertia (m4)
E= 210e9 # Young modulus of the steel.
nu= 0.3 # Poisson's ratio
G= E/(2*(1+nu)) # Shear modulus
J= .2e-1 # Cross section torsion constant (m4)

# Load
f= 1.5e3 # Longitudinal uniform load.
p= 1000 # Transverse uniform load.

feProblem= xc.FEProblem()
preprocessor=  feProblem.getPreprocessor
nodes= preprocessor.getNodeHandler

# Problem type
modelSpace= predefined_spaces.StructuralMechanics2D(nodes)

nodes.defaultTag= 1 # First node number.
nod= nodes.newNodeXY(0,0.0)
nod= nodes.newNodeXY(L*math.sqrt(2)/2,L*math.sqrt(2)/2)

# Geometric transformation(s)
lin= modelSpace.newLinearCrdTransf("lin")

# Materials definition
fy= 275e6 # Yield stress of the steel.
steel= typical_materials.defSteel01(preprocessor, "steel",E,fy,0.001)
respT= typical_materials.defElasticMaterial(preprocessor, "respT",G*J) # Torsion response.
respVy= typical_materials.defElasticMaterial(preprocessor, "respVy",1e9) # Shear response in y direction.
respVz= typical_materials.defElasticMaterial(preprocessor, "respVz",1e9) # Shear response in z direction.
# Sections
import os
pth= os.path.dirname(__file__)
# print("pth= ", pth)
if(not pth):
  pth= "."
exec(open(pth+"/../aux/testQuadRegion.py").read())

materialHandler= preprocessor.getMaterialHandler
quadFibers= materialHandler.newMaterial("fiber_section_3d","quadFibers")
fiberSectionRepr= quadFibers.getFiberSectionRepr()
fiberSectionRepr.setGeomNamed("testQuadRegion")
quadFibers.setupFibers()
A= quadFibers.getFibers().getArea(1.0)

agg= materialHandler.newMaterial("section_aggregator","agg")
agg.setSection("quadFibers")
agg.setAdditions(["T","Vy","Vz"],["respT","respVy","respVz"])
# Torsion and shear responses.



# Elements definition
elements= preprocessor.getElementHandler
elements.defaultTransformation= lin.name # Coordinate transformation for the new elements
elements.defaultMaterial= agg.name
elements.numSections= 3 # Number of sections along the element.
elements.defaultTag= 1
el= elements.newElement("ForceBeamColumn2d",xc.ID([1,2]))



# Constraints
constraints= preprocessor.getBoundaryCondHandler
modelSpace.fixNode000(1)

# Load definition.
lp0= modelSpace.newLoadPattern(name= '0')
modelSpace.setCurrentLoadPattern("0")
crdTransf= el.getCoordTransf
vIElem= crdTransf.getIVector
vJElem= crdTransf.getJVector
vCarga= f*vIElem-p*vJElem
el.vector2dUniformLoadGlobal(vCarga)


loadHandler= preprocessor.getLoadHandler
loadHandler.addToDomain("0") # Append load pattern to domain.

# Solution procedure
analysis= predefined_solutions.plain_newton_raphson(feProblem)
result= analysis.analyze(1)

nodes.calculateNodalReactions(True,1e-7) 
nod2= nodes.getNode(2)
vDisp= xc.Vector([nod2.getDisp[0],nod2.getDisp[1]])
nod1= nodes.getNode(1)
vReac1= xc.Vector([nod1.getReaction[0],nod1.getReaction[1]])
nod2= nodes.getNode(2)
vReac2= xc.Vector([nod2.getReaction[0],nod2.getReaction[1]])

elements= preprocessor.getElementHandler

elem1= elements.getElement(1)
elem1.getResistingForce()
scc= elem1.getSections()[0]
N0= scc.getStressResultantComponent("N")

F= (f*L)
delta0= vDisp.dot(vIElem)
delta0teor= (f*L**2/(2*E*A))
ratio0= (abs((delta0-delta0teor)/delta0teor))
Q= p*L
delta1= vDisp.dot(vJElem)
delta1Teor= (-Q*L**3/8/E/Iz)
ratio1= ((delta1-delta1Teor)/delta1Teor)
ratio2= (abs((N0-F)/F))
RN= vReac1.dot(vIElem)
ratio3= (abs((RN+F)/F))
RN2= vReac2.dot(vIElem)

''' 
print("analOk: ",analOk)
print("delta0: ",delta0)
print("delta0Teor: ",delta0teor)
print("ratio0= ",ratio0)
print("delta1= ",delta1)
print("delta1Teor= ",delta1Teor)
print("ratio1= ",ratio1)
print("N0= ",N0)
print("ratio2= ",ratio2)
print("vReac1= ",vReac1)
print("RN= ",RN)
print("ratio3= ",ratio3)
print("vReac2= ",vReac2)
print("RN2= ",RN2)
   '''
import os
from misc_utils import log_messages as lmsg
fname= os.path.basename(__file__)
if (abs(ratio0)<1e-6) & (abs(ratio1)<0.05) & (abs(ratio2)<1e-10) & (abs(ratio3)<1e-10):
  print('test '+fname+': ok.')
else:
  lmsg.error(fname+' ERROR.')
