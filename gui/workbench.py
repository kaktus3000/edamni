'''
a tk gui to specify the geometry of a horn speaker
saves projects in xml format
will create an input file for simulation (element definition)
'''

#gui stuff
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename
from tkinter import messagebox
import configparser
import numpy
import decimal

from PIL import Image

from subprocess import call

#fancy stuff
from functools import partial

#xml support
import xml.etree.ElementTree as ET

#configure root window
root = tk.Tk()
root.title("Edamni")
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
root.geometry('{}x{}'.format(600, 450) )

#configure menu
menubar = tk.Menu(root)
# create a pulldown menu, and add it to the menu bar
filemenu = tk.Menu(menubar, tearoff=0)
filemenu.add_command(label="Open", command=lambda:loadDefinition(askopenfilename(initialdir="../testcases/", filetypes=[("XML files","*.xml")])))
filemenu.add_command(label="Save", command=lambda:saveDefinition(asksaveasfilename(initialdir="../testcases/", defaultextension = ".xml", filetypes=[("XML files","*.xml")])))
filemenu.add_separator()
filemenu.add_command(label="Exit", command=root.quit)
menubar.add_cascade(label="File", menu=filemenu)

#global settings
g_fDeltaX = 0.01

def configureDialog():
	return

settingsmenu = tk.Menu(menubar, tearoff=0)
settingsmenu.add_command(label="Configure", command=configureDialog)
menubar.add_cascade(label="Settings", menu=settingsmenu )

helpmenu = tk.Menu(menubar, tearoff=0)
helpmenu.add_command(label="About", command=lambda: messagebox.showwarning("About", "Edamni v0.0 dev") )
menubar.add_cascade(label="Help", menu=helpmenu )

root.config(menu=menubar)

#configure master frame
windowFrame = tk.Frame(root)
#windowFrame['background'] = '#e00'
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
#mainFrame['background'] = '#0e0'
mainFrame['borderwidth'] = 2
mainFrame['relief'] = 'solid'
mainFrame.grid(row=0, column=1, sticky=tk.N+tk.E+tk.S+tk.W)

mainFrame.rowconfigure(0, weight=1)
mainFrame.columnconfigure(0, weight=1)

#create frame for mode speaker list
speakerFrame = tk.Frame(mainFrame)
#speakerFrame['background'] = '#00e'
speakerFrame.rowconfigure(1, weight=1)
speakerFrame.columnconfigure(0, weight=1)

#frame for buttons
speakerButtonFrame = ttk.Frame(speakerFrame)
speakerButtonFrame.grid(sticky=tk.W)

#list for speakers
speakerListBox = tk.Listbox(speakerFrame)
speakerListBox['selectmode'] = tk.SINGLE
speakerListBox.grid(sticky=tk.N+tk.S+tk.W+tk.E)

#frame to display speaker properties

speakerPropertyFrame = ttk.Frame(speakerFrame)
speakerPropertyFrame.grid(sticky=tk.S+tk.W)

speakerPropertyNameFrame = ttk.Frame(speakerPropertyFrame)
speakerPropertyNameFrame.grid(row = 0, column = 0)

speakerPropertyValueFrame = ttk.Frame(speakerPropertyFrame)
speakerPropertyValueFrame.grid(row = 0, column = 1)

speakerPropertyUnitFrame = ttk.Frame(speakerPropertyFrame)
speakerPropertyUnitFrame.grid(row = 0, column = 2)

#mapping property -> display label
dPropDisplay = {"Cms" : None,
				"Sd"  : None,
				"Re"  : None,
				"BL"  : None,
				"Mmd" : None,
				"Rms" : None,
				"Le"  : None}

dPropUnits = {"Cms" : "m/N",
			  "Sd"  : "m^2",
			  "Re"  : "Ohms",
			  "BL"  : "Tm",
			  "Mmd" : "kg",
			  "Rms" : "kg/s",
			  "Le"  : "H"}

#create labels to display speaker properties
for strProp in dPropDisplay:
	tk.Label(speakerPropertyNameFrame, text = strProp).grid()
	label = tk.Label(speakerPropertyValueFrame, text = "no data")
	dPropDisplay[strProp] = label
	label.grid()
	tk.Label(speakerPropertyUnitFrame, text = dPropUnits[strProp]).grid()

g_dSpeakers = dict()

decimal.getcontext().prec = 3

def onListBoxSelect(evt):
	w = evt.widget
	if len(w.curselection()) < 1:
		return
	index = int(w.curselection()[0])
	
	strSelectedSpeaker = w.get(index)
	
	#clear labels
	for strProp in dPropDisplay:
		dPropDisplay[strProp].text = "no data"

	if not strSelectedSpeaker in g_dSpeakers:
		return

	for strProp in dPropDisplay:
		if not strProp in g_dSpeakers[strSelectedSpeaker]:
			print("missing speaker property", strProp)
			return
		
		decimalValue = decimal.Decimal (g_dSpeakers[strSelectedSpeaker][strProp])
		strValue = decimalValue.normalize().to_eng_string()
		
		dPropDisplay[strProp].configure(text = strValue )

speakerListBox.bind('<<ListboxSelect>>', onListBoxSelect)

def readSpeakerXML(rootNode):
	strSpeakerName = rootNode.attrib["id"].lower()
	
	print("reading speaker", strSpeakerName)
	
	dProps = dict()
	#read properties
	for prop in rootNode:
		dProps[prop.tag] = float(prop.text)
		print("speaker property", prop.tag, "->", prop.text)
	#assign properties to global speaker buffer
	if not strSpeakerName in g_dSpeakers:
		g_dSpeakers[strSpeakerName] = dProps
	
	return strSpeakerName

def writeSpeakerXML(strSpeakerName, rootElem):
	#write speaker xml file
	rootElem.attrib["id"] = strSpeakerName

	for key in g_dSpeakers[strSpeakerName].keys():
		valueElem = ET.SubElement(rootElem, key)
		valueElem.text = str(g_dSpeakers[strSpeakerName][key])

#callbacks for buttons
def addSpeaker(*args):
	strSpeakerFile = askopenfilename(initialdir="../database", filetypes=[("XML files","*.xml")])
	tree = ET.parse(strSpeakerFile)
	strSpeakerName = readSpeakerXML(tree.getroot() )
	
	speakerListBox.insert(tk.END, strSpeakerName)

def removeSpeaker(*args):
	lSelections = speakerListBox.curselection()
	if len(lSelections) == 0:
		return
	strSpeaker = speakerListBox.get(lSelections[0] )

	print(strSpeaker)
	del g_dSpeakers[strSpeaker ]

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
#acuButtonFrame['background'] = '#770'
acuButtonFrame.grid(sticky=tk.W+tk.E)

#canvas for circuit elements
acuCanvas = tk.Canvas(acuCircuitFrame)
acuCanvas['background'] = '#fff'
acuCanvas.grid(row=1, column=0, sticky=tk.N+tk.S+tk.W+tk.E)

#dictionary with element options
#buttons: row, column
#in the four rotation states
g_dElements = dict(
	Conical = [[[(1, 0), (2, 1), (1, 2), (0, 1)], [(1, 2), (0, 1), (1, 0), (2, 1)]],
			('A1', 'm^2'),
			('A2', 'm^2'),
			('length', 'm'),
			('damping constant', 'Ns/m^4')],
			
	Prismatic = [[[(1, 0), (2, 1), (1, 2), (0, 1)], [(1, 2), (0, 1), (1, 0), (2, 1)]],
			('A1', 'm^2'),
			('A2', 'm^2'),
			('length', 'm'),
			('damping constant', 'Ns/m^4')],

	Exponential = [ [[(1, 0), (2, 1), (1, 2), (0, 1)], [(1, 2), (0, 1), (1, 0), (2, 1)]],
			('A1', 'm^2'),
			('A2', 'm^2'),
			('length', 'm'),
			('damping constant', 'Ns/m^4')],

	Wall = [ [[(1, 2), (0, 1), (1, 0), (2, 1)]],
			('A1', 'm^2'),
			('damping thickness', 'm'),
			('damping transient', 'm'),
			('damping constant', 'Ns/m^4')],

	Space = [ [[(1, 0), (2, 1), (1, 2), (0, 1)]],
			('A1', 'm^2'),
			('length', 'm'),
			('fraction', '1')],

	Speaker = [[[(1, 0), (2, 1), (1, 2), (0, 1)], [(1, 2), (0, 1), (1, 0), (2, 1)]],
			('A1', 'm^2'),
			('A2', 'm^2'),
			('type', '')],
	
	#TODO: handle forks
	Fork = [[[(1, 0), (2, 1), (1, 2), (0, 1)], [(0, 2), (0, 0), (2, 0), (2, 2)], [(2, 2), (0, 2), (0, 0), (2, 0)]],
			('A1', 'm^2'),
			('A2', 'm^2'),
			('A3', 'm^2')],
	
	Mic = [ [[(1, 0), (2, 1), (1, 2), (0, 1)], [(1, 2), (0, 1), (1, 0), (2, 1)]],
			('A1', 'm^2'),
			('A2', 'm^2'),
			('name', '')]
)

g_dAcousticElements = dict()

class Element:
	def __init__(self, strType, lValues, lOptID, lOptMin, lOptMax, frame, lButtons, handler):
		#type
		self.m_Type = strType

		#stored input values
		self.m_lValues = lValues
		
		#optimization optoins
		self.m_lOptID = lOptID
		self.m_lOptMin = lOptMin
		self.m_lOptMax = lOptMax

		#frame on canvas
		self.m_Frame = frame

		#list of connection buttons inside frame
		self.m_lButtons = lButtons

		#rotation state of buttons and image
		self.m_iRotation = 0

		#gui callback object
		self.m_MovableHandler = handler

class MovableHandler:
	def __init__(self, imageWidget, strElemID):
		self.imageWidget = imageWidget
		self.strID = strElemID
		self.moving_x = 0
		self.moving_y = 0

		imageWidget.bind("<ButtonPress-1>", self.onMovablePress)
		imageWidget.bind("<ButtonRelease-1>", self.onMovableRelease)
		imageWidget.bind("<ButtonRelease-3>", self.onRMBRelease)
		imageWidget.bind("<Double-Button-1>", self.onDoubleClick)

	def onMovablePress(self, event):
		self.moving_x = event.x
		self.moving_y = event.y

	def onMovableRelease(self, event):
		dest_x = event.x
		dest_y = event.y

		delta_x = dest_x - self.moving_x
		delta_y = dest_y - self.moving_y

		acuCanvas.move(g_dAcousticElements[self.strID].m_Frame, delta_x, delta_y)

		acuCanvas.after_idle(drawCanvasLines)

		self.moving_x = 0
		self.moving_y = 0

	def onRMBRelease(self, event):
		g_dAcousticElements[self.strID].m_iRotation += 1
		if g_dAcousticElements[self.strID].m_iRotation > 3:
			g_dAcousticElements[self.strID].m_iRotation = 0
			
		iRot = g_dAcousticElements[self.strID].m_iRotation

		strBitmap = self.imageWidget['bitmap']
		self.imageWidget['bitmap'] = strBitmap.replace(strBitmap[-5], str(iRot) )

		#relocate the buttons
		strElementType = self.imageWidget['text']
		buttonPositions = g_dElements[strElementType][0]

		#get list of buttons from dictionary
		lButtons = g_dAcousticElements[self.strID].m_lButtons

		for iButton in range(len(buttonPositions)):
			buttonRow, buttonCol = buttonPositions[iButton][iRot]
			lButtons[iButton].grid(row = buttonRow, column = buttonCol)

		acuCanvas.after(1,drawCanvasLines)

	def onDoubleClick(self, event):
		editElementDialog = tk.Toplevel(root)
		editElementDialog.transient(root)
		editElementDialog.bind("<Map>", lambda event:editElementDialog.grab_set())
		editElementDialog.wm_title("Acoustic Element Properties")

		strElementType = self.imageWidget['text']

		head_font = ("Helvetica", 11, "bold")
		# columns headers
		ttk.Label(editElementDialog, text="prop", font=head_font) .grid(column=0, row=0)
		ttk.Label(editElementDialog, text="value", font=head_font).grid(column=1, row=0)
		ttk.Label(editElementDialog, text="unit", font=head_font) .grid(column=2, row=0)
		ttk.Label(editElementDialog, text="ID", font=head_font)   .grid(column=3, row=0)
		ttk.Label(editElementDialog, text="min", font=head_font)  .grid(column=4, row=0)
		ttk.Label(editElementDialog, text="max", font=head_font)  .grid(column=5, row=0)
		
		#add all the properties
		gridRow = 1

		lValueVars = []
		lOptIDVars = []
		lOptMinVars = []
		lOptMaxVars = []

		for iProp in range(len(g_dElements[strElementType]) - 1):
			propName, propUnit = g_dElements[strElementType][1 + iProp]

			ttk.Label(editElementDialog, text=propName).grid(column=0, row=gridRow)

			value = g_dAcousticElements[self.strID].m_lValues[iProp]
			
			#if this is a speaker, add membrane area
			if g_dAcousticElements[self.strID].m_Type == "Speaker" and propName[0] == "A":
				strSpeaker = g_dAcousticElements[self.strID].m_lValues[2]
				if strSpeaker in g_dSpeakers:
					dSpeakerProps = g_dSpeakers[strSpeaker]
					fMembraneArea = dSpeakerProps["Sd"]
					value = fMembraneArea
				
			lValueVars.append(tk.StringVar())
			lValueVars[-1].set(str(value))
			lOptIDVars.append(tk.StringVar())
			# optimization settings
			lOptIDVars[-1].set(g_dAcousticElements[self.strID].m_lOptID[iProp])
			lOptMinVars.append(tk.StringVar())
			lOptMinVars[-1].set(str(g_dAcousticElements[self.strID].m_lOptMin[iProp]))
			lOptMaxVars.append(tk.StringVar())
			lOptMaxVars[-1].set(str(g_dAcousticElements[self.strID].m_lOptMax[iProp]))

			#a specialty
			if g_dAcousticElements[self.strID].m_Type == "Speaker":
				if propName == "type":
					#get speaker model names
					lstrSpeakers = []
					for iSpeaker in range(speakerListBox.size()):
						strListBoxEntry = speakerListBox.get(iSpeaker)
						lstrSpeakers.append(strListBoxEntry )
					#produce a dropdown box
					speakerModelBox = ttk.Combobox(editElementDialog, width=20, textvariable=lValueVars[-1], values = lstrSpeakers )
					speakerModelBox.state(['readonly'])
					speakerModelBox.grid(column=1, row=gridRow)
				else:
					ttk.Label(editElementDialog, text=str(value)).grid(column=1, row=gridRow)
			else:
				ttk.Entry(editElementDialog, width=8, textvariable=lValueVars[-1] ).grid(column=1, row=gridRow)
				
				# add controls for optimization
				ttk.Entry(editElementDialog, width=12, textvariable=lOptIDVars[-1] ).grid(column=3, row=gridRow)
				ttk.Entry(editElementDialog, width=7, textvariable=lOptMinVars[-1] ).grid(column=4, row=gridRow)
				ttk.Entry(editElementDialog, width=7, textvariable=lOptMaxVars[-1] ).grid(column=5, row=gridRow)

			ttk.Label(editElementDialog, text=propUnit).grid(column=2, row=gridRow)
			
			gridRow += 1
		#add button to delete element
		def deleteMe():
			print("deleting ID", self.strID)
			acuCanvas.delete(g_dAcousticElements[self.strID].m_Frame)
			g_dAcousticElements.pop(self.strID)
			editElementDialog.destroy()
			acuCanvas.after(1,drawCanvasLines)

		tk.Button(editElementDialog, text="Delete", command=deleteMe).grid(row = gridRow, column = 0, sticky = tk.W)
		#add button to confirm
		def confirmMe():
			#save input data to dict
			bFailed = False

			for iProp in range(len(lValueVars)):
				propName, propUnit = g_dElements[strElementType][1 + iProp]
				
				#catch string properties
				if propUnit == "":
					g_dAcousticElements[self.strID].m_lValues[iProp] = lValueVars[iProp].get()
				else:
					#rest must be floats and this will be enforced
					try:
						fValue = float(lValueVars[iProp].get().replace(",","."))
						g_dAcousticElements[self.strID].m_lValues[iProp] = fValue
					except ValueError:
						#input was invalid, reset field
						lValueVars[iProp].set("0")
						bFailed = True
					
					strOptID = lOptIDVars[iProp].get()
					
					try:
						fMin = float(lOptMinVars[iProp].get().replace(",","."))
						fMax = float(lOptMaxVars[iProp].get().replace(",","."))
						g_dAcousticElements[self.strID].m_lValues[iProp] = fValue
					except ValueError:
						#input was invalid, reset field
						lOptMinVars[iProp].set("")
						lOptMaxVars[iProp].set("")

			if not bFailed:
				#check if parsing failed, in that case allow new input
				editElementDialog.destroy()

		tk.Button(editElementDialog, text="OK", command=confirmMe).grid(row = gridRow, column = 1, sticky = tk.E)
		#add button to cancel
		tk.Button(editElementDialog, text="Cancel", command=lambda:editElementDialog.destroy()).grid(row = gridRow, column = 2, sticky = tk.E)

		root.wait_window(editElementDialog)

#( (frame, button), (frame, button) )
g_lLinks = []
g_currStack = None
g_lastStack = None

def checkForConnection(ending):
	bPresent = False
	for (end1, end2) in g_lLinks:
		if end1 == ending or end2 == ending:
			bPresent = True
	return bPresent

def drawCanvasLines():
	#remove old ones
	#acuCanvas.deleteByTag("connectorLine")
	#lFoundItems = acuCanvas.find_withtag("connectorLine")
	#print("found by tag", lFoundItems)
	print("drawing lines")
	acuCanvas.delete("connectorLine")
	#add new ones
	for (end1, end2) in g_lLinks:
		(id1, button1) = end1
		(id2, button2) = end2

		#check if link is valid
		if id1 not in g_dAcousticElements or id2 not in g_dAcousticElements:
			#one of the ids doesn't exist, erase link.
			g_lLinks.remove( (end1, end2) )
		else:
			#get buttons of frames
			button1frame = g_dAcousticElements[id1].m_lButtons[button1]
			button2frame = g_dAcousticElements[id2].m_lButtons[button2]

			#get center points of buttons
			end1x = button1frame.winfo_rootx() + button1frame.winfo_width() // 2
			end1y = button1frame.winfo_rooty() + button1frame.winfo_height() // 2

			end2x = button2frame.winfo_rootx() + button2frame.winfo_width() // 2
			end2y = button2frame.winfo_rooty() + button2frame.winfo_height() // 2

			#draw line
			c1x, c1y, c2x, c2y = end1x - acuCanvas.winfo_rootx(), end1y - acuCanvas.winfo_rooty(), end2x - acuCanvas.winfo_rootx(), end2y - acuCanvas.winfo_rooty()

			acuCanvas.create_line(c1x, c1y, c2x, c2y, width=2.0, tags="connectorLine")

			#a little helper: if a cross section area field is '0' and the neighbor
			#has a value, set this field to the neighbors value
			#check datas on elements
			if g_dAcousticElements[id2].m_lValues[button2] != 0.0 and g_dAcousticElements[id1].m_lValues[button1] == 0.0:
				g_dAcousticElements[id1].m_lValues[button1] = g_dAcousticElements[id2].m_lValues[button2]

			if g_dAcousticElements[id1].m_lValues[button1] != 0.0 and g_dAcousticElements[id2].m_lValues[button2] == 0.0:
				g_dAcousticElements[id2].m_lValues[button2] = g_dAcousticElements[id1].m_lValues[button1]

	#mark currently selected connector button
	#first delete marking on last selected
	if g_lastStack != None:
		stackID, stackButton = g_lastStack
		buttonframe = g_dAcousticElements[stackID].m_lButtons[stackButton]
		buttonframe['bitmap'] = ""

	#then add marking on selected
	if g_currStack != None:
		stackID, stackButton = g_currStack
		buttonframe = g_dAcousticElements[stackID].m_lButtons[stackButton]
		buttonframe['bitmap'] = "@xbm/connector.xbm"

def linkElements(elementID, iButton):
	global g_currStack
	global g_lastStack
	currEnd = (elementID, iButton)
	bIsConnected = checkForConnection(currEnd)

	if g_currStack == None:
		#check if there already is a link
		if bIsConnected:
			for (end1, end2) in g_lLinks:
				if end1 == currEnd or end2 == currEnd:
					g_lLinks.remove( (end1, end2) )
		g_currStack = currEnd
	else:
		#check if you try to connect to itself
		stackID, stackButton = g_currStack
		print("stack id:", stackID, "element id:", elementID)
		if stackID == elementID:
			g_lastStack = g_currStack
			g_currStack = None

			#branch out
			return
		#check if that connection has already been made
		if not bIsConnected:
			g_lLinks.append( (currEnd, g_currStack) )
			g_lastStack = g_currStack
			g_currStack = None

	acuCanvas.after_idle(drawCanvasLines)

elemType = tk.StringVar()

#adds an element frame to the working area
def addElementToCanvas(*args):
	strElemType = elemType.get()
	print("element type is " + strElemType)

	#create element in global dictionary
	iTestID = 1
	strElemID = strElemType + "1"
	
	while strElemID in g_dAcousticElements:
		strElemID = strElemType + str(iTestID)
		iTestID += 1
		
	elementFrame = ttk.Frame(acuCircuitFrame)

	canvasID = acuCanvas.create_window(100, 100, window=elementFrame, tags="movable")

	strBitmapFile = "@xbm/" + elemType.get().lower() + "0.xbm"
	print(strBitmapFile)
	movingLabel = tk.Label(elementFrame, bitmap=strBitmapFile, text = elemType.get())
	movingLabel.grid(row = 1, column = 1)
	#tk.Button(elementFrame, bitmap="@xbm/connector.xbm", command=exit).grid(row = 1, column = 0)
	#add connection buttons
	buttons = []
	for iButton in range(len(g_dElements[elemType.get()][0])):
		gridRow, gridColumn = g_dElements[elemType.get()][0][iButton][0]

		button = tk.Button(elementFrame, text = str(iButton + 1), command=partial(linkElements, strElemID, iButton))

		button.grid(row = gridRow, column = gridColumn)
		buttons.append(button)

	myHandler = MovableHandler(movingLabel, strElemID)

	#add element to global dictionary
	#(strType, lValues, frame, lButtons):
	nValues = len(g_dElements[strElemType]) - 1
	
	print("adding element", strElemID)
	g_dAcousticElements[strElemID] = Element(strElemType, [0.0] *nValues, [""]*nValues, [""] *nValues, [""] *nValues, canvasID, buttons, myHandler)
	
	return strElemID

#callbacks for buttons
def addAcousticElement(*args):
	addElementDialog = tk.Toplevel(root)
	addElementDialog.transient(root)
	addElementDialog.grab_set()
	addElementDialog.wm_title("Add Acoustic Element")

	#create radio buttons for mode setting
	for iElementType in range(len(g_dElements.keys()) ):
		strElemType = list(g_dElements.keys())[iElementType]
		ttk.Radiobutton(addElementDialog, text=strElemType, variable=elemType, value=strElemType).grid(row = 1, column = iElementType)
		tk.Label(addElementDialog, bitmap="@xbm/" + strElemType.lower() + "0.xbm", text = strElemType).grid(row=0, column = iElementType)

	def okayCallback(*args):
		addElementToCanvas(args)
		addElementDialog.destroy()

	#add button to create element
	tk.Button(addElementDialog, text="OK", command=okayCallback).grid()
	#add button to cancel creation
	tk.Button(addElementDialog, text="Cancel", command=lambda:addElementDialog.destroy()).grid()

	root.wait_window(addElementDialog)

#create buttons
tk.Button(acuButtonFrame, bitmap="@xbm/add.xbm", command=addAcousticElement).grid(row=1, column=0)

#functions for import and export of simulation definitions
def loadDefinition(strFile):
	print("deleting old objects")
	if speakerListBox.size() > 0:
		speakerListBox.delete(0, speakerListBox.size())

	acuCanvas.delete("all")
	g_lLinks.clear()

	g_dAcousticElements.clear()
	
	g_dSpeakers.clear()
	
	print("loading from file", strFile ,"...")
	tree = ET.parse(strFile)
	root = tree.getroot()


	dx = root.get("dx")
	g_fDeltaX = float(dx)
	svSimuElementLength.set(str(g_fDeltaX) )

	#preliminary links
	#id1 -> (id2, button1)
	dLinks = dict()
	
	dRename = dict()

	for element in root:
		#check if this is speaker data
		if element.tag=="tspset":
			strSpeakerName = readSpeakerXML(element)
			
			print("inserting speaker", strSpeakerName, "to speaker list")
			speakerListBox.insert(tk.END, strSpeakerName)
			continue
	
		#get type of element
		#capitalize key
		strElementType = element.tag[0].upper() + element.tag[1:]
		
		#get id of element
		#strElementID = element.get("id")
		
		#create element on canvas
		elemType.set(strElementType)
		strElementID = addElementToCanvas()
		
		print("added element", element.get("id"), "as", strElementID)
		dRename[element.get("id")] = strElementID

		dLinks[strElementID] = []

		for prop in element:
			if prop.tag.find("neighbor")!= -1:
				#this is a neighbor tag, create a link.
				iLinkIndex = int(prop.tag[-1]) - 1
				strTargetID = prop.get("ref")

				#write preliminary link information
				dLinks[strElementID].append( (strTargetID, iLinkIndex) )
			elif prop.tag=="screen_position":
				#read screen position of frame and set position accordingly
				x,y = int(prop.get("x") ), int(prop.get("y"))
				acuCanvas.coords(g_dAcousticElements[strElementID].m_Frame, x, y)
			elif prop.tag=="screen_rotation":
				#read screen rotation of frame and set accordingly
				rot = int(prop.get("rot"))
				for i in range(rot):
					g_dAcousticElements[strElementID].m_MovableHandler.onRMBRelease(None)
			else:
				#find out visual name of property
				for iProp in range(len(g_dElements[strElementType]) - 1):
					propName, propUnit = g_dElements[strElementType][iProp + 1]
					
					#check against input
					if prop.tag == propName.lower().replace(" ", "_"):
						print("parsing property", propName, "[" + propUnit + "] =", prop.text)
						#read value of property
						#if this is a 'type' property, it will contain a string
						if propUnit != "":
							#no type, this must be a floating point value
							fProperty = float(prop.text)
							#write to property dictionary of element
							g_dAcousticElements[strElementID].m_lValues[ iProp ] = fProperty
							
							# check for optimizer settings
							if "id" in prop.attrib:
								g_dAcousticElements[strElementID].m_lOptID[ iProp ] = prop.attrib["id"]
								g_dAcousticElements[strElementID].m_lOptMin[ iProp ] = prop.attrib["min"]
								g_dAcousticElements[strElementID].m_lOptMax[ iProp ] = prop.attrib["max"]
						else:
							#write to properties
							g_dAcousticElements[strElementID].m_lValues[ iProp ] = prop.text
							
	# rename links
	dRenamedLinks = dict()
	for strID in dLinks.keys():
		print(dLinks[strID])
		dRenamedLinks[strID] = []
		for (strTargetID, iLinkIndex) in dLinks[strID]:
			print("strID", strID)
			print("strTargetID", strTargetID)
			dRenamedLinks[strID].append( (dRename[strTargetID], iLinkIndex) )
		
	#finalize links
	sFinished = set()
	for strID1 in dRenamedLinks:
		for (strID2, link1) in dRenamedLinks[strID1]:
			end1 = (strID1, link1)
			if end1 not in sFinished:
				#find other end of link
				for (strID1_1, link2) in dRenamedLinks[strID2]:
					if strID1_1 == strID1:
						end2 = (strID2, link2)
						g_lLinks.append( (end1, end2) )

						sFinished.add(end1)
						sFinished.add(end2)
	#update visuals
	acuCanvas.after_idle(drawCanvasLines)
	acuCanvas.after(100,drawCanvasLines)
	
	print("finished loading")

def saveDefinition(strFile):
	#parse new element length
	
	try:
		fValue = float(svSimuElementLength.get().replace(",","."))
		g_fDeltaX = fValue
	except ValueError:
		#input was invalid, reset field
		svSimuElementLength.set(str(g_fDeltaX) )

	print("element length", g_fDeltaX)
	
	
	print("writing to file", strFile ,"...")
	#create root element for output tree
	root = ET.Element("horn", dx = str(g_fDeltaX) )
	
	#add speakers
	for strSpeakerName in g_dSpeakers:
		#create xml data
		speakerElem = ET.SubElement(root, "tspset")
		writeSpeakerXML(strSpeakerName, speakerElem)

	#iterate existing elements
	for eleID in g_dAcousticElements:
		strType = g_dAcousticElements[eleID].m_Type

		#create element
		element = ET.SubElement(root, strType.lower().replace(" ", "_"), id = eleID)

		#find links for this element, add neighbor tags
		for (end1, end2) in g_lLinks:
			id1, port1 = end1
			id2, port2 = end2
			if id1 == eleID:
				ET.SubElement(element, "neighbor" + str(port1 + 1), ref = id2)
			if id2 == eleID:
				ET.SubElement(element, "neighbor" + str(port2 + 1), ref = id1)

		#extract element parameters
		for iProp in range(len(g_dElements[strType]) - 1):
			propName, propUnit = g_dElements[strType][1 + iProp]
			strValue = str(g_dAcousticElements[eleID].m_lValues[iProp])
			
			if g_dAcousticElements[eleID].m_lOptID[iProp] != "":
				ET.SubElement(element, propName.lower().replace(" ", "_"), id=g_dAcousticElements[eleID].m_lOptID[iProp], min=g_dAcousticElements[eleID].m_lOptMin[iProp], max=g_dAcousticElements[eleID].m_lOptMax[iProp]).text = strValue
			else:
				ET.SubElement(element, propName.lower().replace(" ", "_")).text = strValue

		#write screen coordinates of element
		frame = g_dAcousticElements[eleID].m_Frame

		(x1, y1) = acuCanvas.coords(frame)

		ET.SubElement(element, "screen_position", x = str(int(x1)), y= str(int(y1)))

		#write rotation state
		ET.SubElement(element, "screen_rotation", rot = str(g_dAcousticElements[eleID].m_iRotation))

	tree = ET.ElementTree(root)

	with open(strFile, 'wb') as f:
		f.write(bytes('<?xml version="1.0" encoding="UTF-8" ?><!DOCTYPE horn SYSTEM "../horn.dtd">', 'utf-8'))
		tree.write(f, 'utf-8')
	
	print("finished writing")

#create frame for mode simulation
simuFrame = ttk.Frame(mainFrame)

def parseColumns(hFile):
	points = []
	for line in hFile:
		numbers = line.split("\t")
		#garbage input -> terminate
		if len(numbers[0]) == 0:
			break
		aNumbers = []
		for number in numbers:
			aNumbers.append( float(number))

		points.append(aNumbers)
	return points

def rmsColumn(aData, iColumn):
	fSquares = 0
	for aLine in aData:
		fData = aLine[iColumn]
		fSquares += fData * fData
	return math.sqrt(fSquares / float(len(aData)) )

def cutRows(aData, fStart, fEnd):
	aOut = []
	for aLine in aData:
		if aLine[0] >= fStart  and aLine[0] <= fEnd:
			aOut.append(aLine)
	return aOut

#filenames for intermediate files

g_strFile = "current_simulation"
g_strDir = "../temp/"
g_strFilename = g_strDir + g_strFile
g_strXMLFile = g_strFilename + ".xml"
g_strElementListFile = g_strFile + ".txt"
g_strElementListFilename = g_strDir + g_strElementListFile

g_strImageFile = g_strFilename + ".png"
g_strResizedFile = g_strFilename + "_resized.png"

g_strSimuOutputFile = g_strFilename + ".out"
g_strSimuInputFile = g_strFilename + ".in"

g_strPlotFile = g_strFilename + "_plot.png"

g_strSimuCommand = "../bin/simu"


def generateElementList():
	#write xml file of setup
	saveDefinition(g_strXMLFile)

	#write element list
	call(["python3", "../tools/xml2list.py", g_strXMLFile, g_strElementListFilename])
	
	
	call(["python3", "../tools/list2img.py", g_strElementListFilename, g_strImageFile, str(simuImageCanvas.winfo_width()), str(simuImageCanvas.winfo_height()), "1"])

def escapeString(strToEscape):
	return "".join([c if c.isalnum() else '_' for c in strToEscape ])

svSimuElementLength = tk.StringVar()
svSimuElementLength.set(str(g_fDeltaX) )
svSimuMaxTimeStep = tk.StringVar()
svSimuMaxTimeStep.set("0.001")
svSimuStepResponse = tk.IntVar()
svSimuStepResponse.set(1)
svSimuMinFreq = tk.StringVar()
svSimuMinFreq.set("20")
svSimuMaxFreq = tk.StringVar()
svSimuMaxFreq.set("1000")
svSimuNumFreq = tk.StringVar()
svSimuNumFreq.set("256")

def onSimulationButtonClick():
	print("run simulation: generating element list")
	showSimuImage()
	
	print("run simulation: creating simulation configuration")
	config = configparser.ConfigParser()

	g_fMaxTimeStep = float(svSimuMaxTimeStep.get())

	config['general'] = {'element_file': g_strElementListFile,
						 'max_timestep': str(g_fMaxTimeStep),
						 'output_file' : g_strFile + ".out"}
	 
	# check if we are simulating a step response
	if(svSimuStepResponse.get() == 1):
		g_iSignalPeriods = 1
		g_fLeadTime = 0.0
		strFreqs = "20"
		strSignalType = "step"
		config['general']['mic_output'] = g_strFile + "_time_series"
	else:
		strSignalType = "sine"
		lfFreqs = numpy.logspace(numpy.log10(float(svSimuMinFreq.get())), numpy.log10(float(svSimuMaxFreq.get())), num=int(svSimuNumFreq.get()))
		strFreqs = ""
		for fFreq in lfFreqs:
			strFreqs += str(fFreq) + "; "
		g_iSignalPeriods = 8
		g_fLeadTime = 0.1
	config['signal'] = {'signal_type': strSignalType,
						'frequencies': strFreqs,
						'signal_periods': str(g_iSignalPeriods),
						'lead_time': str(g_fLeadTime)}
	dSpeakerFileMapping = dict()
	for iSpeaker in range(speakerListBox.size()):
		strSpeakerName = speakerListBox.get(iSpeaker)
		strSpeakerFile = escapeString(strSpeakerName) + ".cfg"
	
		strSpeakerFilename = g_strDir + strSpeakerFile
	
		dSpeakerFileMapping[escapeString(strSpeakerName)] = strSpeakerFile
		#create xml data
		xmlTree = ET.ElementTree(ET.Element("tspset") )
		rootElem = xmlTree.getroot()
		writeSpeakerXML(strSpeakerName, rootElem)
		speakerConfig = configparser.ConfigParser()
		dSpeakerProps = dict()
		for prop in rootElem:
			dSpeakerProps[prop.tag] = prop.text
	
		speakerConfig['tspset'] = dSpeakerProps
	
		with open(strSpeakerFilename, 'w') as speakerFile:
			speakerConfig.write(speakerFile)
	
	config['speakers'] = dSpeakerFileMapping
	#open simulation input file for writing

	print("run simulation: writing simulation input file")
	strSimuInput = g_strSimuInputFile
	with open(strSimuInput, 'w') as configfile:
		config.write(configfile)
		
	#call(["python3", "../tools/run_simulation.py", strSimuInput, g_strPlotFile, "python3", "../tools/lightsim.py", "1"])
	call(["python3", "../tools/run_simulation.py", strSimuInput, g_strPlotFile, "../simu/Release/simu"])

simuSettingsFrame = ttk.Frame(simuFrame)
simuSettingsFrame.pack()

ttk.Label(simuSettingsFrame, text="element length").grid(row=1, column=1, padx=5)
ttk.Entry(simuSettingsFrame, width=8, textvariable=svSimuElementLength).grid(row=2, column=1)

ttk.Label(simuSettingsFrame, text="max time step").grid(row=1, column=2, padx=5)
ttk.Entry(simuSettingsFrame, width=8, textvariable=svSimuMaxTimeStep).grid(row=2, column=2)

ttk.Label(simuSettingsFrame, text="step response").grid(row=1, column=3, padx=5)
ttk.Checkbutton(simuSettingsFrame, variable=svSimuStepResponse).grid(row=2, column=3, padx=5)

ttk.Label(simuSettingsFrame, text="min frequency").grid(row=3, column=1, padx=5)
ttk.Entry(simuSettingsFrame, width=8, textvariable=svSimuMinFreq).grid(row=4, column=1)

ttk.Label(simuSettingsFrame, text="max frequency").grid(row=3, column=2, padx=5)
ttk.Entry(simuSettingsFrame, width=8, textvariable=svSimuMaxFreq).grid(row=4, column=2)

ttk.Label(simuSettingsFrame, text="number of frequencies").grid(row=3, column=3, padx=5)
ttk.Entry(simuSettingsFrame, width=8, textvariable=svSimuNumFreq).grid(row=4, column=3)

ttk.Button(simuFrame, text="Run Simulation", command=onSimulationButtonClick).pack()

simuImageCanvas = tk.Label(simuFrame)
#simuImageCanvas.grid(sticky = tk.N+tk.S+tk.W+tk.E)

simuImageCanvas.pack(expand=1, fill=tk.BOTH)

def showSimuImage():
	generateElementList()
	
	print("loading image", g_strImageFile)
	
	imageSimu = Image.open(g_strImageFile)
	
	fImageAspectRatio = 1
	
	canvasWidth = simuImageCanvas.winfo_width()
	canvasHeight = simuImageCanvas.winfo_height()
	
	fCanvasAspectRatio = 1
	
	#scale according to aspect ratio
		
	print("labelWidth", canvasWidth, "labelHeight", canvasHeight)
	
	resizedSimu = imageSimu.resize(size = (canvasWidth, canvasHeight) )
	resizedSimu.save(g_strResizedFile)
	
	#tkpi = tk.PhotoImage( image = resizedSimu)
	tkpi = tk.PhotoImage( file = g_strResizedFile)
	
	simuImageCanvas.image = tkpi
	simuImageCanvas.configure(image=tkpi)
	

#create frame for mode results
resultsFrame = ttk.Frame(mainFrame)
choiceLabel = ttk.Label(resultsFrame, text='xxx dB')
choiceLabel.grid()

dModeFrames = {'Speakers': speakerFrame, 'Acoustic Circuit': acuCircuitFrame, 'Simulation': simuFrame, 'Results': resultsFrame}

def onChangeMode(*args):
	#hide all other frames, show selected
	for subFrame in dModeFrames.values():
		subFrame.grid_remove()

	dModeFrames[mode.get()].grid(sticky = tk.N+tk.E+tk.S+tk.W)
	
	#update circuit diagram
	if mode.get() == 'Acoustic Circuit':
		acuCanvas.after(100, drawCanvasLines)
	
	#update image of simulation
	if mode.get() == 'Simulation':
		acuCanvas.after(100, showSimuImage)

#initialize to speaker mode
mode.trace("w", onChangeMode)
mode.set(lModes[0])

#start the whole thing
root.mainloop()
