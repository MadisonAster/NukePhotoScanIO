import struct, random
from collections import OrderedDict

from pprint import pprint

def ImportPointCloud(filePath):
    #Takes: filePath as valid path str to .ply file
    #Performs: reads from file and creates BakedPointCloud node
    #Returns: pointer to BakedPointCloud node
    file = open(filePath, 'r+b')
    HeaderData = ReadHeaderData(file)
    Vertexes = ReadVertexes(file, HeaderData)
    Faces = ReadFaces(file, HeaderData, Vertexes)
    file.close()
    #pprint(Vertexes)
    #return
    return CreatPointCloud(Vertexes)
def ReadHeaderData(file):
    #Takes: file as open binary file handle with cursor positioned at the beginning of the file
    #Performs: reads HeaderData from file
    #Returns: HeaderData as OrderedDict
    
    HeaderData = OrderedDict()
    bindata = ""
    while bindata[-10:] != 'end_header':
        bindata += file.read(1)
    file.read(1) #skip spacer character
    
    bindata = bindata.split('\n')
    
    HeaderData['format'] = bindata[1].split(' ',1)[-1]
    HeaderData['vertex'] = int(bindata[2].split(' ',2)[-1])
    counter = 3
    
    HeaderData['VertexProperties'] = OrderedDict()
    while True:
        if 'property' in bindata[counter]:
            propdata = bindata[counter].split(' ')
            HeaderData['VertexProperties'][propdata[2]] = propdata[1]
            counter += 1
        else:
            break
    if 'face' in bindata[counter]:
        HeaderData['face'] = int(bindata[counter].split(' ',2)[-1])
    else:
        HeaderData['face'] = 0
    for key in HeaderData.keys():
        print key, HeaderData[key]
    return HeaderData
def ReadVertexes(file, HeaderData):
    #Takes: file as open binary file handle with cursor positioned at the first vertex, HeaderData as OrderedDict
    #Performs: reads Vertex data from file
    #Returns: Vertexes as list of OrderedDicts representing each vertex, keys [x,y,z,u,v,w,red,green,blue] with values formatted as strings
    datasizes = { #number of bytes in each data type
    'char' : 1,
    'uchar' : 1,
    'short' : 2,
    'ushort' : 2,
    'int' : 4,
    'uint' : 4,
    'float' : 4,
    'double' : 8,
    }
    datatypes = { #struct library abbreviations
    'char' : 'c',
    'uchar' : 'B',
    'short' : 'h',
    'ushort' : 'H',
    'int' : 'i',
    'uint' : 'I',
    'float' : 'f',
    'double' : 'd',
    }
    Vertexes = []        
    for vertex in range(HeaderData['vertex']):
        vertex = OrderedDict([('x',''),('y',''),('z',''),('u','0'),('v','0'),('w','0'),('red',str(random.uniform(0, 1))),('green',str(random.uniform(0, 1))),('blue',str(random.uniform(0, 1)))])
        for key in HeaderData['VertexProperties'].keys():
            datatype = HeaderData['VertexProperties'][key]
            if key == 'size':
                key = 'z'
            data = struct.unpack('<'+datatypes[datatype],file.read(datasizes[datatype]))
            
            if datatype == 'uchar':
                vertex[key] = str(data[0]/255.0)
            if datatype == 'float':
                vertex[key] = str(data[0])
        Vertexes.append(vertex)
    return Vertexes
def ReadFaces(file, HeaderData, Vertexes):
    #Takes: file as open binary file handle with cursor positioned at the first face, HeaderData as OrderedDict, Vertexes as list of OrderedDicts
    #Performs: reads Face data from file
    #Returns: None
    return None
def CreatPointCloud(points):
    #Takes: points as list of OrderedDicts, each vertex should have 9 keys [x,y,z,u,v,w,r,g,b] values should be formatted as strings
    #Performs: creates BakedPointCloud node in nuke, populates it with data
    #Returns: BakedPointCloud node
    import nuke
    pcPoints = pcVelocities = pcColors = str(len(points))+' '
    for point in points:
        pcPoints += ' '.join(point.values()[0:3])+' '
        pcVelocities += ' '.join(point.values()[3:6])+' '
        pcColors += ' '.join(point.values()[6:9])+' '
    pcNode = nuke.createNode("BakedPointCloud")
    pcNode['serializePoints'].fromScript(pcPoints)
    pcNode['serializeNormals'].fromScript(pcVelocities)
    pcNode['serializeColors'].fromScript(pcColors)
    pcNode['pointSize'].setValue(0.25)
    
    axisNode = nuke.createNode('Axis')
    axisNode.setName('BakedPointCloudAxis'+pcNode.name().rsplit('Cloud',1)[-1])
    pcNode['translate'].setExpression('parent.BakedPointCloudAxis1.translate')
    pcNode['rotate'].setExpression('parent.BakedPointCloudAxis1.rotate')
    pcNode['scaling'].setExpression('parent.BakedPointCloudAxis1.scaling')
    pcNode['uniform_scale'].setExpression('parent.BakedPointCloudAxis1.uniform_scale')
    pcNode['skew'].setExpression('parent.BakedPointCloudAxis1.skew')
    pcNode['pivot'].setExpression('parent.BakedPointCloudAxis1.pivot')
    pcNode['useMatrix'].setExpression('parent.BakedPointCloudAxis1.useMatrix')
    
    return pcNode
if __name__ == '__main__':
    ImportPointCloud('T:/AppVariables/Nuke/development/PalmyraTest/mesh.ply')