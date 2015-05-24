'''
a tk gui to specify the geometry of a horn speaker
saves projects in xml format
will create an input file for simulation (element definition) 
'''

import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename

#configure root window
root = tk.Tk()
root.title("Edamni")
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
root.geometry('{}x{}'.format(600, 450) )

#configure master frame
windowFrame = tk.Frame(root)
windowFrame['background'] = '#e00'
windowFrame.grid(sticky=tk.N+tk.E+tk.S+tk.W)
windowFrame.columnconfigure(1, weight=1)
windowFrame.rowconfigure(0, weight=1)

#frame for radio buttons
modeSelectionFrame = ttk.Frame(windowFrame)
modeSelectionFrame['borderwidth'] = 2
modeSelectionFrame['relief'] = 'solid'
modeSelectionFrame.grid(sticky=tk.N)

ttk.Label(modeSelectionFrame, text="Mode").grid()

#radio button variable
mode = tk.StringVar()

#modes for the gui to be in
lModes = ['Speakers', 'Acoustic Circuit', 'Simulation', 'Results']

#create radio buttons for mode setting
for strMode in lModes:
	ttk.Radiobutton(modeSelectionFrame, text=strMode, variable=mode, value=strMode).grid()

#create frame for contents of program
mainFrame = tk.Frame(windowFrame)
mainFrame['background'] = '#0e0'
mainFrame['borderwidth'] = 2
mainFrame['relief'] = 'solid'
mainFrame.grid(row=0, column=1, sticky=tk.N+tk.E+tk.S+tk.W)

mainFrame.rowconfigure(0, weight=1)
mainFrame.columnconfigure(0, weight=1)

#create frame for mode speaker list
speakerFrame = tk.Frame(mainFrame)
speakerFrame['background'] = '#00e'
speakerFrame.rowconfigure(1, weight=1)
speakerFrame.columnconfigure(0, weight=1)

#frame for buttons
speakerButtonFrame = ttk.Frame(speakerFrame)
speakerButtonFrame.grid(sticky=tk.W)

#list for speakers
speakerListBox = tk.Listbox(speakerFrame)
speakerListBox['selectmode'] = tk.SINGLE
speakerListBox.grid(sticky=tk.N+tk.S+tk.W+tk.E)

#callbacks for buttons
def addSpeaker(*args):
	speakerFileName = askopenfilename(initialdir="../preprocessor/bcd")
	speakerListBox.insert(tk.END, speakerFileName)

def removeSpeaker(*args):
	lSelections = speakerListBox.curselection()
	if len(lSelections) == 0:
		return
	speakerListBox.delete(lSelections[0])

def moveSpeakerUp(*args):
	lSelections = speakerListBox.curselection()
	if len(lSelections) == 0:
		return
	iSelection = lSelections[0]
	if iSelection < 1:
		return
	strContent = speakerListBox.get(iSelection)
	speakerListBox.delete(iSelection)
	speakerListBox.insert(iSelection - 1, strContent)
	speakerListBox.selection_set(iSelection - 1)

def moveSpeakerDown(*args):
	lSelections = speakerListBox.curselection()
	if len(lSelections) == 0:
		return
	iSelection = lSelections[0]
	if iSelection >= speakerListBox.size()-1:
		return
	strContent = speakerListBox.get(iSelection)
	speakerListBox.delete(iSelection)
	speakerListBox.insert(iSelection + 1, strContent)
	speakerListBox.selection_set(iSelection + 1)

#create buttons
tk.Button(speakerButtonFrame, bitmap="@xbm/add.xbm", command=addSpeaker).grid(row=1, column=0)
tk.Button(speakerButtonFrame, bitmap="@xbm/remove.xbm", command=removeSpeaker).grid(row=1, column=1)
tk.Button(speakerButtonFrame, bitmap="@xbm/up.xbm", command=moveSpeakerUp).grid(row=1, column=2)
tk.Button(speakerButtonFrame, bitmap="@xbm/down.xbm", command=moveSpeakerDown).grid(row=1, column=3)

#create frame for mode acoustic circuit
acuCircuitFrame = ttk.Frame(mainFrame)
acuCircuitFrame.rowconfigure(1, weight=1)
acuCircuitFrame.columnconfigure(0, weight=1)

#frame for buttons
acuButtonFrame = tk.Frame(acuCircuitFrame)
acuButtonFrame['background'] = '#770'
acuButtonFrame.grid(sticky=tk.W+tk.E)

#canvas for circuit elements
acuCanvas = tk.Canvas(acuCircuitFrame)
acuCanvas['background'] = '#070'
acuCanvas.grid(row=1, column=0, sticky=tk.N+tk.S+tk.W+tk.E)

class MovableHandler:
	def __init__(self, canvas, widget, canvasID):#, canvas, canvasID):
		self.m_Canvas = canvas

		self.moving_widget = canvasID
		self.moving_x = 0
		self.moving_y = 0

		widget.bind("<ButtonPress-1>", self.onMovablePress)
		widget.bind("<ButtonRelease-1>", self.onMovableRelease)

	def onMovablePress(self, event):
#		self.moving_widget = self.m_Canvas.find_closest(event.x, event.y)[0]
		self.moving_x = event.x
		self.moving_y = event.y

	def onMovableRelease(self, event):
		dest_x = event.x
		dest_y = event.y

		delta_x = dest_x - self.moving_x
		delta_y = dest_y - self.moving_y

		self.m_Canvas.move(self.moving_widget, delta_x, delta_y)

#		self.moving_widget = None
		self.moving_x = 0
		self.moving_y = 0

#callbacks for buttons
def addAcousticElement(*args):
	print("adding element...")
	addElementDialog = tk.Toplevel(root)
	addElementDialog.transient(root)
	addElementDialog.grab_set()
	addElementDialog.wm_title("Add Acoustic Element")

	#modes for the gui to be in
	lElementTypes = ['Conical', 'Exponential', 'Mic', 'Open', 'Speaker', 'Wall']

	elemType = tk.StringVar()

	#create radio buttons for mode setting
	for iElementType in range(len(lElementTypes) ):
		strElemType = lElementTypes[iElementType]
		ttk.Radiobutton(addElementDialog, text=strElemType, variable=elemType, value=strElemType).grid(row = 1, column = iElementType)
		tk.Label(addElementDialog, bitmap="@xbm/" + strElemType.lower() + "0.xbm").grid(row=0, column = iElementType)

	def addElementToCanvas(*args):
		print("element type is " + elemType.get())
		elementFrame = ttk.Frame(acuCircuitFrame)

		canvasID = acuCanvas.create_window(100, 100, window=elementFrame, tags="movable")

		movingLabel = tk.Label(elementFrame, bitmap="@xbm/" + elemType.get().lower() + "0.xbm")
		movingLabel.grid(row = 1, column = 1)
		tk.Button(elementFrame, bitmap="@xbm/connector.xbm", command=exit).grid(row = 1, column = 0)
		tk.Button(elementFrame, bitmap="@xbm/connector.xbm", command=exit).grid(row = 1, column = 2)

		myHandler = MovableHandler(acuCanvas, movingLabel, canvasID)

		addElementDialog.destroy()

	#add button to create element
	tk.Button(addElementDialog, text="OK", command=addElementToCanvas).grid()
	#add button to cancel creation
	tk.Button(addElementDialog, text="Cancel", command=lambda:addElementDialog.destroy()).grid()


	root.wait_window(addElementDialog)

#create buttons
tk.Button(acuButtonFrame, bitmap="@xbm/add.xbm", command=addAcousticElement).grid(row=1, column=0)

#put up a window to modify element options

#dictionary with element options
dElements = dict(
	conical = [('length', 'm'),
			   ('damping constant', '1'),
			   ('A1', 'm^2'),
			   ('A2', 'm^2')],
	
	expo = [('length', 'm'),
			('A1', 'm^2'),
			('A2', 'm^2'),
			('exponent', '1')],
	 
	wall = [('damping thickness', 'm'),
			('damping transient', 'm'),
			('damping constant', 'Ns/m^4')],
	 
	space = [('length', 'm'),
			 ('fraction', '1')],
	
	speaker = [('index', '1')],
	
	fork = [('A1', 'm^2'),
			('A2', 'm^2'),
			('A3', 'm^2')],

	mic = []
	)

#create frame for element options


#create frame for mode simulation
simuFrame = ttk.Frame(mainFrame)
ttk.Button(simuFrame, text="Run Simulation", command=exit).grid()

#create frame for mode results
resultsFrame = ttk.Frame(mainFrame)
choiceLabel = ttk.Label(resultsFrame, text='xxx dB')
choiceLabel.grid()

dModeFrames = {'Speakers': speakerFrame, 'Acoustic Circuit': acuCircuitFrame, 'Simulation': simuFrame, 'Results': resultsFrame}

def onChangeMode(*args):
	#hide all other frames, show selected
	for subFrame in dModeFrames.values():
		subFrame.grid_remove()
	
	dModeFrames[mode.get()].grid(sticky=tk.N+tk.E+tk.S+tk.W)

#initialize to speaker mode
mode.trace("w", onChangeMode)
mode.set(lModes[0])

#start the whole thing
root.mainloop()
