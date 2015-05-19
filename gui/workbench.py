'''
a tk gui to specify the geometry of a horn speaker
saves projects in xml format
will create an input file for simulation (element definition) 
'''

import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename

root = tk.Tk()
root.title("Edamni")
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
root.geometry('{}x{}'.format(600, 450) )

windowFrame = tk.Frame(root)
windowFrame['background'] = '#e00'
windowFrame.grid(sticky=tk.N+tk.E+tk.S+tk.W)
windowFrame.columnconfigure(1, weight=1)
windowFrame.rowconfigure(0, weight=1)

lModes = ['Speakers', 'Acoustic Circuit', 'Simulation', 'Results']

modeSelectionFrame = ttk.Frame(windowFrame)
modeSelectionFrame['borderwidth'] = 2
modeSelectionFrame['relief'] = 'solid'
modeSelectionFrame.grid(sticky=tk.N)

ttk.Label(modeSelectionFrame, text="Mode").grid()

mode = tk.StringVar()

#create radio buttons for the simulation elements

for strMode in lModes:
    ttk.Radiobutton(modeSelectionFrame, text=strMode, variable=mode, value=strMode).grid()

mainFrame = tk.Frame(windowFrame)
mainFrame['background'] = '#0e0'
mainFrame['borderwidth'] = 2
mainFrame['relief'] = 'solid'
mainFrame.grid(row=0, column=1, sticky=tk.N+tk.E+tk.S+tk.W)

mainFrame.rowconfigure(0, weight=1)
mainFrame.columnconfigure(0, weight=1)

speakerFrame = tk.Frame(mainFrame)
speakerFrame['background'] = '#00e'
speakerListBox = tk.Listbox(speakerFrame)
speakerListBox.grid(sticky=tk.N+tk.S+tk.W+tk.E)

speakerFrame.rowconfigure(0, weight=1)
speakerFrame.columnconfigure(0, weight=1)

buttonFrame = ttk.Frame(speakerFrame)
buttonFrame.grid(sticky=tk.W)

def addSpeaker(*args):
	speakerFileName = askopenfilename(initialdir="../preprocessor/bcd")
	speakerListBox.insert(tk.END, speakerFileName)

ttk.Button(buttonFrame, text="Add Speaker", command=addSpeaker).grid(row=1, column=0)
ttk.Button(buttonFrame, text="Remove Speaker", command=addSpeaker).grid(row=1, column=1)
ttk.Button(buttonFrame, text="Move Up", command=addSpeaker).grid(row=1, column=2)
ttk.Button(buttonFrame, text="Move Down", command=addSpeaker).grid(row=1, column=3)


acuCircuitFrame = ttk.Frame(mainFrame)
ttk.Button(acuCircuitFrame, text="Add Element", command=exit).grid()

simuFrame = ttk.Frame(mainFrame)
ttk.Button(simuFrame, text="Run Simulation", command=exit).grid()

resultsFrame = ttk.Frame(mainFrame)
choiceLabel = ttk.Label(resultsFrame, text='xxx dB')
choiceLabel.grid()

dModeFrames = {'Speakers': speakerFrame, 'Acoustic Circuit': acuCircuitFrame, 'Simulation': simuFrame, 'Results': resultsFrame}

def onChangeType(*args):
	#hide all other frames, show selected
    for subFrame in dModeFrames.values():
        subFrame.grid_remove()
    
    dModeFrames[mode.get()].grid(sticky=tk.N+tk.E+tk.S+tk.W)

mode.trace("w", onChangeType)
mode.set(lModes[0])

root.mainloop()
