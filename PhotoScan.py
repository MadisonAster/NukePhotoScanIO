import nuke, math, os, shutil
import xml.etree.ElementTree as ET
from zipfile import ZipFile

def deselectAll():
    for a in nuke.selectedNodes():
        a['selected'].setValue(False)
def selectList(List):
    for a in List:
        a['selected'].setValue(True)
def createCameraFromMatrix(matrixstr):
    #Takes: matrixstr as str of ' ' separated floats
    #Performs: generates camera node with matrix values:
    #Returns: node reference
    matrix = matrixstr.split(' ')[0:16]
    node = nuke.createNode('Camera')
    node['useMatrix'].setValue(True)
    node['matrix'].setValue(matrix)
    #node['far'].setValue(150.0)
    deselectAll()
    return node
def transformFromMatrix(node, frame = nuke.frame(), SetScale = False):
    #Takes: node as nuke node reference
    #Performs: populates translate, rotate, and scale knobs on node from it's matrix values
    #          sets useMatrix to false to allow for gui transformations
    #Returns: translate, rotate, and scale values
    nuke.frame(frame)
    worldMatrix = node.knob('world_matrix')
    worldMatrixAt = node.knob('world_matrix').getValueAt(frame)

    matrix = nuke.math.Matrix4()

    worldMatrix = node.knob('world_matrix')
    matrix = nuke.math.Matrix4()
    for y in range(worldMatrix.height()):
        for x in range(worldMatrix.width()):
            matrix[x+(y*worldMatrix.width())] = worldMatrixAt[y+worldMatrix.width()*x]
  
    transM = nuke.math.Matrix4(matrix)
    transM.translationOnly()
    rotM = nuke.math.Matrix4(matrix)
    rotM.rotationOnly()
    scaleM = nuke.math.Matrix4(matrix)
    scaleM.scaleOnly()
  
    if SetScale == True:
        scale = (scaleM.xAxis().x, float(scaleM.yAxis().y)*-1, float(scaleM.zAxis().z)*-1)
    else:
        scale = (scaleM.xAxis().x, scaleM.yAxis().y, scaleM.zAxis().z)
    rot = rotM.rotationsZXY()
    rotate = (math.degrees(rot[0]), math.degrees(rot[1]), math.degrees(rot[2]))
    translate = (transM[12], transM[13], transM[14])
          
    node['translate'].setValue(translate)
    node['rotate'].setValue(rotate)
    node['scaling'].setValue(scale)
    node['useMatrix'].setValue(False)
    return translate, rotate, scale
def createReadNode(cameraid, framecameras):
    #Takes: cameraid as numeric str
    #Performs: lookup in frame.xml, creates readnode
    #Returns: read node as node reference
    ReadNode = nuke.createNode('Read')
    for framecamera in framecameras:
        #print camera.attrib
        if int(framecamera.attrib['camera_id']) == int(cameraid):
            break
    camerapath = framecamera.find('photo').attrib['path']
    ReadNode['file'].setValue(camerapath)
    deselectAll()
    return ReadNode
        
def createProject3D(CameraNode, ReadNode, LastMergeNode):
    ProjectNode = nuke.createNode('Project3D')
    ProjectNode.setInput(0, ReadNode)
    ProjectNode.setInput(1, CameraNode)
    deselectAll()
    MergeNode = nuke.createNode('MergeMat')
    MergeNode.setInput(0, LastMergeNode)
    MergeNode.setInput(1, ProjectNode)
    deselectAll()
    return ProjectNode, MergeNode
        
def getMatrixfromTransform(node, frame = nuke.frame()):
    #Takes: node as nuke node reference
    #Performs: 
    #Returns: current transform matrix values
    return node.knob('world_matrix').getValueAt(frame)
    
def readProjectFiles(psxFilePath):
    filesFilePath = psxFilePath.rsplit('.',1)[0]+'.files'
    os.chdir(filesFilePath)
    
    chunkZipPath = filesFilePath+'/0/chunk.zip'
    frameZipPath = filesFilePath+'/0/0/frame.zip'
    thumbnailsZipPath = filesFilePath+'/0/0/thumbnails/thumbnails.zip'
    pointcloudZipPath = filesFilePath+'/0/0/point_cloud.1/point_cloud.zip'
    
    
    chunkZip = ZipFile(chunkZipPath)
    chunkZip.extractall()
    shutil.move('doc.xml', 'chunk.xml')
    
    frameZip = ZipFile(frameZipPath)
    frameZip.extractall()
    shutil.move('doc.xml', 'frame.xml')
    
    
    chunktree = ET.parse('chunk.xml')
    chunkroot = chunktree.getroot()
    chunkcameras = chunkroot.find('cameras')
    frametree = ET.parse('frame.xml')
    frameroot = frametree.getroot()
    framecameras = frameroot.find('cameras')
    
    return chunkroot, frameroot
    
def clearScene():
    trashclasses = ['Read', 'Camera', 'MergeMat', 'Project3D', 'Scene']
    for node in nuke.thisGroup().nodes():
        if node.Class() in trashclasses:
            nuke.delete(node)