#!/usr/python3

# optimize horn geometry with regard to objective function

#define initial step widths
#define minimum step widths by practical tolerances
g_fMinLenStep = 0.005
g_fMinCrossSectionChange = 0.05

#optimization loop

#if we don't make any progress, reduce step widths
#if we reached minimum step width

#line search for one parameter

#try moving it up first

#then try moving it down

#define new geometry

#check for constant cross section in fork elements
#A1 = A2 + A3

#check for neighboring cross-sections
#usually we don't want hard steps at the element borders


#check if we already have a similar design in our cache
#if we do, discard this design and try something different



#check constraints by looking at generated element list

#check for maximum cost

#check for maximum length

#check for maximum volume

#run simulation

#calculate objective (cost) function for output

#calculate optimal fit of linear response

#calculate cost for linearity
#calculate cost for edge frequency


