'''
a tk gui to specify the geometry of a horn speaker
saves projects in xml format
will create an input file for simulation (element definition) 
'''

from tkinter import *
from tkinter import ttk

root = Tk()
root.title("Feet to Meters")

sectionFrame = ttk.Frame(root)
sectionFrame.grid()

#list of all elements availiable to the user
dPropTypes = dict(Boolean = 0, Integer = 1, Float = 2)

#areas set to 0 will try to evaluate their values by their neighbors

dElements = dict(
                conical = [('length', dPropTypes['Float'], 'm'),
                            ('A1', dPropTypes['Float'], 'm^2'),
                            ('A2', dPropTypes['Float'], 'm^2')],
                
                expo = [('length', dPropTypes['Float'], 'm'),
                        ('A1', dPropTypes['Float'], 'm^2'),
                        ('A2', dPropTypes['Float'], 'm^2'),
                        ('exponent', dPropTypes['Float'], '1')],
                 
                wall = [('damping thickness', dPropTypes['Float'], 'm'),
                        ('damping constant', dPropTypes['Float'], '1')],
                 
                mouth = [('space', dPropTypes['Float'], '1')],
                
                speaker = [('induction', dPropTypes['Float'], 'T')],
                
                fork = [('A1', dPropTypes['Float'], 'm^2'),
                        ('A2', dPropTypes['Float'], 'm^2'),
                        ('A3', dPropTypes['Float'], 'm^2')]
                )

typeSelectionFrame = ttk.Frame(sectionFrame)
typeSelectionFrame['borderwidth'] = 2
typeSelectionFrame['relief'] = 'solid'
typeSelectionFrame.grid()

ttk.Label(typeSelectionFrame, text="section type").grid()

sectionType = StringVar()

#create radio buttons for the simulation elements

for key in dElements.keys():
    ttk.Radiobutton(typeSelectionFrame, text=key, variable=sectionType, value=key).grid()

propertiesFrame = ttk.Frame(sectionFrame)
propertiesFrame['borderwidth'] = 2
propertiesFrame['relief'] = 'solid'
propertiesFrame.grid()

choiceLabel = ttk.Label(propertiesFrame, text='none')
choiceLabel.grid()

#create property frames for all possible element types, but don't show them
dPropertyFrames = dict();

for key in dElements.keys():
    dPropertyFrames[key] = ttk.Frame(propertiesFrame)
    
    #################################
    gridRow = 0;
    
    for props in dElements[key]:
        (propDesc, propType, propUnit) = props;
        ttk.Label(dPropertyFrames[key], text=propDesc).grid(column=0, row=gridRow)
        if propType == dPropTypes['Float']:
            ttk.Entry(dPropertyFrames[key], width=8).grid(column=1, row=gridRow)
        
        ttk.Label(dPropertyFrames[key], text=propUnit).grid(column=2, row=gridRow)
        
        gridRow = gridRow+1;
        

def onChangeType(*args):
    choiceLabel['text'] = sectionType.get() + ' properties';
    
    #hide all other frames, show selected
    for subFrame in dPropertyFrames.values():
        subFrame.grid_remove()
    
    dPropertyFrames[sectionType.get()].grid()

sectionType.trace("w", onChangeType)


ttk.Button(sectionFrame, text="Ok", command=exit).grid()



root.mainloop()
