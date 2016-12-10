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
    float m_fDamping;
    float m_fArea;
    uint m_bBreak;
    uint m_bGeometry;

    // link syntax:
    //   -1: no link
    //   0: link to "infinity"
    //   >0: link to actual element
    uint m_iLink;

    // speaker will be inserted on the velocity link to the previous pressure element
    char* m_strSpeaker;

    // microphone definition. measures pressure of this pressure element
    char* m_strMic;
} Elem;

float scanElemFile(const char* strFilename, Elem** ppElems, uint* pnElems);
void getComponents(const Elem* aElems, uint nElems, uint** ppSpeakers, uint* pnSpeakers, uint** ppMics, uint* pnMics);


#endif /* ELEMFILE_H_ */
