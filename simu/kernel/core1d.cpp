#include "core1d.h"

#include <iostream> //for putting v, can be removed










int f1DStartCalculation(f1DCalculationContainer* field, float* buffer,  int parameter)
{
	static bool start=true;

	float VolumeFlow=0; //needed in elements p-calculation loop

	float high1=10;
	float high2=10;
	float t1=0;
	float t2=0;
	bool start1=false;
	bool found1=false;
	bool start2=false;
	bool found2=false;



	for (unsigned int i=0; i< field->info->numberTimesteps;i++) //calculation timeintegration main loop
	{
		for (unsigned int j=0;j <field->connectors.size();j++) // calculate new velocitys
		{
			field->connectors[j].velocity =field->connectors[j].velocity*(1-field->connectors[j].damping*field->info->dt)+
				field->connectors[j].vfactor*(field->connectors[j].negativeNeighbour->pressure-field->connectors[j].positiveNeighbour->pressure);
			


		}// calculate new velocitys

		for (unsigned int j=0;j <field[0].speakers.size();j++) // calculate new velocitys for speakers
		{
			field->speakers[j].position->velocity=field->speakers[j].f(field->info->dt, //timestep
																field->speakers[j], //speakerinfo
																500,  //old velocity
																start);
			
		}// calculate new velocitys for speakers

		for (unsigned int k=0; k<field->openElements.size();k++)// calculate new velocitys for the open ends
		{  //first v-element is connected to a normal element
			field->openElements[k].vField[0]= field->info->OpenElementsDamping*(field->openElements[k].vField[0]+
				field->openElements[k].vFactorField[0]*(field->openElements[k].element.pressure - field->openElements[k].pField[0]));

			for (unsigned int j=1;j <field->openElements[k].vFactorField.size();j++) // calculate new velocitys for a open end
			{
				field->openElements[k].vField[j]= field->info->OpenElementsDamping*(field->openElements[k].vField[j]+
					field->openElements[k].vFactorField[j]*(field->openElements[k].pField[j-1]- field->openElements[k].pField[j]));						
			}// calculate new velocitys for a open end
		}// calculate new velocitys for all open ends

		for (unsigned int j=0;j <field->elements.size();j++) // calculate new pressure for elements
		{
			VolumeFlow=0;

			for (unsigned int k=0;k<field->elements[j].negativeNeighbours.size();k++){ //sum up volumeflow from negative neighbours
				VolumeFlow+=field->elements[j].negativeNeighbours[k]->crossSectionArea*field->elements[j].negativeDirections[k]*field->elements[j].negativeNeighbours[k]->velocity;
			}

			for (unsigned int k=0;k<field->elements[j].positiveNeighbours.size();k++){//volumeflow from positive neighbours is substractet v1=v0+f(p0-p1)
				VolumeFlow-=field->elements[j].positiveNeighbours[k]->crossSectionArea*field->elements[j].positiveDirections[k]*field->elements[j].positiveNeighbours[k]->velocity;
			}

			field->elements[j].pressure= (field->elements[j].pressure+field->elements[j].pFactor*VolumeFlow);//calculate new p

			
		} // calculate new pressure for elements

		for (unsigned int k=0; k<field->openElements.size();k++)// calculate new pressures for the open ends
		{
			for (unsigned int j=0;j <field->openElements[k].pField.size()-1;j++) // calculate new pressures for a open end
			{
				field->openElements[k].pField[j]= field->info->OpenElementsDamping*(field->openElements[k].pField[j]+field->openElements[k].pFactorField[j]*(field->openElements[k].vField[j]*field->openElements[k].aField[j]-field->openElements[k].vField[j+1]*field->openElements[k].aField[j+1]));
				
			}// calculate new pressures for a open end

			//calculate pressure at element connection
			field->openElements[k].element.pressure= field->info->OpenElementsDamping*(field->openElements[k].element.pressure+field->openElements[k].element.pFactor*
				(field->openElements[k].connector->velocity *field->openElements[k].connector->crossSectionArea*field->openElements[k].direction)
				-field->openElements[k].vField[0]*field->openElements[k].aField[0]);	
			}// calculate new pressures for all open ends

		for (unsigned int j=0;j <field->microphones.size();j++) // store microphonevalues in memory
		{
			field->microphones[i].putValue(field->microphones[i].refE->pressure);
		} // store microphonevalues in memory



	for (unsigned int j=0; j<field->elements.size();j++)
	{
		buffer[j+field->elements.size()*i]=field->elements[j].pressure;
	}
	
	//velocity test, can be removed later 
	//only valid in a tube with constant cross section area around id 80-70 
	//space to reflectors needed

	if ((field->elements[80].pressure<=high1)){
		high1=field->elements[80].pressure;
		start1=true;
	}
	else {
		if ((!found1)&&start1){
			t1=i*field->info->dt;
			found1=true;
		}
	}
	if ((field->elements[70].pressure<=high2)){
		high2=field->elements[70].pressure;
		start2=true;
	}
	else {
		if ((!found2)&&start2){
			t2=i*field->info->dt;
			found2=true;
			std::cout<<"v= "<<(field->dx*(80.0f-70.0f)/(t2-t1));
			std::cout<<std::endl;
		}
	}
	start=false;
	}//calculation timeintegration main loop


	return 1;//Calculation succesfull
}
