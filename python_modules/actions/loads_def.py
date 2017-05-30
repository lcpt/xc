# -*- coding: utf-8 -*-


__author__= "Ana Ortega (AO_O)"
__copyright__= "Copyright 2017, AO_O"
__license__= "GPL"
__version__= "3.0"
__email__= "ana.Ortega@ciccp.es"

import xc_base
import geom
import xc
from actions.earth_pressure import soil_properties as sp

class BaseVectorLoad(object):
    '''Base class for loads introduced using a load as an xcVector 

    :ivar name:     name identifying the load
    :ivar loadVector: load xc.Vector
    '''
    def __init__(self,name, loadVector):
        self.name=name
        self.loadVector= loadVector

    def __mul__(self,factor):
        '''Apply the factor to the load and append it to the current load pattern'''
        self.loadVector=factor*self.loadVector
        self.appendLoadToCurrentLoadPattern()
            
    def __rmul__(self,factor):
        '''Apply the factor to the load and append it to the current load pattern'''
        self.loadVector=factor*self.loadVector
        self.appendLoadToCurrentLoadPattern()
     

        

class InertialLoad(BaseVectorLoad):
    '''Inertial load (density*acceleration) applied to the elements in the list
    of mesh-sets

    :ivar name:     name identifying the load
    :ivar lstMeshSets: list of mesh-sets (of type LinSetToMesh or SurfSetToMesh)
    :ivar vAccel:   acceleration vector xc.Vector([ax,ay,az])
    '''
    def __init__(self,name, lstMeshSets, vAccel):
        super(InertialLoad,self).__init__(name,vAccel)
        self.lstMeshSets=lstMeshSets

    def appendLoadToCurrentLoadPattern(self):
        for ms in self.lstMeshSets:
            if 'shell' in ms.elemType:
                loadVector=ms.matSect.getAreaDensity()*self.loadVector
                el_group=ms.surfSet.getElements
            elif 'beam' in ms.elemType:
                loadVector=ms.matSect.getLongitudinalDensity()*self.loadVector
                el_group=ms.linSet.getElements
            for e in el_group:
                e.vector3dUniformLoadGlobal(loadVector)

class NodalLoad(BaseVectorLoad):
    '''Point load applied on a list of nodes

    :ivar name:   name identifying the load
    :ivar lstNod: list of nodes on which the load is applied.
    :ivar loadVector: xc.Vector with the six components of the 
          load: xc.Vector([Fx,Fy,Fz,Mx,My,Mz]).
    '''
    def __init__(self,name, lstNod, loadVector):
        super(NodalLoad,self).__init__(name,loadVector)
        self.name=name
        self.lstNod= lstNod

    def appendLoadToCurrentLoadPattern(self):
        print 'aquí nodal load load=', self.loadVector.Norm()
        for n in self.lstNod:
            n.newLoad(self.loadVector)

           
class UniformLoadOnBeams(BaseVectorLoad):
    '''Uniform load applied on the beam elements generated from
    all the lines in the xcSet.

    :ivar name:       name identifying the load
    :ivar xcSet:      set that contains the lines
    :ivar loadVector: xc.Vector with the six components of the load: 
                      xc.Vector([Fx,Fy,Fz,Mx,My,Mz]).
    :ivar refSystem: reference system in which loadVector is defined:
                   'Local': element local coordinate system
                   'Global': global coordinate system (defaults to 'Global)
    '''
    def __init__(self,name, xcSet, loadVector,refSystem='Global'):
        super(UniformLoadOnBeams,self).__init__(name,loadVector)
        self.xcSet=xcSet
        self.refSystem= refSystem

    def appendLoadToCurrentLoadPattern(self):
        ''' Append load to the current load pattern.'''
        print 'aquí UniformLoadOnBeams load=',self.loadVector.Norm()
        for l in self.xcSet.getLines:
            for e in l.getElements():
                if self.refSystem=='Local':
                    e.vector3dUniformLoadLocal(self.loadVector)
                else:
                    e.vector3dUniformLoadGlobal(self.loadVector)
 

class UniformLoadOnLines(BaseVectorLoad):
    '''Uniform load applied to all the lines (not necessarily defined as lines
    for latter generation of beam elements, they can be lines belonging to 
    surfaces for example) found in the xcSet
    The uniform load is introduced as point loads in the nodes
    
    :ivar name:   name identifying the load
    :ivar xcSet:  set that contains the lines
    :ivar loadVector: xc.Vector with the six components of the load: 
                      xc.Vector([Fx,Fy,Fz,Mx,My,Mz]).
    '''                            
    def __init__(self,name,  xcSet, loadVector):
        super(UniformLoadOnLines,self).__init__(name,loadVector)
        self.xcSet=xcSet

    def appendLoadToCurrentLoadPattern(self):
        print 'aquí UniformLoadOnLines load=',self.loadVector.Norm()
        for l in self.xcSet.getLines:
            nod=[n for n in l.getNodes()]
            ndistOrig=[n.getCoo.Norm() for n in nod]
            sortNod=[nod for ndistOrig,nod in sorted(zip(ndistOrig,nod))]
            lnInfl=[(sortNod[i-1].getInitialPos3d).distPos3d(sortNod[i+1].getInitialPos3d)/2 for i in range(1,len(sortNod)-1)]
            lnInfl.insert(0,(sortNod[0].getInitialPos3d).distPos3d(sortNod[1].getInitialPos3d)/2.0)
            lnInfl.append((sortNod[len(sortNod)-2].getInitialPos3d).distPos3d(sortNod[len(sortNod)-1].getInitialPos3d)/2.0)
        for i in range(len(sortNod)):
            sortNod[i].newLoad(lnInfl[i]*self.loadVector)

class UniformLoadOnSurfaces(BaseVectorLoad):
    '''Uniform load applied on the shell elements generated from
    all the surfaces in the xcSet.

    :ivar name:       name identifying the load
    :ivar xcSet:      set that contains the surfaces
    :ivar loadVector: xc.Vector with the six components of the load: 
                      xc.Vector([Fx,Fy,Fz,Mx,My,Mz]).
    :ivar refSystem: reference system in which loadVector is defined:
                     'Local': element local coordinate system
                     'Global': global coordinate system (defaults to 'Global)
    '''
    def __init__(self,name, xcSet, loadVector,refSystem='Global'):
        super(UniformLoadOnSurfaces,self).__init__(name,loadVector)
        self.xcSet=xcSet
        self.refSystem=refSystem
        
    def appendLoadToCurrentLoadPattern(self):
        ''' Append load to the current load pattern.'''
        print 'aquí UniformLoadOnSurfaces load=',self.loadVector.Norm()
        for s in self.xcSet.getSurfaces:
            for e in s.getElements():
                if self.refSystem=='Local':
                    e.vector3dUniformLoadLocal(self.loadVector)
                else:
                    e.vector3dUniformLoadGlobal(self.loadVector)

class EarthPressLoad(BaseVectorLoad):
    '''Earth pressure applied on the shell elements generated from
    all the surfaces in the xcSet. 
    
    :ivar name:      name identifying the load
    :ivar xcSet:     set that contains the surfaces
    :ivar soilProp:  instance of the class SoilProp that defines the 
                     soil parameters required to calculate the earth pressure
                     (K:coefficient of pressure, zGround: global Z coordinate 
                     of ground level,gammaSoil: weight density of soil, 
                     zWater: global Z coordinate of groundwater level, 
                     gammaWater: weight density of water) 
    :ivar vDir:      unit xc vector defining pressures direction
    '''
    def __init__(self,name, xcSet,soilData, vDir):
        super(EarthPressLoad,self).__init__(name,vDir)
        self.xcSet=xcSet
        self.soilData=soilData

    def appendLoadToCurrentLoadPattern(self):
        ''' Append load to the current load pattern.'''
        for s in self.xcSet.getSurfaces:
            for e in s.getElements():
                presElem=self.soilData.getPressure(e.getCooCentroid(False)[2])
                if(presElem!=0.0):
                    e.vector3dUniformLoadGlobal(presElem*self.loadVector)
 

# TO DO: change the method in order to be able to append to current load pattern
class StrainGradientLoadOnSurfaces(object):
    '''Strain gradient applied on the shell elements generated from
    all the surfaces in the xcSet. 
    
    :ivar name:  name identifying the load
    :ivar xcSet: set that contains the surfaces
    :ivar nabla: strain gradient in the thickness of the elements:
                 nabla=espilon/thickness    
    '''
    def __init__(self,name, xcSet,nabla):
        self.name=name
        self.xcSet=xcSet
        self.nabla=nabla
    
    def appendLoadToLoadPattern(self,loadPattern):
        ''' Append load to the current load pattern.'''
        for s in self.xcSet.getSurfaces:
            for e in s.getElements():
                eLoad= loadPattern.newElementalLoad("shell_strain_load")
                eLoad.elementTags= xc.ID([e.tag])
                eLoad.setStrainComp(0,3,self.nabla)
                eLoad.setStrainComp(1,3,self.nabla)
                eLoad.setStrainComp(2,3,self.nabla)
                eLoad.setStrainComp(3,3,self.nabla)
