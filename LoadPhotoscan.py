import nuke, math, os, shutil
import xml.etree.ElementTree as ET
from zipfile import ZipFile

def ImportPhotoscanProject():
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
        deselectAll()
        return node
    def transformFromMatrix(node, frame = nuke.frame()):
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
  
        scale = (scaleM.xAxis().x, float(scaleM.yAxis().y)*-1, float(scaleM.zAxis().z)*-1)
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
    
    deselectAll()
    psxFilePath = nuke.getFilename('Chose a psx project to import', '*.psx')
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
    
    
    SceneNode = nuke.createNode('Scene')
    SceneNode.setName(psxFilePath.rsplit('/',1)[1].rsplit('.',1)[0])
    LightNode = nuke.createNode('Light')
    LightNode['translate'].setValue([0, 500, 0])
    SceneNode.setInput(0, LightNode)
    deselectAll()
    
    GroupNode = nuke.createNode('Group')
    GroupNode.begin()
    
    GroupNode.addKnob(nuke.Boolean_Knob('isolated'))
    GroupNode['isolated'].setVisible(False)
    GroupNode.addKnob(nuke.Enumeration_Knob('cameras', 'cameras', []))
    GroupNode.addKnob(nuke.PyScript_Knob('', 'IsolateCamera', "targetnode = nuke.toNode('MergeMat'+nuke.thisGroup()['cameras'].value().strip('Camera'))\nresetFlag = True\nfor node in nuke.thisGroup().nodes():\n    if 'MergeMat' in node.name():\n        if targetnode['disable'].value() == False and nuke.thisGroup()['isolated'].value() == True:\n            node['disable'].setValue(False)\n            resetFlag = False\n        else:\n            node['disable'].setValue(True)\nnuke.thisGroup()['isolated'].setValue(resetFlag)\ntargetnode['disable'].setValue(False)"))
    GroupNode.addKnob(nuke.PyScript_Knob('', 'OpenCamera', "nodename = nuke.thisGroup()['cameras'].value()\nnuke.show(nuke.thisGroup().node(nodename))"))
    CameraNames = []
    
    AxisNode = nuke.createNode('Axis')
    AxisNode.setName('GlobalTransform')
    AxisNode['translate'].setValue([11.76185989, 322.43740845, -2035.89147949])
    AxisNode['rotate'].setValue([-16.14972562, 1.23336947, -180.27386188])
    AxisNode['uniform_scale'].setValue(10)
    deselectAll()
    LastMergeNode = nuke.createNode('Constant')
    LastMergeNode['color'].setValue([0.862179,0.460351,0,1])
    deselectAll()
    LastMergeNode.setXYpos(-400,321)
    
    AutoAlignList = []
    for chunkcamera in chunkcameras.findall('camera'):
        cameramatrix = chunkcamera.findtext('transform')
        if cameramatrix == None:
            cameramatrix = '1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1'
        CameraNode = createCameraFromMatrix(cameramatrix)
        CameraNames.append(CameraNode.name())
        transformFromMatrix(CameraNode)
        
        ReadNode = createReadNode(chunkcamera.attrib['id'], framecameras)
        ProjectNode, MergeNode = createProject3D(CameraNode, ReadNode, LastMergeNode)
        LastMergeNode = MergeNode
        
        
        #SceneNode.setInput(SceneNode.inputs(), CameraNode)
        CameraNode.setInput(0, AxisNode)
        
        AutoAlignList.append(CameraNode)
        AutoAlignList.append(ReadNode)
        AutoAlignList.append(ProjectNode)
        AutoAlignList.append(MergeNode)
        
    TextureOutput = nuke.createNode('NoOp')
    TextureOutput.setName('TextureOutput')
    TextureOutput.setInput(0, LastMergeNode)
    OutputNode = nuke.createNode('Output')
    OutputNode.setInput(0, TextureOutput)
    deselectAll()
    
    AxisNode.setXYpos(-400,100)
    TextureOutput.setXYpos(-1000,230)
        
    #selectList(AutoAlignList)
    for a in AutoAlignList:
        a.autoplace()
        
    GroupNode['cameras'].setValues(CameraNames)
    GroupNode.end()
    
    #SceneNode.setXYpos(-750,750)
    #LightNode.setXYpos(-750,500)
    #transformFromMatrix(mynode)
    


  