from utils import setLastBit, getLastBit, decToBinary, binaryToDec
from PIL import Image
from audio_managing import frameToAudio
from image_managing import binarization, grayscale, imgSize
import numpy as np
import math

ALPHA = 0.1

#Check if the image is in grayscale and covert it in this mode
def isImgGrayScale(image):
    if image.mode != "L":
        image = grayscale(image)
    return image

#Check if the image is in binary and covert it in this mode
def isImgBinary(image):
    if image.mode != "1":
        image = binarization(image)
    return image

#Embedding of width and height. Audio must be linear and not frames
def sizeEmbedding(audio, width, height):
    bWidth = decToBinary(width, 16)
    bHeight = decToBinary(height, 16)

    #Embedding width and heigth
    for w in range(16):
        audio[w] = setLastBit(audio[w],int(bWidth[w]))
        audio[w+16] = setLastBit(audio[w+16],int(bHeight[w]))

    return audio

def sizeExtraction(audio):
    bWidth, bHeight = ("","")

    #Extraction of width and height
    for w in range(16):
        bWidth += str(getLastBit(audio[w]))
        bHeight += str(getLastBit(audio[w+16]))

    width = binaryToDec(bWidth)
    height = binaryToDec(bHeight)

    return width, height

#Check if audio is divided in frames:
    # if true, it joins audio and then the reverse will be called
    # if false, it does nothing
def isJoinedAudio(audio):
    if type(audio[0]) in (int, float):
        numOfFrames = -1 #Audio is not divided in frame  
        joinAudio = audio
    else:
        numOfFrames = audio.shape[0]
        joinAudio = frameToAudio(audio)
    return joinAudio, numOfFrames

def iisJoinedAudio(audio):
    return audioToFrame(joinAudio, numOfFrames)

def LSB(audio, image):   
    image = isImgBinary(image)
    
    #Verify if audio is divided in frames
    if type(audio[0]) is int:
        numOfFrames = -1 #Audio is not divided in frame  
        joinAudio = audio
    else:
        numOfFrames = audio.shape[0]
        joinAudio = frameToAudio(audio)

    width, height = image.size
    audioLen = len(joinAudio)
    
    if (width * height) + 32 >= audioLen:
        print("LEAST SIGNIFICANT BIT: Cover dimension is not sufficient for this payload size!")
        return

    joinAudio = sizeEmbedding(joinAudio, width, height)

    #Embedding watermark
    for i in range(width):
        for j in range(height):
            value = image.getpixel(xy=(i,j))
            x = i*height + j
            joinAudio[x + 32] = setLastBit(joinAudio[x + 32],value)

    if numOfFrames is not -1:
        return audioToFrame(joinAudio, numOfFrames)
    else:
        return joinAudio
    

def iLSB(audio):
    #Verify if audio is divided in frames
    if type(audio[0]) is int:
        numOfFrames = -1 #Audio is not divided in frame  
        joinAudio = audio
    else:
        numOfFrames = audio.shape[0]
        joinAudio = frameToAudio(audio)
    
    width, height = sizeExtraction(joinAudio)
    
    image = Image.new("1",(width,height))

    #Extraction watermark
    for i in range(width):
        for j in range(height):
            x = i*height + j
            value = getLastBit(joinAudio[x+32])
            image.putpixel(xy=(i,j),value=value)

    return image

#Delta embedding mixed with LSB technique for embedding of width and height
def deltaDCT(coeffs, image):
    image = isImgGrayScale(image)
    
    #Verify if audio is divided in frames
    if type(coeffs[0]) is int:
        numOfFrames = -1 #Audio is not divided in frame  
        joinCoeffs = coeffs
    else:
        numOfFrames = coeffs.shape[0]
        joinCoeffs = frameToAudio(coeffs)

    coeffsLen = len(joinCoeffs)
    width, height = image.size
    if (width * height) + 32 >= coeffsLen:
        print("DELTA DCT: Cover dimension is not sufficient for this payload size!")
        return

    joinCoeffs = sizeEmbedding(joinCoeffs, width, height)

    #Embedding watermark
    for i in range(width):
        for j in range(height):
            value = image.getpixel(xy=(i,j))
            x = i*height + j
            joinCoeffs[x+32] = joinCoeffs[x+32] + normalize(value,255)

    if numOfFrames is not -1:
        return audioToFrame(joinCoeffs, numOfFrames)
    else:
        return joinCoeffs

def ideltaDCT(coeffs, wCoeffs):
    #Verify if audio is divided in frames
    if type(audio[0]) is int:
        numOfFrames = -1 #Audio is not divided in frame  
        joinCoeffs = coeffs
        joinWCoeffs = wCoeffs
    else:
        numOfFrames = coeffs.shape[0]
        joinCoeffs = frameToAudio(coeffs)
        joinWCoeffs = frameToAudio(wCoeffs)
    
    width, height = sizeExtraction(joinCoeffs)

    extracted = Image.new("L",(width,height))
    coeffsLen = len(coeffs)

    #Extraction watermark
    for i in range(width):
        for j in range(height):
            x = i*height + j
            value = coeffs[x] - image.getpixel(xy=(i,j))
            extracted.putpixel(xy=(i,j),value=value)

#The watermark is embedded into k coefficents of greater magnitudo
def magnitudoDCT(coeffs, watermark, alpha):
    watermark = isImgBinary(watermark)
    print(np.asarray(watermark))
    watermark = createImgArrayToEmbed(watermark)
    print(watermark)
    coeffs, joinFlag = isJoinedAudio(coeffs)
    coeffs = coeffs[:len(watermark)] #to delete for main.py
    wCoeffs = []
    if(len(coeffs) == len(watermark)):
        for i in range(len(coeffs)):
            wCoeffs.append(((coeffs[i])*(1 + alpha*watermark[i])))
        #wCoeffs = np.asarray(wCoeffs)
        if joinFlag != -1:
            wCoeffs = iisJoinedAudio(wCoeffs)
        return wCoeffs
    else:
        print("magnitudoDCT: error because DCT coefficients and watermark coefficients must have same length")
        return None

#The extraction of watermark from k coefficents of greater magnitudo       
def imagnitudoDCT(coeffs, wCoeffs, alpha):
    coeffs, joinCoeffsFlag = isJoinedAudio(coeffs)
    wcoeffs, joinWCoeffsFlag = isJoinedAudio(wCoeffs)
    coeffs = coeffs[:len(wCoeffs)]
    watermark = []
    for i in range(len(coeffs)):
        #watermark.append(math.ceil((wCoeffs[i] - coeffs[i])/(coeffs[i]*alpha)))
        watermark.append(wCoeffs[i] - coeffs[i])
    return watermark

#Routine procedure to embedd the shape of image into flatted array of it
def createImgArrayToEmbed(image):
    width, heigth = imgSize(image)
    flattedImage = [width, heigth]
    tmp = np.ravel(image)
    for i in range(len(tmp)):
        flattedImage.append(tmp[i])
    return flattedImage

'''
TESTING
'''


audio = [1,5,6,7,8,9,4,5,6,1,3,5,4,7,1,5,6,7,8,9,4,5,6,1,3,5,4,7,1,5,6,7,8,9,4,5,6,1,3,5,4,7,5,6,7]
image = Image.new("1",(3,4))
image.putpixel(xy=(1,2),value=1)
lsb = LSB(audio,image)
print(np.asarray(iLSB(lsb)))

#flattedImage = createImgArrayToEmbed(image)
#print("flatted image: ", flattedImage)
#lenFlattedImage = len(flattedImage)
#coeffs = audio[:lenFlattedImage]
wCoeffs = magnitudoDCT(audio, image, ALPHA)
print("watermarked coeffs: ", wCoeffs)
watermark = imagnitudoDCT(audio, wCoeffs, ALPHA)
print("extracted watermark: ", watermark)

