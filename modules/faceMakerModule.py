import cv2
import face_recognition


# imagePath create a list of name of the files from the path
def imagePath(path, images, classNames):
    for cl in path:
        curImg = cv2.imread(f'{cl}')
        images.append(curImg)
        pName = cl.split('/')
        classNames.append(pName[-1].split('.')[0])
    print(classNames)


# findEncodings
def findEncodings(images, encodeList):
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
    return encodeList


# Create EDL
def createEDL(fName, listbox, classNames, fileName):
    filename = fName + '.edl'
    with open(filename, 'w') as edlFile:
        edlFile.write('')
    listbox.insert(1, 'Found {classNames} in {title}'.format(
        classNames=classNames, title=fileName))


# write EDL
def writeEDL(fName,
             index,
             TC_in,
             TC_out,
             typeOfShot,
             markColor,
             persons,
             durClip):
    filename = fName + '.edl'
    with open(filename, 'r+') as edlFile:
        edlFile.readlines()
        edlFile.writelines('\n{a} 1 V {TC_in} {TC_out} {TC_in} {TC_out}\n{typeOfShot} |C:ResolveColor{markColor} |M:{persons} |D:{durClip}'
                           .format(a=index,
                                   TC_in=TC_in,
                                   TC_out=TC_out,
                                   typeOfShot=typeOfShot,
                                   markColor=markColor,
                                   persons=persons,
                                   durClip=durClip))


# typeOfShot
def type_of_shot(shot, accuracy):
    if int(shot) in range(int(0), int(10*accuracy)):
        return 'none'
    if int(shot) in range(int(11*accuracy), int(90*accuracy)):
        return 'LS'
    if int(shot) in range(int(91*accuracy), int(150*accuracy)):
        return 'MLS'
    if int(shot) in range(int(151*accuracy), int(280*accuracy)):
        return 'MS'
    if int(shot) in range(int(281*accuracy), int(450*accuracy)):
        return 'MCU'
    if int(shot) in range(int(451*accuracy), int(1000*accuracy)):
        return 'CU'


# durationMarker elimitates from the list all the elements
# except the first time that find a face
def durationMarker(list):
    count = 1
    dur = []
    edl = []
    for i in range(len(list) - 1):
        if list[i][0] + 1 == list[1+i][0]:
            count += 1
        else:
            dur.append(count)
            edl.append(list[i - count + 1])
            edl[-1].append(count)
            count = 1
    dur.append(count)
    edl.append(list[i - count + 2])
    edl[-1].append(count)
    return edl
