from modules.faceMakerModule import imagePath, findEncodings, type_of_shot, createEDL, durationMarker, writeEDL
from modules.frames_to_TC import frames_to_timecode
import DaVinciResolveScript as dvr_script
import datetime
import tkinter as tk
from tkinter import filedialog
import imageio
from PIL import Image, ImageTk
import cv2
import numpy as np
import face_recognition
from math import sqrt
import ffmpeg
from timecode import Timecode
import os

# connecting to DaVinci Resolve API, Media Storage, Project Manager
resolve = dvr_script.scriptapp("Resolve")
mediaStorage = resolve.GetMediaStorage()
projectManager = resolve.GetProjectManager()

# folder give the path where the EDL files are stored
folder = os.path.join(os.path.join(os.path.expanduser('~'), 'Downloads'))


# EDLfolder
def EDLfolder(listbox):
    global folder
    folder = filedialog.askdirectory(
        title=('Choose The EDL File Folder Destination')
    )
    listbox.delete(0)
    listbox.insert(1, 'Saving EDL in the: {folder}'.format(
        folder=folder.split('/')[-1]))


# tkinter root
root = tk.Tk()

root.title('MarkerFace')

# logo
root.geometry('800x800')
logo = Image.open('render.png')
logo = ImageTk.PhotoImage(logo)
logoLabel = tk.Label(root, image=logo)
logoLabel.place(x=0, y=0, relwidth=1, relheight=1)

# fisrt empty row tkinter
# label
root.rowconfigure(0, minsize=100)


# button edl folder
setFolder = tk.StringVar()
browseBtn2 = tk.Button(root, textvariable=setFolder,
                       command=lambda: EDLfolder(listbox),
                       font='Arial', bg='#ddd', fg='#aaa',
                       width=15, height=2)
setFolder.set('EDL Folder')
browseBtn2.grid(row=2, column=0, padx=50, pady=35, sticky='w')


# button browse
browseText = tk.StringVar()
browseBtn2 = tk.Button(root, textvariable=browseText,
                       command=lambda: openFile(),
                       font='Arial', bg='#ddd', fg='#aaa',
                       width=15, height=2)
browseText.set('Browse')
browseBtn2.grid(row=2, column=1, sticky='e')


# displaing on tkinter
listbox = tk.Listbox(root, width=78, height=20, border=0, bg='#ddd')
listbox.grid(row=4, column=1, rowspan=5, columnspan=1,
             sticky='e', padx=0, pady=33)
listbox.insert(1, 'Saving EDL In : {folder}'.format(
    folder=folder.split('\\')[-1]))

# create scrollbar
scrollbar = tk.Scrollbar(root)
scrollbar.grid(row=4, column=2, sticky='e', padx=5)

# set scroll to listbox
listbox.configure(yscrollcommand=scrollbar.set)
scrollbar.configure(command=listbox.yview())

# canvas = tk.Canvas(root, width=800, height=200)
# canvas.grid(columnspan=3, rowspan=3)

# open files function


def openFile():

    images = []
    classNames = []
    encodeList = []

    accuracy = 0.5

    # select the persons to looking for
    path = filedialog.askopenfilenames(
        title=('Which Person Are You Searching For?'),
        filetypes=([("Photos files", "*.png;*.jpg;*.jpeg")]))

    currentProject = projectManager.GetCurrentProject()
    mediaPool = currentProject.GetMediaPool()
    rootFolder = mediaPool.GetRootFolder()

    folderName = []

    for name in path:
        # insert the name of the persons in the listbox
        listbox.insert(1, 'Looking For: {name}'.format(
            name=name.split('/')[-1].split('.')[0]))
        folderName.append(name.split('/')[-1].split('.')[0] + ' ')

    strFolderName = ''
    strFolderName = strFolderName.join(folderName)

    # creting the date
    date = str(datetime.datetime.now().strftime(
        "- Date: %A %d-%m-%Y - Time: %H:%M:%S"))

    # creting subfolder where put face recognized clips
    mediaPool.AddSubFolder(rootFolder, 'Clips with ' +
                           strFolderName.upper()
                           + date)

    # reading the current folder just created in DaVinci Resolve
    davinciFolder = mediaPool.GetCurrentFolder()

    # imagePath encodes the images and print the names in console
    imagePath(path, images, classNames)
    encodeListKnown = findEncodings(images, encodeList)
    print('Encoding Complete')

    # filename gives the path of the files
    filenames = filedialog.askopenfilenames(
        title=('Choose The Videos For Analyzing'),
        filetypes=([("Video files", "*.mov;*.mp4")]))

    # this index is the index for the EDL
    index = 1

    # filename give the path of the file
    for filename in filenames:
        # inizialize the TC and the seconds
        videoTC = '00:00:00:00'
        seconds = 0

        # edlData is the list necessary for building the edl
        edlData = []

        # redear is an imageio object with different properties
        reader = imageio.get_reader(filename)
        # get metadata from the video: fps and duration
        fps = reader.get_meta_data()['fps']
        duration = reader.get_meta_data()['duration']

        # print the filename, fps and duration of the clips
        nameOfTheFile = filename.split('/')[-1]
        print('\n')
        print('Name', nameOfTheFile)
        print('FPS: ', fps)
        print('Duration: ', duration, '\n')

        # convert fps into string
        stringFps = str(fps)

        # get all metadata from the video
        metadata = ffmpeg.probe(filename)
        # vidFormatted = pprint.pformat(metadata)
        # print(pprint.pformat(metadata))

        # for loop iterate in the dictionary
        for key in metadata['streams']:
            # .get() method check dinamically if exist the key
            if key.get('tags').get('timecode'):
                # if timecode exist, it assigned to videoTC
                # this is a string that must convered in proper timecode
                videoTC = key.get('tags').get('timecode')
            else:
                videoTC = '00:00:00:00'

        # this is one second in TC format
        TC_one_second = Timecode(stringFps, '00:00:01:00')

        for i, frame in enumerate(reader):
            # img is a matrix that rappresent the image from the imageio object
            img = frame
            if i % round(fps) == 10:
                # resize the image
                imgS = cv2.resize(img, (0, 0), None, accuracy, accuracy)
                imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

                # imgS is an image rappresented by an array
                # encodesCurFrame - face misuraments
                # facesCurFrame - coordinates for box
                facesCurFrame = face_recognition.face_locations(imgS)
                encodesCurFrame = face_recognition.face_encodings(
                    imgS, facesCurFrame)

                frames = seconds * fps
                # seconds is a counter necessary to calculate the frames
                # with frames is possible to clculate the timecode based on fps
                # and then the timecode start is added.
                # -1 is one frame
                TC_in = Timecode(stringFps, frames_to_timecode(
                    frames, fps)) + Timecode(stringFps, videoTC) - 1

                print(TC_in)

                for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):

                    # matches is True or False
                    matches = face_recognition.compare_faces(
                        encodeListKnown, encodeFace)

                    # faceDis is the face prediction
                    faceDis = face_recognition.face_distance(
                        encodeListKnown, encodeFace)
                    matchIndex = np.argmin(faceDis)

                    # faceLoc is the position of the box
                    y1, x2, y2, x1 = faceLoc

                    # calculate the diagonal fot the type of shot
                    diagonal = int(sqrt((x2 - x1) ** 2 + (y2 - y1)))

                    # if matches[matchIndex] is true, there is the person
                    if matches[matchIndex]:
                        typeOfShot = type_of_shot(diagonal, accuracy)

                        # classNames is the list created with imagePath()
                        # [matchIndex] is the position number to find the
                        # person in the list
                        # .upper() method transform the text in uppercase
                        persons = classNames[matchIndex].upper()

                        TC_out = TC_in + TC_one_second - 1  # 1 is one frame

                        edlData.append(
                            [index, TC_in, TC_out, typeOfShot,
                             'Blue', persons])
                seconds += 1
                index += 1

        if edlData != []:
            # filename without extension
            fileName = filename.split('/')[-1].split('.')[0]

            # edl creation
            fName = folder + '/' + fileName
            createEDL(fName, listbox, classNames, fileName)

            edl = durationMarker(edlData)
            for i, a in enumerate(edl):

                # add all the clips for analyzing to the MediaPool
                mediaStorage.AddItemListToMediaPool(filename)

                # checking how many clips are in the folder
                clips = davinciFolder.GetClipList()

                clips[len(clips)-1].AddMarker((edl[i][0]*fps)-fps,
                                              edl[i][4],
                                              edl[i][5], edl[i][3],
                                              (edl[i][6]*fps-(fps-1)),
                                              '')

                writeEDL(fName,
                         edl[i][0],
                         edl[i][1],
                         edl[i][2],
                         edl[i][3],
                         edl[i][4],
                         edl[i][5],
                         edl[i][6]*fps
                         )

        index = 1
    # inizialize searche images
    for i, a in enumerate(classNames):
        classNames.pop(i)
        encodeList.pop(i)
        images.pop(i)

    print('Finished \n')


# close loop
root.mainloop()
