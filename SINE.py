import matplotlib.pyplot as plt
import pyaudio, wave
import numpy as np

from collections import OrderedDict as OD
from struct import pack
from math import fmod
from os import system

def getNoteAndDuration(chord : str, defaultDuration : float):
    if ',' in chord:
        note,duration = chord.strip('()').split(',')
        return note,float(duration)
    return chord,defaultDuration

def generateSineWave(samplingFreq : int = 44100, freq : float = 440.0, amplitude : float = 0.4, duration : float = 1.0, phase : float = 0, chunk : int = 0):
    t = np.arange(samplingFreq*duration)/samplingFreq if not chunk else np.arange(chunk)/samplingFreq
    sineWave = amplitude*np.sin(2 * pi * freq * t + phase)
    return sineWave

def generateSong(keysOfChords : [str], samplingFreq : int = 44100, amplitude : float = 0.4, defaultDuration : float = 0.5, phase : float = 0):
    song = np.array([])
    for chord in keysOfChords:
        note, duration = getNoteAndDuration(chord,defaultDuration)
        noteFreq = octaves[note]
        sineWave = generateSineWave(samplingFreq,noteFreq,amplitude,duration,phase)
        phase = fmod(2.0 * pi * noteFreq * duration + phase, 2.0*pi)
        song = np.concatenate((song,sineWave))
    return song

def playAudio(samples,samplingFreq : int = 44100):
    stream = p.open(format = pyaudio.paFloat32, channels = 1, rate = samplingFreq, output = True)
    stream.write(samples.astype(np.float32).tostring())
    stream.close()

def playAudioFromFile(path : str):
    wf = wave.open(path,'rb') 
    stream = p.open(format = p.get_format_from_width(wf.getsampwidth()), channels = wf.getnchannels(), rate = wf.getframerate(), output = True)
    chunk = 4096

    data = wf.readframes(chunk)
    while data:
        stream.write(data)
        data = wf.readframes(chunk)

    stream.close()
    wf.close()

def pad(data : [float]):
    nextPowerOf2 = lambda x: 1 << (x-1).bit_length()
    return np.concatenate((data,np.zeros(nextPowerOf2(len(data))-len(data))))

def plot(data : [float], nchannels : int = 1, samplingFreq : int = 44100):
    formerLen,data = len(data),pad(data)
    channels = [[] for channel in range(nchannels)]
    for index, channelData in enumerate(data):
        channels[index%len(channels)].append(channelData)
    t=np.linspace(0, int(formerLen/len(channels)/samplingFreq), num=int(formerLen/len(channels)))

    fig,ax = plt.subplots(nrows=2,ncols=2)
    fig.tight_layout()
    for idx in range(len(channels)):
        ax[0,idx].plot(t,channels[idx][:formerLen//nchannels],color='C'+str(idx))
        ax[0,idx].set_title('Signal (channel %i)' %(idx+1))
        ax[0,idx].set_xlabel('Time')
        ax[0,idx].set_ylabel('Amplitude')

    n = len(data)
    T = n/samplingFreq
    frq = np.arange(n)/T
    frq = frq[range(n//2)]
    for idx in range(len(channels)):
        FFT = (np.fft.fft(channels[idx])/n)[range(n//2)]
        ax[1,idx].plot(frq,abs(FFT),color='C'+str(idx+2))
        ax[1,idx].set_title('Spectrum (channel %i)' %(idx+1))
        ax[1,idx].set_xlabel('Freq (Hz)')
        ax[1,idx].set_ylabel('Magnitude')
    plt.subplots_adjust(left=0.125, bottom=0.1, right=0.9, top=0.9, wspace=0.5, hspace=0.5)
    plt.show()

def plotFromFile(path : str):
    wf = wave.open(path,'rb')
    data = np.frombuffer(wf.readframes(wf.getnframes()), np.int16)/32767
    plot(data, wf.getnchannels(),wf.getframerate())
    wf.close()

def groupByChunk(n, iterable):
    l = len(iterable)
    for idx in range(0,l,n):
        yield iterable[idx:min(idx+n,l)]

def saveFile(fileName : str, samples : [float], sampleFreq : int = 44100):
    wf=wave.open(fileName,"w")
    nchannels = 1; sampwidth = 2
    wf.setparams((nchannels, sampwidth, sampleFreq, len(samples), "NONE", "not compressed"))
    
    for chunk in groupByChunk(4096,samples):
        wf.writeframes(b''.join(map(lambda sample : pack('<h', int(sample * 32767)),chunk)))

    wf.close()

def getParamsSineWave():
    parameters = OD()
    inputs = [input('Sampling Frequency (Hz | default = 44100): '),input('Sinewave Frequency (Hz | default = 440.0): '),input('Amplitude ( float (0,1] | default = 0.4): '),input('Duration ( s | default = 1): '),input('Phase ( radians | default = 0): ')]
    parameters['samplingFreq'] = int(inputs[0]) if inputs[0] else 44100
    parameters['freq'] = float(inputs[1]) if inputs[1] else 440.0
    parameters['amplitude'] = float(inputs[2]) if inputs[2] else 0.4
    parameters['duration'] = float(inputs[3]) if inputs[3] else 1
    parameters['phase'] = eval(inputs[4]) if inputs[4] else 0
    return parameters

def getParamsSong():
    parameters = OD()
    inputs = [input('Insert the path to a txt file with keys of chords (more info in help.txt): '), input('Sampling Frequency (Hz | default = 44100): '),input('Amplitude ( float (0,1] | default = 0.4): '),input('Duration ( s | default = 0.4): '),input('Phase ( radians | default = 0): ')]
    f = open(inputs[0],'r')
    parameters['keysOfChords'] = f.read().split()
    parameters['samplingFreq'] = int(inputs[0]) if inputs[1] else 44100
    parameters['amplitude'] = float(inputs[2]) if inputs[2] else 0.4
    parameters['duration'] = float(inputs[3]) if inputs[3] else 0.4
    parameters['phase'] = eval(inputs[4]) if inputs[4] else 0
    f.close()
    return parameters

def getParamsFile():
    return input('Path to a wav file: ')

pi = np.pi
p = pyaudio.PyAudio()
octaves = {
    'C0': 16.35, 'C#0': 17.32, 'D0': 18.35, 'D#0': 19.45, 'E0': 20.6, 'F0': 21.83, 'F#0': 23.12, 'G0': 24.5, 'G#0': 25.96, 'A0': 27.5, 'A#0': 29.14, 'B0': 30.87,
    'C1': 32.70, 'C#1': 34.65, 'D1': 36.71, 'D#1': 38.89, 'E1': 41.20, 'F1': 43.65, 'F#1': 46.25, 'G1': 49.0, 'G#1': 51.91, 'A1': 55.0, 'A#1': 58.27, 'B1': 61.74,
    'C2': 65.41, 'C#2': 69.3, 'D2': 73.42, 'D#2': 77.78, 'E2': 82.41, 'F2': 87.31, 'F#2': 92.5, 'G2': 98.0, 'G#2': 103.83, 'A2': 110.0, 'A#2': 116.54, 'B2': 123.47,
    'C3': 130.81, 'C#3': 138.59, 'D3': 146.83, 'D#3': 155.56, 'E3': 164.81, 'F3': 174.62, 'F#3': 185.0, 'G3': 196.0, 'G#3': 207.65, 'A3': 220.0, 'A#3': 233.08, 'B3': 246.94,
    'C4': 261.62, 'C#4': 277.19, 'D4': 293.67, 'D#4': 311.12, 'E4': 329.62, 'F4': 349.23, 'F#4': 370.0, 'G4': 392.0, 'G#4': 415.31, 'A4': 440.0, 'A#4': 466.17, 'B4': 493.88,
    'C5': 523.25, 'C#5': 554.37, 'D5': 587.33, 'D#5': 622.25, 'E5': 659.25, 'F5': 698.46, 'F#5': 739.99, 'G5': 783.99, 'G#5': 830.61, 'A5': 880.0, 'A#5': 932.33, 'B5': 987.77,
    'C6': 1046.5, 'C#6': 1108.74, 'D6': 1174.66, 'D#6': 1244.5, 'E6': 1318.5, 'F6': 1396.92, 'F#6': 1479.98, 'G6': 1567.98, 'G#6': 1661.22, 'A6': 1760.0, 'A#6': 1864.66,'B6': 1975.54,
    'C7': 2093.0, 'C#7': 2217.48, 'D7': 2349.32, 'D#7': 2489.0, 'E7': 2637.0, 'F7': 2793.84, 'F#7': 2959.96, 'G7': 3135.96, 'G#7': 3322.44,'A7': 3520.0, 'A#7': 3729.32, 'B7': 3951.08,
    'C8': 4186.0, 'C#8': 4434.96, 'D8': 4698.64, 'D#8': 4978.0, 'E8': 5274.0, 'F8': 5587.68, 'F#8': 5919.92, 'G8': 6271.92, 'G#8': 6644.88, 'A8': 7040.0, 'A#8': 7458.64, 'B8': 7902.16,
    '.': 0
}

choice1 = int(input('Select an option:\n1 - Generate sine wave\n2 - Generate song\n3 - Load wav file\n\nYour choice (1,2 or 3): '))
if choice1 not in [1,2,3]: raise ValueError('Invalid choice: %i' %choice1)
options = {1: getParamsSineWave, 2:getParamsSong, 3:getParamsFile}
param = options[choice1]()
system('cls||clear')

dialog = 'Select an option:\n1 - Play\n2 - Plot\n3 - Save\n4 - Exit\n\nYour choice (1,2,3 or 4): '
dialog2 = 'Select an option:\n1 - Play\n2 - Plot\n3 - Exit\n\nYour choice (1,2 or 3): '

while True:
    choice2 = int(input(dialog)) if choice1 in [1,2] else int(input(dialog2))
    if choice1 in [1,2]:
        dataSine = generateSineWave(*param.values()) if choice1 == 1 else None
        dataSong = generateSong(*param.values()) if choice1 == 2 else None
        if choice2 == 1:
            playAudio(dataSine, param['samplingFreq']) if choice1 == 1 else playAudio(dataSong,param['samplingFreq'])
        elif choice2 == 2:
            plot(dataSine, samplingFreq = param['samplingFreq']) if choice1 == 1 else plot(dataSong, samplingFreq = param['samplingFreq'])
        elif choice2 == 3:
            fileName = input('File name: ')
            saveFile(fileName,dataSine if choice1 == 1 else dataSong,param['samplingFreq'])
        elif choice2 == 4:
            break

    elif choice1 == 3:
        if choice2 == 1:
            playAudioFromFile(param)
        elif choice2 == 2:
            plotFromFile(param)
        elif choice2 == 3:
            break
    system("cls||clear")

p.terminate() 