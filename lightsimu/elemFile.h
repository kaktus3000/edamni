/*
 * elemFile.h
 *
 *  Created on: Nov 10, 2016
 *      Author: ben
 */

#ifndef ELEMFILE_H_
#define ELEMFILE_H_


typedef struct
{
	// velocity damping
    float m_fDamping;
    // cross-section area
    float m_fArea;
    // no connection to prior element?
    uint m_bBreak;
    // part of horn geometry?
    uint m_bGeometry;

    float m_fInfiniteDamping;

    // link syntax:
    //   -1: no link
    //   0: link to "infinity"
    //   >0: link to actual element
    uint m_iLink;

    // speaker will be inserted on the velocity link to the previous pressure element
    char* m_strSpeaker;

    // microphone definition. measures pressure of this pressure element
    char* m_strMic;
} SElement;

float scanElemFile(const char* strFilename, SElement** ppElems, uint* pnElems);
void getComponents(const SElement* aElems, uint nElems, uint** ppSpeakers, uint* pnSpeakers, uint** ppMics, uint* pnMics);


#endif /* ELEMFILE_H_ */
