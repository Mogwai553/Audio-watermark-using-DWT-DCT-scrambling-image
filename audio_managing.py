from scipy.io import wavfile
import subprocess as sp
import platform
from utils import makeFileName
import os

AUDIO_PATH = 0
SAMPLERATE = 1
AUDIO_DATA = 2

#Read the file audio.wav from path
def readWavFile(path):
    samplerate, data = wavfile.read(path)
    tupleWav = (path, samplerate, data)
    return tupleWav

#Print some information about file audio    
def printMetadata(entry):
    print("Path: {}"\
          .format(entry[AUDIO_PATH]))
    print("\tsamplerate: {}"\
          .format(entry[SAMPLERATE]))
    print("\t#samples: {}"\
          .format(entry[AUDIO_DATA].shape))

#Save processed file audio with wav format
def saveWavFile(path, samplerate, signal):
    path = makeFileName("watermarked", path)
    wavfile.write(path, samplerate, signal)
    
#Join audio channels to only one
def joinAudioChannels(path):
    outPath = makeFileName("mono", path)
    if platform.system() == "Linux":
        cmdffmpeg_L = "ffmpeg -y -i {} -ac 1 -f wav {}"\
                    .format(path, outPath)
        os.system(cmdffmpeg_L)
    elif platform.system() == "Windows":
        cmdffmpeg_W = "./ffmpeg/bin/ffmpeg.exe -y -i {} -ac 1 -f wav {}"\
                    .format(path, outPath)
        sp.call(cmdffmpeg_W)
    return outPath

'''
TESTING
'''

tupleAudio = readWavFile("piano.wav")
printMetadata(tupleAudio)
saveWavFile(tupleAudio[AUDIO_PATH], tupleAudio[SAMPLERATE], tupleAudio[AUDIO_DATA])
monoAudio = joinAudioChannels(tupleAudio[AUDIO_PATH])

