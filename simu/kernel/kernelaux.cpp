#include "kernelaux.h"
#include <math.h>

//struct connectionBuffer;
//dummy auxilary data types for parsing

int useDefaultDescriptor(f1DCalculationDescriptor* desc){
	if (!desc) return BAD_POINTER;
	desc->density=static_cast<float>(DENSITY);
	desc->gasconstant=static_cast<float>(GASCONSTANT);
	desc->temperature=static_cast<float>(TEMPERATURE);
	desc->numberTimesteps=DEFAULT_TIME_STEPS;
	desc->OpenElementsDamping=static_cast<float>(OPEN_ELEMENT_DAMPING); //To do : has to be calculated from timestep
	desc->OpenEndElements=DEFAULT_NUM_OPEN_ELEMENTS;
	desc->OpenEndLength=0;
	desc->dt=0;
	return NO_ERR;
}

int fullfillDescriptor(f1DCalculationContainer* container){ //calculate dt and damping from dx
	if (container->dx<=0.0f) return FATAL_ERROR;
	container->info->dt=0.999f*container->dx/(float)sqrt(container->info->gasconstant*container->info->temperature);
	container->info->OpenEndLength=container->dx*container->info->OpenEndElements;
	container->info->OpenElementsDamping=static_cast<float>(OPEN_ELEMENT_DAMPING); //To do : has to be calculated from timestep
	return NO_ERR;
}



struct microphoneParser{//struct for buffer unparsed connection data
	int line;
	int ID;//p-element ID
	int ref;//crosssection area
};

struct speakerParser{//struct for buffer unparsed connection data
	int line;
	int ID;//speaker-element ID
	int ref1;//p-element ID
	float area1;//crosssection area
	int ref2;//p-element ID
	float area2;//crosssection area
};

struct connection{ //struct for buffer unparsed connection data
	int line;
	int negref; //p-element ID
	int posref;//p-element ID
	float area; //crosssection area
};

struct connectionParser{ //struct for buffer unparsed connection data for the elements
	int line;
	std::vector<connection>  negconnectionBuffer; 
	std::vector<connection> posconnectionBuffer;
};

//auxilary functions for load1DKernelIpnut
//return a pointer to the p-element with ID =ref
f1DElement* getNeighbourPointer(int ref,std::vector<f1DElement> &elements)
{
	for (unsigned int i=0;i<elements.size();i++){ //look if ref= element .ID for all elements
		if (elements[i].ID==ref)
			return &elements[i];
	}
	return nullptr;//element was not found, so it does not exist and nullptr is returned
}

bool existsEID(int ref,std::vector<f1DElement> &elements)
{
	if (!getNeighbourPointer(ref, elements)) return false;
	return true;
}

bool existsMID(int ref,std::vector<microphoneParser> &unparsedMicrophones)
{
	for (unsigned int i=0;i<unparsedMicrophones.size();i++){ //look if ref= element .ID for all elements
		if (unparsedMicrophones[i].ID==ref)
			return true;
	}
	return false;
}




//read file stream and create raw-p-elements and store the rest to the buffers
int storeFileToBuffers(f1DCalculationContainer* container, 
						std::ifstream &file, 
						std::vector<connectionParser>  &unparsedConnections,
						std::vector<speakerParser> &unparsedSpeakers,
						std::vector<microphoneParser> &unparsedMicrophones){

	speakerParser umparsedSpeakerDummy; //dummy for create a new buffer element via std::vector.pushback()
	connectionParser unparsedCContainerDummy;//dummy for create a new buffer element via std::vector.pushback()
	connection unparsedConnectionDummy;//dummy for create a new buffer element via std::vector.pushback()
	microphoneParser unparsedMicrophoneDummy;//dummy for create a new buffer element via std::vector.pushback()

	f1DElement bufferElement;
	//f1DSpeaker speakerBuffer;
	//f1DMicrophone microphoneBuffer;
	//f1DConnector connectorBuffer;
	bool elementInProgress=false;
	int LineInFile=0; //Gives the current Linenumber for debugging reason


	std::string buffer; //to read lines from filestream
	std::istringstream parsingBuffer; //To get easy access to typconverting during parsinsg the string buffer

	std::cout<<"Start scanning file..."<<std::endl;	

	if(!std::getline(file,buffer)){
		std::cout<<"File is Empty!"<<std::endl;
		return FILE_IS_EMPTY;
	}
	LineInFile++;
	parsingBuffer.str(buffer);

	std::string elementLabelDummy;
	float dx;

	//Read and check file header dx <dx>
	parsingBuffer>>elementLabelDummy;
	if (parsingBuffer.fail()){ //und testen
        std::perror("Error while reading file!");
		std::cout<<"Label <dx> expected @Line: "<<LineInFile<<std::endl;
		return CORRUPTED_FILE;
	}

	if (elementLabelDummy!="dx") {
		std::cout<<"Unexpected File Found"<<std::endl;
		return UNEXPECTED_FILE;
	}

	parsingBuffer>>dx;
	if (parsingBuffer.fail()){ //und testen
        std::perror("Error while reading file!");
		std::cout<<"Element size <dx> expected @Line: "<<LineInFile<<std::endl;
		return CORRUPTED_FILE;
	}



	container->dx=dx;
	std::cout<<"Elementsize: "<<container[0].dx<<std::endl;	
	buffer.clear();
	parsingBuffer.clear();
	 

	//read a line from filestream and parse ist
	while (std::getline(file,buffer))
	{	
		LineInFile++;
		if (!buffer.size()){ 
			std::cout<<"FATAL_ERROR: Buffer could not be read @Line: "<<LineInFile<<std::endl;
			return CORRUPTED_FILE;
		}
		parsingBuffer.str(buffer);
		switch(buffer[0])
		{
			case 'e'://normal element
				elementInProgress=true; // now the parser entered an element block
				bufferElement.ID=container->elements.size();
				parsingBuffer>>elementLabelDummy; //remove e from buffer
				if (parsingBuffer.fail()){ //Test if it was succesfully
					std::cout<<"Corrupted Element. Element Label <e> expected @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE;
				}
				parsingBuffer>>bufferElement.ID; //read id
				if (parsingBuffer.fail()){ //check it
					std::cout<<"Corrupted Element. Element ID expected @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE;
				}
				if (bufferElement.ID<1){ //ID must be >= 1
					std::cout<<"Error: Reserved Element-ID used: "<<bufferElement.ID<<" @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE;
				}
				if (existsEID(bufferElement.ID,container->elements)){ //check if it is a unique element id
					std::cout<<"Error: Element-ID: "<<bufferElement.ID<<" is already used! @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE;
				}
				bufferElement.damping=1.0;//initalize a new buffer element
				bufferElement.pFactor=0;
				bufferElement.pressure=0;
				bufferElement.negativeNeighbours.clear();
				bufferElement.positiveNeighbours.clear();
				unparsedCContainerDummy.negconnectionBuffer.clear();
				unparsedCContainerDummy.posconnectionBuffer.clear();
				unparsedCContainerDummy.line=LineInFile;
				unparsedConnections.push_back(unparsedCContainerDummy);//create a raw connection container for the element
				container->elements.push_back(bufferElement); //create new element
				break;

			case 's'://speaker element found
				elementInProgress=false;// parser left element block
				parsingBuffer>>elementLabelDummy; //s" aus buffer entfernen
				if (parsingBuffer.fail()){ //und testen
					std::cout<<"Corrupted Element. Element label <s> expected @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE;
				}

				umparsedSpeakerDummy.ID=unparsedSpeakers.size();// give it a ID

				int ref1;
				float area1;
				float area2;
				int ref2;
				bool positiveSide;
				positiveSide=false;
				bool negativeSide;
				negativeSide=false;
				//clear buffer to read a new line
				buffer.clear();
				parsingBuffer.clear();
				if (!getline(file,buffer)){ //check if reading was succesful
					std::cout<<"Corrupted Speaker-Element. <+/-> <ref> <area> expeceted @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE_AT_SPEAKER;
				}
				LineInFile++;
				parsingBuffer.str(buffer);

				parsingBuffer>>elementLabelDummy;
				if (parsingBuffer.fail()){ //and check
					std::cout<<"Corrupted Speaker-Element. Element label <+>/<-> expected @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE;
				}

				//parse new line 
				if (elementLabelDummy== "+"){ //+ connection found
					parsingBuffer>>ref2; 
					if (parsingBuffer.fail()){ //und testen
						std::cout<<"Corrupted Speaker-Element. Element  <ref> expected @Line: "<<LineInFile<<std::endl;
						return CORRUPTED_FILE;
					}
					parsingBuffer>>area2; 
					if (parsingBuffer.fail()){ //und testen
						std::cout<<"Corrupted Speaker-Element. Element  <area> expected @Line: "<<LineInFile<<std::endl;
						return CORRUPTED_FILE;
					}
					positiveSide=true;
				}else if (elementLabelDummy== "-"){ //- connection found
					parsingBuffer>>ref1; 
					if (parsingBuffer.fail()){ //und testen
						std::cout<<"Corrupted Speaker-Element. Element  <ref> expected @Line: "<<LineInFile<<std::endl;
						return CORRUPTED_FILE;
					}
					parsingBuffer>>area1; 
					if (parsingBuffer.fail()){ //und testen
						std::cout<<"Corrupted Speaker-Element. Element  <area> expected @Line: "<<LineInFile<<std::endl;
						return CORRUPTED_FILE;
					}
					negativeSide=true;
				} else {
					std::cout<<"Corrupted Speaker-Element; Element <+/-> expected @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE_AT_SPEAKER;
				}

				// read a new line and check it as above 
				buffer.clear();
				parsingBuffer.clear();
				if (!getline(file,buffer)){//read right connection
					std::cout<<"Corrupted Speaker-Element @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE_AT_SPEAKER;
				}
				LineInFile++;
				parsingBuffer.str(buffer);
				parsingBuffer>>elementLabelDummy;
				if (parsingBuffer.fail()){ //und testen
					std::cout<<"Corrupted Speaker-Element. Element label <+>/<-> expected @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE;
				}

				if (elementLabelDummy== "+"){
					parsingBuffer>>ref2; 
					if (parsingBuffer.fail()){ //und testen
						std::cout<<"Corrupted Speaker-Element. Element  <ref> expected @Line: "<<LineInFile<<std::endl;
						return CORRUPTED_FILE;
					}
					parsingBuffer>>area2; 
					if (parsingBuffer.fail()){ //und testen
						std::cout<<"Corrupted Speaker-Element. Element  <area> expected @Line: "<<LineInFile<<std::endl;
						return CORRUPTED_FILE;
					}
					positiveSide=true;
				}else if (elementLabelDummy== "-"){
					parsingBuffer>>ref1; 
					if (parsingBuffer.fail()){ //und testen
						std::cout<<"Corrupted Speaker-Element. Element  <ref> expected @Line: "<<LineInFile<<std::endl;
						return CORRUPTED_FILE;
					}
					parsingBuffer>>area1; 
					if (parsingBuffer.fail()){ //und testen
						std::cout<<"Corrupted Speaker-Element. Element  <area> expected @Line: "<<LineInFile<<std::endl;
						return CORRUPTED_FILE;
					}
					negativeSide=true;
				} else {
					std::cout<<"Corrupted Speaker-Element; Element <+/-> expected"<<" @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE_AT_SPEAKER;
				}


				//there must be a + and a- connection for a correct speaker element
				if (!(positiveSide)){ 
					std::cout<<"Corrupted Speaker-Element. No <+> <ref> <area>"<<" @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE_AT_SPEAKER;
				}

				if (!(negativeSide)){ 
					std::cout<<"Corrupted Speaker-Element. No <-> <ref> <area>"<<" @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE_AT_SPEAKER;
				}
				if (area1<=0){ 
					std::cout<<"Corrupted Speaker-Element. Area must be greater than zero @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE_AT_SPEAKER;
				}
				if (area2<=0){ 
					std::cout<<"Corrupted Speaker-Element. Area must be greater than zero @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE_AT_SPEAKER;
				}
				if (ref1<=0){ 
					std::cout<<"Corrupted Speaker-Element. Reference for a speaker must be greater than 0 @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE_AT_SPEAKER;
				}
				if (ref2<=0){ 
					std::cout<<"Corrupted Speaker-Element. Reference for a speaker must be greater than 0 @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE_AT_SPEAKER;
				}
				// initialize a dummyspeaker
				umparsedSpeakerDummy.line=LineInFile;
				umparsedSpeakerDummy.area1=area1;
				umparsedSpeakerDummy.area2=area2;
				umparsedSpeakerDummy.ref1=ref1;
				umparsedSpeakerDummy.ref2=ref2;
				unparsedSpeakers.push_back(umparsedSpeakerDummy); //create a raw-speaker

				break;

			case 'm'://microphone found
				elementInProgress=false; //parser left elementblock
				unparsedMicrophoneDummy.line=LineInFile;

				parsingBuffer>>elementLabelDummy; //remove m from buffer
				if (parsingBuffer.fail()){ //und testen
					std::cout<<"Corrupted microphone-element. Element label <m> expected @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE;
				}

				parsingBuffer>>unparsedMicrophoneDummy.ID; //give it a ID
				if (parsingBuffer.fail()){ //und testen
					std::cout<<"Corrupted microphone-element. microphone <ID> expected @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE;
				}
				if (unparsedMicrophoneDummy.ID<0){
					std::cout<<"Error: Microphone reference, ID: "<<unparsedMicrophoneDummy.ID<<" must be greater than zero @Line: "<<LineInFile<<std::endl;
					return FATAL_ERROR;
				}

				if (existsMID(unparsedMicrophoneDummy.ID,unparsedMicrophones)){
					std::cout<<"Error: Microphone ID: "<<unparsedMicrophoneDummy.ID<<" exists already! @Line: "<<LineInFile<<std::endl;
					return FATAL_ERROR;
				}
				//read the p-element reference
				parsingBuffer>>unparsedMicrophoneDummy.ref;
				if (parsingBuffer.fail()){ //und testen
					std::cout<<"Corrupted microphone-element. Element <ref> expected @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE;
				}
				unparsedMicrophones.push_back(unparsedMicrophoneDummy); //create a raw microphone
				break;

			case '+':// + connection found
				if (!elementInProgress) { //only valid if it is an element-block
					std::cout<<"Corrupted File-Format; Element Descriptor <e> expected! @Line:" <<LineInFile<<std::endl;
					return ELEMENT_EXPECTED;
				}
				parsingBuffer>>elementLabelDummy; //remove + from buffer
				if (parsingBuffer.fail()){ //und testen
					std::cout<<"Corrupted connector. Element label <+> expected @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE;
				}
				parsingBuffer>>unparsedConnectionDummy.posref;
				if (parsingBuffer.fail()){ //read reference to p-element
					std::cout<<"Corrupted connector-element. Element <ref> expected @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE;
				}

				parsingBuffer>>unparsedConnectionDummy.area;//read cross section area
				if (parsingBuffer.fail()){ //und testen
					std::cout<<"Corrupted connector-element. Element <area> expected @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE;
				}
				if (unparsedConnectionDummy.area<=0){ 
					std::cout<<"Corrupted Element. Area must be greater than zero! @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE_AT_SPEAKER;
				}

				//create a raw-connection
				unparsedConnectionDummy.negref=container->elements[container->elements.size()-1].ID;
				unparsedConnectionDummy.line=LineInFile;
				unparsedConnections[unparsedConnections.size()-1].posconnectionBuffer.push_back(unparsedConnectionDummy);

				break;
				// - connection found, same procedure as for + connection
			case '-':
				if (!elementInProgress) {
					std::cout<<"Corrupted File-Format; Element Descriptor <e> expected! @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE;
				}
				parsingBuffer>>elementLabelDummy; //s" aus buffer entfernen
				if (parsingBuffer.fail()){ //und testen
					std::cout<<"Corrupted microphone-element. Element label <-> expected @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE;
				}
				parsingBuffer>>unparsedConnectionDummy.negref;
				if (parsingBuffer.fail()){ //und testen
					std::cout<<"Corrupted connector-element. Element <ref> expected @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE;
				}

				parsingBuffer>>unparsedConnectionDummy.area;
				if (parsingBuffer.fail()){ //und testen
					std::cout<<"Corrupted connector-element. Element <area> expected @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE;
				}
				if (unparsedConnectionDummy.area<=0){ 
					std::cout<<"Corrupted Element. Area must be greater than zero! @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE_AT_SPEAKER;
				}
				unparsedConnectionDummy.posref=container->elements[container->elements.size()-1].ID; //give it a ID
				unparsedConnectionDummy.line=LineInFile;//store line in file for debugging
				unparsedConnections[unparsedConnections.size()-1].negconnectionBuffer.push_back(unparsedConnectionDummy);

				break;
			case 'd': //damping constant found
				if (!elementInProgress) { //only valid in an elementblock
					std::cout<<"Corrupted File-Format; Element Descriptor <e> expected @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE;
				}
				elementInProgress= false; // element block is completed with a damping constant
				parsingBuffer>>elementLabelDummy; //read label "d" from buffer
				if (parsingBuffer.fail()){ //und testen
					std::cout<<"Corrupted connector-element. Element <d> expected @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE;
				}
				float damping; //dummy to store damping
				parsingBuffer>>damping;
				if (parsingBuffer.fail()){ //read damping and check it
					std::cout<<"Corrupted connector-element. Element <value> expected @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_FILE;
				}
				if (damping<0.0)//damping must be >=0
				{
					std::cout<<"Corrupted File-Format; Damping constant must be >=0, in element: "<<container->elements[container->elements.size()-1].ID<<" @Line: "<<LineInFile<<std::endl;
					return CORRUPTED_DAMPING_CONSTANT;
				}
				container->elements[container->elements.size()-1].damping=1.0f/(1.0f+damping); //store the damping constant for the current element
				break;

			default:{ //something unkown was found
						if (elementInProgress){
							std::cout<<"Corrupted File. <+>/<-> expected but found: "<<buffer[0]<<" @Line: "<<LineInFile<<std::endl;
							return CORRUPTED_FILE;
						}
						std::cout<<"Corrupted File @Line: "<<LineInFile<<std::endl;
						return CORRUPTED_FILE;
					}
		}
	
	//clear the buffers to read a new line
	buffer.clear();
	parsingBuffer.clear();

	} // read elements, speakers and microphones in memory
	if (file.bad()) //check why the while loop was terminated
       std::perror("Error while reading file!" );
	return NO_ERR;
}

//checks if a raw-connection already exists as an v-element
bool IsRedundantConnection(f1DConnector& connector,std::vector<f1DConnector> &Connections)
{
	for (unsigned int i=0; i<Connections.size();i++){//For each element look up if neighbour IDs are identical
		if ((connector.negativeNeighbour==Connections[i].negativeNeighbour)&&(connector.positiveNeighbour==Connections[i].positiveNeighbour))
		{
			return true;
		} //must be done for two cases depending on the orientation of the connection -/+ ->+/- or -/+->+/-
		if ((connector.negativeNeighbour==Connections[i].positiveNeighbour)&&(connector.positiveNeighbour==Connections[i].negativeNeighbour))
		{
			return true;
		}
	}
	return false;
}


//returns the highest used value in an element container
int getHighestElementID(std::vector<f1DElement> &elements){
	int highestID=0;
	for ( unsigned int i=0;i<elements.size();i++){
		if (elements[i].ID>highestID)highestID=elements[i].ID;
	}
	return highestID;
}

int getHighestConnectorID(std::vector<f1DConnector> &connectors){
	int highestID=0;
	for ( unsigned int i=0;i<connectors.size();i++){
		if (connectors[i].ID>highestID)highestID=connectors[i].ID;
	}
	return highestID;
}

//looks if there is a second connection from elref to conref in another element//returns bool if a back connection was found
//function is executed by allbackconnection function
bool AConnection(int elref,int conref,std::vector<connectionParser> &unparsedConnections) 
{
	bool foundFirst=false;
	for (unsigned int i=0 ; i<unparsedConnections.size();i++){
		for (unsigned int j=0 ; j<unparsedConnections[i].negconnectionBuffer.size();j++){
			if((unparsedConnections[i].negconnectionBuffer[j].negref==elref)&&(unparsedConnections[i].negconnectionBuffer[j].posref==conref)){
				if (foundFirst)
				{
					return true;
				}
				else
				{
					foundFirst=true;
				}
			}
			if((unparsedConnections[i].negconnectionBuffer[j].negref==conref)&&(unparsedConnections[i].negconnectionBuffer[j].posref==elref)){
				if (foundFirst){
					return true;
				}
				else
				{
					foundFirst=true;
				}
			}
		}
		for (unsigned int j=0 ; j<unparsedConnections[i].posconnectionBuffer.size();j++){
			if((unparsedConnections[i].posconnectionBuffer[j].negref==elref)&&(unparsedConnections[i].posconnectionBuffer[j].posref==conref)){
				if (foundFirst)
				{
					return true;
				}
				else
				{
					foundFirst=true;
				}
			}
			if((unparsedConnections[i].posconnectionBuffer[j].negref==conref)&&(unparsedConnections[i].posconnectionBuffer[j].posref==elref)){
				if (foundFirst)
				{
					return true;
				}
				else
				{
					foundFirst=true;
				}
			}
		}
	}
	return false;
}

//has every connection its second connection, excluded openend connections
//checkDoubleConnection has to be executed first to work correct
//returns vector index of the element with a connection without backconnection
//returns RESULT_FALSE =(-1) if every backconnection exists
//in id the element ref stored if !result_false
int AllBackConnection(std::vector<connectionParser> &unparsedConnections, int &id,int &line)
{ 
	for (unsigned int i=0 ; i<unparsedConnections.size();i++){
		for (unsigned int j=0 ; j<unparsedConnections[i].negconnectionBuffer.size();j++){
			if ((unparsedConnections[i].negconnectionBuffer[j].posref==0) ||(unparsedConnections[i].negconnectionBuffer[j].negref==0))
				continue;//exclude openends for they have not backconnection 
			if(!AConnection(unparsedConnections[i].negconnectionBuffer[j].posref,unparsedConnections[i].negconnectionBuffer[j].negref,unparsedConnections))
			{
				id=unparsedConnections[i].negconnectionBuffer[j].negref;
				line=unparsedConnections[i].negconnectionBuffer[j].line;
				return i;
			}
		}
		for (unsigned int j=0 ; j<unparsedConnections[i].posconnectionBuffer.size();j++){
			if ((unparsedConnections[i].posconnectionBuffer[j].posref==0) ||(unparsedConnections[i].posconnectionBuffer[j].negref==0))
				continue;//exclude openends for they have not backconnection
			if(!AConnection(unparsedConnections[i].posconnectionBuffer[j].posref,unparsedConnections[i].posconnectionBuffer[j].negref,unparsedConnections))
			{
				id=unparsedConnections[i].posconnectionBuffer[j].posref;
				line=unparsedConnections[i].posconnectionBuffer[j].line;
				return i;
			}
		}
	}
	return RESULT_FALSE;
}

//support function for check double connection
//returns true if an int value exists alreade in an int vector-array
bool intInVector(int id,std::vector<int> &vector)
{
	for (unsigned int i=0 ; i<vector.size();i++){
		if(vector[i]==id)
			return true;
	}
	return false;
}

//check if the p-elements has more than one connection to another element 
//returns the vector index of the first p-element found
//returns RESULT_FALSE =(-1) if every element is ok
//function has to be executed befor allbackconnection

int checkDoubleConnection(std::vector<connectionParser> &unparsedConnections,int &ref,int &line)
{
	std::vector<int> ids;
	for (unsigned int i=0 ; i<unparsedConnections.size();i++){
		ids.clear();
		for (unsigned int j=0 ; j<unparsedConnections[i].negconnectionBuffer.size();j++){
			if (intInVector(unparsedConnections[i].negconnectionBuffer[j].negref,ids)){
				ref=unparsedConnections[i].negconnectionBuffer[j].negref;
				line=unparsedConnections[i].negconnectionBuffer[j].line;
				return i;
			}else
				ids.push_back(unparsedConnections[i].negconnectionBuffer[j].negref);
		}
		for (unsigned int j=0 ; j<unparsedConnections[i].posconnectionBuffer.size();j++){
			if (intInVector(unparsedConnections[i].posconnectionBuffer[j].posref,ids)){
				ref=unparsedConnections[i].posconnectionBuffer[j].posref;
				line=unparsedConnections[i].posconnectionBuffer[j].line;
				return i;
			}else
				ids.push_back(unparsedConnections[i].posconnectionBuffer[j].posref);
		}
	}
	return RESULT_FALSE;
}


//validates that for every connection for an element there is a second connection in another element which referes to the first element
//validates also that there is only allowed exact one connection or no connection between to elements
//recommed to use because it can indicate failures in the parsing graph-to-elementlist proces
bool preCheckElementConnections(f1DCalculationContainer* container,std::vector<connectionParser> &unparsedConnections)
{
	int line=0;
	int ref=0;
	int result=0;
	result=checkDoubleConnection(unparsedConnections,ref,line);
	if(!(result==RESULT_FALSE)){
		std::cout<<"Error: Element with a redundant connection was found!"<<std::endl;
		std::cout<<"Element-ID: "<<container->elements[result].ID<<", refered to: "<<ref<<" @Line: "<<line<<std::endl;
		return false;
	}
	result=AllBackConnection(unparsedConnections,ref,line);
	if(!(result==RESULT_FALSE)){
		std::cout<<"Error: Element with no back connection was found!"<<std::endl;
		std::cout<<"Element-ID: "<<container->elements[result].ID<<", refered to: "<<ref<<" @Line: "<<line<<std::endl;
		return false;
	}
	return true;

}

//v-elements are created from the raw connection buffer data, openend elements( ref 0) are created if necessary, vpointers are mapped to p-elements
//in a open element, there is a start p-element-> every element gets a unique ID, open end connetions are mapped to this elements
int parseVRawData(f1DCalculationContainer* container,std::vector<connectionParser> &unparsedConnections){
	//first check if a p-element has redundant connections

	if(!preCheckElementConnections(container,unparsedConnections))
	{
		std::cout<<"Error during element pre-validation!"<<std::endl;
		return FATAL_ERROR;
	}

	f1DConnector connectorBuffer;//dummies to use vector.push_back()
	f1DOpenElement openElement;
	std::cout<<"Start creating pressure-pointers..."<<std::endl;
	if (unparsedConnections.size()<1){ //check if there are connections in the buffer
		std::cout<<"Error: No Connection found!"<<std::endl;
		return NO_CONNECTION_FOUND;
	}
	const int openEndStartID=getHighestElementID(container->elements)+1; //IDs for p-elements in open ends 


	for (unsigned int i=0; i<unparsedConnections.size();i++){// for each  element there is connection buffercontainer
		float dummys=0;
		for (unsigned int k=0;k<unparsedConnections[i].negconnectionBuffer.size();k++){ //look for the negative neighbours connections

			bool IsNew=false;//needed to mark an openelement

			connectorBuffer.ID=container->connectors.size();//give the v-element a unique ID

			connectorBuffer.crossSectionArea=unparsedConnections[i].negconnectionBuffer[k].area; //store cross section area


			
			if (unparsedConnections[i].negconnectionBuffer[k].negref){ //check if ref is not "0"
				connectorBuffer.negativeNeighbour=getNeighbourPointer(unparsedConnections[i].negconnectionBuffer[k].negref,container->elements); //get the pointer of the p-element which is described by ref
				if ((connectorBuffer.negativeNeighbour==nullptr)){//check if something went wrong
					std::cout<<"Error @Line: "<<unparsedConnections[i].negconnectionBuffer[k].line<<std::endl;
					std::cout<<"Element ID: "<<unparsedConnections[i].negconnectionBuffer[k].negref<<"  connection could not be found!"<<std::endl;
					return FATAL_ERROR;
				}
			}else {
				IsNew=true; //mark that there is an open element
				openElement.ID=container->openElements.size(); //give it an ID
				openElement.direction=-1; // mark the direction, -1= is connected as an negative neighbour
				container->openElements.push_back(openElement); //create an openelement
				container->openElements[container->openElements.size()-1].element.ID=openEndStartID+container->openElements.size(); //give it an ID which is not used by normal p-elements
				container->openElements[container->openElements.size()-1].element.damping=1;//initialize values
				container->openElements[container->openElements.size()-1].element.pressure=0.0f;
				container->openElements[container->openElements.size()-1].connector=nullptr; //dont let it point to nirvana ;)
				unparsedConnections[i].negconnectionBuffer[k].negref=container->openElements[container->openElements.size()-1].element.ID;//give it an ID which is not used by normal p-elements
				connectorBuffer.negativeNeighbour=&container->openElements[container->openElements.size()-1].element;//map v-pointer to the corresponding p-element
			}

			if (unparsedConnections[i].negconnectionBuffer[k].posref){//check if ref is not "0" //double check for e0 +/- 0 not needed, guarded by if statement in store filetobuffer, element IDs must be greater zero
				connectorBuffer.positiveNeighbour=getNeighbourPointer(unparsedConnections[i].negconnectionBuffer[k].posref,container->elements);//get the pointer of the p-element which is described by ref
				if ((connectorBuffer.positiveNeighbour==nullptr)){//check if something went wrong
					std::cout<<"Error @Line: "<<unparsedConnections[i].negconnectionBuffer[k].line<<std::endl;
					std::cout<<"Element ID: "<<unparsedConnections[i].negconnectionBuffer[k].posref<<" for connection could not be found!"<<std::endl;
					return FATAL_ERROR;
				}
			}else {
				IsNew=true;//mark that there is an open element
				openElement.ID=container->openElements.size();// mark the direction, += is connected as an positive neighbour
				openElement.direction=+1;// mark the direction, += is connected as an positive neighbour
				container->openElements.push_back(openElement);//create an openelement
				container->openElements[container->openElements.size()-1].element.ID=openEndStartID+container->openElements.size();//give it an ID which is not used by normal p-elements
				container->openElements[container->openElements.size()-1].element.damping=1;//initialize values
				container->openElements[container->openElements.size()-1].element.pressure=0.0f;
				container->openElements[container->openElements.size()-1].connector=nullptr; //dont let it point to nirvana ;)
				unparsedConnections[i].negconnectionBuffer[k].posref=container->openElements[container->openElements.size()-1].element.ID;//give it an ID which is not used by normal p-elements
				connectorBuffer.negativeNeighbour=&container->openElements[container->openElements.size()-1].element;//map v-pointer to the corresponding p-element

			}
			if ((!IsRedundantConnection(connectorBuffer,container->connectors)||IsNew)){ //check if the connections doesnot exist already
				connectorBuffer.velocity=0;//initialise some values
				connectorBuffer.damping=(connectorBuffer.negativeNeighbour->damping+connectorBuffer.positiveNeighbour->damping)*0.5f;
				connectorBuffer.vfactor=0;
				container->connectors.push_back(connectorBuffer);//create v- element
			}
		}
		//the same for all the positive neighbours, behaviour is equal to negative neighbours
		for (unsigned int k=0;k<unparsedConnections[i].posconnectionBuffer.size();k++){
			bool IsNew=false;//for a openelement
			connectorBuffer.ID=container->connectors.size();
			connectorBuffer.crossSectionArea=unparsedConnections[i].posconnectionBuffer[k].area;

			if (unparsedConnections[i].posconnectionBuffer[k].negref){
				connectorBuffer.negativeNeighbour=getNeighbourPointer(unparsedConnections[i].posconnectionBuffer[k].negref,container->elements);
				if ((connectorBuffer.negativeNeighbour==nullptr)){
					std::cout<<"Error @Line: "<<unparsedConnections[i].posconnectionBuffer[k].line<<std::endl;
					std::cout<<"Element ID: "<<unparsedConnections[i].posconnectionBuffer[k].negref<<" for connection could not be found!"<<std::endl;
					return FATAL_ERROR;
				}
			}else {
				IsNew=true;
				openElement.ID=container->openElements.size();
				openElement.direction=-1;
				container->openElements.push_back(openElement);
				container->openElements[container->openElements.size()-1].element.ID=openEndStartID+container->openElements.size();
				container->openElements[container->openElements.size()-1].element.damping=1;//initialize values
				container->openElements[container->openElements.size()-1].element.pressure=0.0f;
				container->openElements[container->openElements.size()-1].connector=nullptr; //dont let it point to nirvana ;)
				unparsedConnections[i].posconnectionBuffer[k].negref=container->openElements[container->openElements.size()-1].element.ID;
				connectorBuffer.positiveNeighbour=&container->openElements[container->openElements.size()-1].element;
			}
			
			if (unparsedConnections[i].posconnectionBuffer[k].posref){
				connectorBuffer.positiveNeighbour=getNeighbourPointer(unparsedConnections[i].posconnectionBuffer[k].posref,container->elements);

			
				if ((connectorBuffer.positiveNeighbour==nullptr)){
					std::cout<<"Error @Line: "<<unparsedConnections[i].posconnectionBuffer[k].line<<std::endl;
					std::cout<<"Element ID: "<<unparsedConnections[i].posconnectionBuffer[k].posref<<" for connection could not be found!"<<std::endl;
					return FATAL_ERROR;
				}
			}else {
				IsNew=true;
				openElement.ID=container->openElements.size();
				openElement.direction=1;
				container->openElements.push_back(openElement);
				container->openElements[container->openElements.size()-1].element.ID=openEndStartID+container->openElements.size();
				container->openElements[container->openElements.size()-1].element.damping=1;//initialize values
				container->openElements[container->openElements.size()-1].element.pressure=0.0f;
				container->openElements[container->openElements.size()-1].connector=nullptr; //dont let it point to nirvana ;)
				unparsedConnections[i].posconnectionBuffer[k].posref=container->openElements[container->openElements.size()-1].element.ID;
				connectorBuffer.positiveNeighbour=&container->openElements[container->openElements.size()-1].element;
			}
	
			if ((!IsRedundantConnection(connectorBuffer,container->connectors))||IsNew){
				connectorBuffer.velocity=0;
				connectorBuffer.damping=(connectorBuffer.negativeNeighbour->damping+connectorBuffer.positiveNeighbour->damping)*0.5f;
				connectorBuffer.vfactor=0;
				container->connectors.push_back(connectorBuffer);
			}
		}//V-Parsing done
	}
	return NO_ERR;//everything went well
}

//returns a pointer to a v-element in a v-element vector were the v-element describes the same connection as a raw connection
f1DConnector* getConnectorPointer(connection & aConnection,std::vector<f1DConnector> &connectors)
{
	for (unsigned int i=0; i<connectors.size();i++){//look if the ids are idental
		if ((aConnection.negref==connectors[i].negativeNeighbour->ID)&&(aConnection.posref==connectors[i].positiveNeighbour->ID)){
			return &connectors[i];
		} // must be done twice because of the orientation
		if ((aConnection.negref==connectors[i].positiveNeighbour->ID)&&(aConnection.posref==connectors[i].negativeNeighbour->ID)){
			return &connectors[i];
		}
	}
	return nullptr;
}

//referenceable by ID because an openelement has a unique Id and a single connection
f1DConnector* getConnectorPointer(int openEndPElementID,std::vector<f1DConnector> &connectors)
{
	for (unsigned int i=0; i<connectors.size();i++){//look if the ids are idental
		if ((openEndPElementID==connectors[i].negativeNeighbour->ID)||(openEndPElementID==connectors[i].positiveNeighbour->ID)){
			return &connectors[i];
		} // must be done twice because of the orientation
	}
	return nullptr;
}

//the v-pointers of the p-elements are mapped to v-elements
// neighbours orientation vector is created and initialized
int mapVPointers(f1DCalculationContainer* container,std::vector<connectionParser> &unparsedConnections){
	std::cout<<"Start mapping velocity-pointers..."<<std::endl;
	if (container->elements.size()!=unparsedConnections.size()){
		std::cout<<"FATAL_ERROR: Elementsize does not equal unparsedConnectionsize!"<<std::endl;
		return FATAL_ERROR;
	}
	for (unsigned int i=0; i< container->elements.size();i++){ //for every p-element 
		for (unsigned int k=0;k<unparsedConnections[i].negconnectionBuffer.size();k++)// every negative neighbour connection from raw data
		{
			pf1DConnector aConnectorPointer;
			aConnectorPointer=getConnectorPointer(unparsedConnections[i].negconnectionBuffer[k],container->connectors);// find the v-element-pointer which describes the same connection as the connection raw data
			if (!(aConnectorPointer==nullptr)){//check if the connection really exists->something went really wrong
				container->elements[i].negativeNeighbours.push_back(aConnectorPointer);//map the v-pointer to v-element
			} else{
				std::cout<<"FATAL_ERROR: Lost negative neighbour-pointer to v from: "<<unparsedConnections[i].negconnectionBuffer[k].negref<<" to "<<unparsedConnections[i].negconnectionBuffer[k].posref<<std::endl;
				return FATAL_ERROR;
			}
		}
		for (unsigned int k=0;k<unparsedConnections[i].posconnectionBuffer.size();k++)//same for the positive neighbours
		{
			pf1DConnector aConnectorPointer;
			aConnectorPointer=getConnectorPointer(unparsedConnections[i].posconnectionBuffer[k],container->connectors);


			if (!(aConnectorPointer==nullptr)){
				container->elements[i].positiveNeighbours.push_back(aConnectorPointer);
			} else{
				std::cout<<"FATAL_ERROR: Lost positive neighbour-pointer to v from: "<<unparsedConnections[i].posconnectionBuffer[k].negref<<" to "<<unparsedConnections[i].posconnectionBuffer[k].posref<<std::endl;
				return FATAL_ERROR;
			}
		}
	}//v-pointer mapping for p-elements is done

	for (unsigned int i=0; i< container->openElements.size();i++){ //for every p-element 
		pf1DConnector aConnectorPointer =getConnectorPointer(container->openElements[i].element.ID,container->connectors);
		container->openElements[i].connector=aConnectorPointer;
		if(!container->openElements[i].connector){
			std::cout<<"FATAL_ERROR: V-Pointer for OpenElement ID: "<<container->openElements[i].element.ID<<" could not be found."<<std::endl;
			return FATAL_ERROR;
		}
		container->openElements[i].element.negativeNeighbours.push_back(aConnectorPointer);
		container->openElements[i].element.negativeDirections.push_back(container->openElements[i].direction);
	}//v-pointer mapping for openelements is done


	int orientationdummy=0;
	//orientations are done
	for (unsigned int i=0; i< container->elements.size();i++){ //for every p-element 
		for (unsigned int k=0;k<container->elements[i].negativeNeighbours.size();k++)// every negative neighbour connection from raw data
		{
			if (container->elements[i].negativeNeighbours[k]->negativeNeighbour->ID==container->elements[i].ID){
				orientationdummy=-1;//wrong orientation
			}else if (container->elements[i].negativeNeighbours[k]->positiveNeighbour->ID==container->elements[i].ID){
				orientationdummy=1; //right orientation
			} else {//something went fucking wrong
				std::cout<<"FATAL_ERROR: Mismatched pointer from p-element: "<<container->elements[i].ID<<" to v-element: "<<container->elements[i].negativeNeighbours[k]->ID<<std::endl;
			}
			container->elements[i].negativeDirections.push_back(orientationdummy);
		}
		for (unsigned int k=0;k<container->elements[i].positiveNeighbours.size();k++)//same for the positive neighbours
		{
			if (container->elements[i].positiveNeighbours[k]->negativeNeighbour->ID==container->elements[i].ID){
				orientationdummy=1; //right orientation
			}else if (container->elements[i].positiveNeighbours[k]->positiveNeighbour->ID==container->elements[i].ID){
				orientationdummy=-1;//wrong orientation
			} else {//something went fucking wrong
				std::cout<<"FATAL_ERROR: Mismatched pointer from p-element: "<<container->elements[i].ID<<" to v-element: "<<container->elements[i].negativeNeighbours[k]->ID<<std::endl;
			}
			container->elements[i].positiveDirections.push_back(orientationdummy);
		}
	}

	return NO_ERR; // every thing is fine
}

//create speaker elements from raw data and create v-elements on which they are mapped
int parseAndMapSpeakers(f1DCalculationContainer* container,std::vector<speakerParser> &unparsedSpeakers){
	std::cout<<"Parse speaker raw-data..."<<std::endl;
	std::cout<<"Create speaker connection..."<<std::endl;
	f1DSpeaker dummySpeaker;
	f1DConnector dummyConnector;
	const int IDOffset=getHighestConnectorID(container->connectors)+1;
	
	for (unsigned int i=0; i<unparsedSpeakers.size();i++){
		dummySpeaker.ID=unparsedSpeakers[i].ID;
		dummySpeaker.f=nullptr;
		dummySpeaker.speakerDiscriptor=nullptr;
		//create connection
		dummyConnector.crossSectionArea=(unparsedSpeakers[i].area1+unparsedSpeakers[i].area2)*0.5f;
		dummyConnector.ID=IDOffset+container->speakers.size();
		dummyConnector.damping=1.0f;
		dummyConnector.negativeNeighbour=getNeighbourPointer(unparsedSpeakers[i].ref1,container->elements); //parse the p-pointers 
		if(!dummyConnector.negativeNeighbour){
			std::cout<<"Element with ID: "<<unparsedSpeakers[i].ref1<<" could not be found for speaker ID: "<<dummySpeaker.ID<<" @line: "<<(unparsedSpeakers[i].line+1)<<std::endl;
			return FATAL_ERROR;
		}

		dummyConnector.positiveNeighbour=getNeighbourPointer(unparsedSpeakers[i].ref2,container->elements);
		if(!dummyConnector.positiveNeighbour){
			std::cout<<"Element with ID: "<<unparsedSpeakers[i].ref2<<" could not be found for speaker ID: "<<dummySpeaker.ID<<" @line: "<<(unparsedSpeakers[i].line+2)<<std::endl;
			return FATAL_ERROR;
		}
		dummyConnector.vfactor=container->info->dt/(container->dx*container->info->dt);//initialize
		dummyConnector.velocity=0;
		container->connectors.push_back(dummyConnector);//connection is created

		//create v-pointers and map them to the created connector
		//check if the connectors neighbours have closed ends
		// speaker is connected to closed end
		// new v-pointer is created from element with closed end to speaker-connector-element
		//for the negative side
		if(container->connectors[container->connectors.size()-1].negativeNeighbour->negativeNeighbours.size()==0){ 
			container->connectors[container->connectors.size()-1].negativeNeighbour->negativeNeighbours.push_back(&container->connectors[container->connectors.size()-1]);
			container->connectors[container->connectors.size()-1].negativeNeighbour->negativeDirections.push_back(-1);//wrong orientation - to -
		} else if(container->connectors[container->connectors.size()-1].negativeNeighbour->positiveNeighbours.size()==0){
			container->connectors[container->connectors.size()-1].negativeNeighbour->positiveNeighbours.push_back(&container->connectors[container->connectors.size()-1]);
			container->connectors[container->connectors.size()-1].negativeNeighbour->positiveDirections.push_back(1);//right orientation - to +
		} else{
			std::cout<<"Error during v-element creation for speaker coupling"<<std::endl;
			return FATAL_ERROR;
		}
		//for the positive side
		if(container->connectors[container->connectors.size()-1].positiveNeighbour->negativeNeighbours.size()==0){
			container->connectors[container->connectors.size()-1].positiveNeighbour->negativeNeighbours.push_back(&container->connectors[container->connectors.size()-1]);
			container->connectors[container->connectors.size()-1].positiveNeighbour->negativeDirections.push_back(1);// right orientation + to -
		} else if(container->connectors[container->connectors.size()-1].positiveNeighbour->positiveNeighbours.size()==0){
			container->connectors[container->connectors.size()-1].positiveNeighbour->positiveNeighbours.push_back(&container->connectors[container->connectors.size()-1]);
			container->connectors[container->connectors.size()-1].positiveNeighbour->positiveDirections.push_back(-1);// wrong orientation + to +
		} else{
			std::cout<<"Error during v-element creation for speaker coupling"<<std::endl;
			return FATAL_ERROR;
		}


		dummySpeaker.position=&container->connectors[container->connectors.size()-1];
		if (dummySpeaker.position==nullptr){
			std::cout<<"Lost speaker pointer to Connector!"<<std::endl;
			std::cout<<"ref1: "<<unparsedSpeakers[i].ref1<<std::endl;
			std::cout<<"ref2: "<<unparsedSpeakers[i].ref2<<std::endl;
			return FATAL_ERROR;
		} 
		container->speakers.push_back(dummySpeaker);
	}
	return NO_ERR;
}



int initializeOpenEnds(f1DCalculationContainer* container){

	float exp_m=0; //opening constant
	float area=0;
	std::vector<float> initial(container->info->OpenEndElements,0);
	for (unsigned int i=0; i<container->openElements.size();i++){//for every openelement 
		area=container->openElements[i].connector->crossSectionArea; // allocate memory
		container->openElements[i].pFactorField=initial;
		container->openElements[i].vFactorField=initial;
		container->openElements[i].aField=initial;
		container->openElements[i].pField=initial;
		container->openElements[i].vField=initial;
		for (unsigned int j=0; j<container->openElements[i].aField.size();j++) {
			container->openElements[i].aField[j]=area*exp(exp_m*j); //calculate cross sections
		}

		// create p and v-factors for the open elements

		container->openElements[i].element.pFactor=container->info->density*container->info->gasconstant*container->info->temperature*container->info->dt/
			(container->dx*(container->openElements[i].connector->crossSectionArea+container->openElements[i].aField[0])*0.5f);//pfacotr for the 1st element

		for (unsigned int j=0; j<container->openElements[i].pFactorField.size()-1;j++) {//calculate the other p-factors
		container->openElements[i].pFactorField[j]=container->info->density*container->info->gasconstant*container->info->temperature*container->info->dt/
			(container->dx*(container->openElements[i].aField[j+1]+container->openElements[i].aField[j])*0.5f);			
		}

		//vfacotr for the 1st element
		container->openElements[i].vFactorField[0]=container->info->dt*container->openElements[i].aField[0]/
			(container->info->density*container->dx*(0.25f*(container->openElements[i].connector->crossSectionArea+container->openElements[i].aField[1])+container->openElements[i].aField[0]*0.5f));

		for (unsigned int j=1; j<container->openElements[i].vFactorField.size()-1;j++) {
			container->openElements[i].vFactorField[j]=container->info->dt*container->openElements[i].aField[j]/
			(container->info->density*container->dx*(0.25f*(container->openElements[i].aField[j-1]+container->openElements[i].aField[j+1])+container->openElements[i].aField[j]*0.5f));
		}
		//v-vactor for the last element
			container->openElements[i].vFactorField[container->openElements[i].vFactorField.size()-1]=container->info->dt*container->openElements[i].aField[container->openElements[i].vFactorField.size()-1]/
			(container->info->density *container->dx*(0.25f*(container->openElements[i].aField[container->openElements[i].vFactorField.size()-2]+container->openElements[i].aField[container->openElements[i].vFactorField.size()-1])+container->openElements[i].aField[container->openElements[i].vFactorField.size()-1]*0.5f));
		
	}

	return NO_ERR;

}



int initializeMicrophones(f1DCalculationContainer* container,std::vector<microphoneParser> &unparsedMicrophones){
	std::cout<<"Create microphones..."<<std::endl;
	for (unsigned int i=0; i<unparsedMicrophones.size();i++){
		f1DMicrophone microphonedummy(unparsedMicrophones[i].ID,container->info->numberTimesteps,container->info->dt);
		microphonedummy.refE=getNeighbourPointer(unparsedMicrophones[i].ref,container->elements);
		if (!microphonedummy.refE){
			std::cout<<"Error: Microphone reference, ID: "<<unparsedMicrophones[i].ref<<" @Line: "<<unparsedMicrophones[i].line<<std::endl;
			return FATAL_ERROR;
		}
		container->microphones.push_back(microphonedummy);
	}
	return NO_ERR;
}

// case param=0 negativeneighbourh
//returns true if the connector  is a positive neighbour from its negative neighbour otherwise false is returned
// case param!=1 positiveneighbourh
//returns true if the connector  is a negative neighbour from its positiveneighbour else false is returned
bool isRightNeighbour(f1DConnector & connector,int param)
{
	if (param){ //look at negative neighbour side
		for (unsigned int i=0; i<connector.negativeNeighbour->positiveNeighbours.size();i++)
		{
			if (connector.ID==connector.negativeNeighbour->positiveNeighbours[i]->ID) return true;//id found in positive neighbours 
		}
		return false;//id not found in positive neighbours so it must be in negativeneighbours

	}
	//look at positive side
	for (unsigned int i=0; i<connector.positiveNeighbour->negativeNeighbours.size();i++)
	{
		if (connector.ID==connector.positiveNeighbour->negativeNeighbours[i]->ID) return true;// id found in negative neighbours
	}
	return false;// id not found in negative neighbours so it must be in positvie neighbours
}

int preCalculateFactors(f1DCalculationContainer* container){

	//factors for pressurecalculation are precalculated

	for (unsigned int i=0; i<container->elements.size();i++){
		float sum_area=0;
		for (unsigned int j=0; j<container->elements[i].negativeNeighbours.size();j++){
			sum_area+=container->elements[i].negativeNeighbours[j]->crossSectionArea;
		}
		for (unsigned int j=0; j<container->elements[i].positiveNeighbours.size();j++){
			sum_area+=container->elements[i].positiveNeighbours[j]->crossSectionArea;
		}
		container->elements[i].pFactor=2.0f*container->info->density*container->info->gasconstant*container->info->temperature*container->info->dt/(container->dx*sum_area);
	}

	//factors for velocitycalculation are precalculatet

	for (unsigned int i=0; i<container->connectors.size();i++){
		float sum0=0;
		float sum1=0;
		float sum2=0;
		float area01=0;
		float area12=0;

		//negative neighbourside

		if(isRightNeighbour( container->connectors[i],0)){//=is negative neighbour and right orientated
			for(unsigned int j=0;j<container->connectors[i].negativeNeighbour->positiveNeighbours.size();j++)
			{
				sum1+=container->connectors[i].negativeNeighbour->positiveNeighbours[j]->crossSectionArea;
			}
			for(unsigned int j=0;j<container->connectors[i].negativeNeighbour->negativeNeighbours.size();j++)
			{
				sum0+=container->connectors[i].negativeNeighbour->negativeNeighbours[j]->crossSectionArea;
			}
			area01=0.5*(sum1+sum0)*container->connectors[i].crossSectionArea/sum1;
		}else{
			for(unsigned int j=0;j<container->connectors[i].negativeNeighbour->positiveNeighbours.size();j++)
			{
				sum0+=container->connectors[i].negativeNeighbour->positiveNeighbours[j]->crossSectionArea;
			}
			for(unsigned int j=0;j<container->connectors[i].negativeNeighbour->negativeNeighbours.size();j++)
			{
				sum1+=container->connectors[i].negativeNeighbour->negativeNeighbours[j]->crossSectionArea;
			}
			area01=0.5*(sum1+sum0)*container->connectors[i].crossSectionArea/sum1;
		}

		sum1=0;

		if(isRightNeighbour( container->connectors[i],1)){
			for(unsigned int j=0;j<container->connectors[i].positiveNeighbour->negativeNeighbours.size();j++)
			{
				sum1+=container->connectors[i].positiveNeighbour->negativeNeighbours[j]->crossSectionArea;
			}
			for(unsigned int j=0;j<container->connectors[i].positiveNeighbour->positiveNeighbours.size();j++)
			{
				sum2+=container->connectors[i].positiveNeighbour->negativeNeighbours[j]->crossSectionArea;
			}
			area12=0.5*(sum1+sum2)*container->connectors[i].crossSectionArea/sum1;
		}else{
			for(unsigned int j=0;j<container->connectors[i].positiveNeighbour->positiveNeighbours.size();j++)
			{
				sum2+=container->connectors[i].positiveNeighbour->positiveNeighbours[j]->crossSectionArea;
			}
			for(unsigned int j=0;j<container->connectors[i].positiveNeighbour->negativeNeighbours.size();j++)
			{
				sum1+=container->connectors[i].positiveNeighbour->negativeNeighbours[j]->crossSectionArea;
			}
			area01=0.5*(sum1+sum2)*container->connectors[i].crossSectionArea/sum1;
		}

		container->connectors[i].vfactor=container->info->dt*container->connectors[i].crossSectionArea/
			(container->info->density*container->dx*0.5f*(container->connectors[i].crossSectionArea+0.5f*
			(area01+area12)));
	}
	return NO_ERR;
}

int load1DKernelInput(const char* filename, f1DCalculationContainer* container, int param){

	int error; //dummy to store errorcodes


	if(container==nullptr){ //check if a calculation container is assigned
		std::cout<<"FATAL_ERROR: Bad Containerpointer"<<std::endl;
		return FATAL_ERROR;
	}

	if(container->info==nullptr){//check if there is a calculation descriptor
		std::cout<<"FATAL_ERROR: Bad Info-desc-pointer"<<std::endl;
		return FATAL_ERROR;
	}

	std::cout<<"Load file: "<<filename<<std::endl;

	std::ifstream file(filename,std::ios_base::in);
    if (!file.is_open()){
		std::cout<<"Error while opening file: "<<std::endl;
        std::perror(filename);
		return FILE_NOT_FOUND; //create file stream and check it
	}
	
	//Initialize the container
	container->connectors.clear();
	container->elements.clear();
	container->speakers.clear();
	container->microphones.clear();	
	container->openElements.clear();

	//create buffers for the parser;
	std::vector<connectionParser>  unparsedConnections; //buffer for raw-connection-data
	std::vector<speakerParser> unparsedSpeakers; // buffer for raw-speaker-data
	std::vector<microphoneParser> unparsedMicrophones;// buffer for raw-microphones-data

	//read file stream and create raw-p-elements and store the rest to the buffers
	error=storeFileToBuffers(container,file,unparsedConnections,unparsedSpeakers,unparsedMicrophones);
	if(error){
		std::cout<<"Error during buffering!"<<std::endl;
		return error;
	}
	file.close(); //everything is buffered, so file can be closed

	if(! param){
		useDefaultDescriptor(container->info); //use standart calculation descriptor
	}
	fullfillDescriptor(container); //missing descriptor values are calculated



	// now unparsed raw-connections are parsed. v-elements and raw-open-end-elements are created and v-element-pointers are mapped to the p-elements

	error=parseVRawData(container,unparsedConnections);
	if(error){
		std::cout<<"Error during velocity Parsing!"<<std::endl;
		return error;
	}

	//Now v-pointers from p-elements are mapped to v-elements

	error=mapVPointers(container,unparsedConnections);
	if(error){
		std::cout<<"Error during V-Pointer mapping!"<<std::endl;
		return error;
	}

	//now speaker elements are created and mapped on v-elements

	error=parseAndMapSpeakers(container,unparsedSpeakers);
	if(error){
		std::cout<<"Error during Speaker parsing and mapping!"<<std::endl;
		return error;
	}

	//now open-end elements are initialized 
	error= initializeOpenEnds(container);
	if(error){
		std::cout<<"Error while creating OpenEndElements!"<<std::endl;
		return error;
	}
		// To do create micropohnes and map them to p-elements
	error=initializeMicrophones(container,unparsedMicrophones);
	if(error){
		std::cout<<"Error while initializing microphones!"<<std::endl;
		return error;
	}


	preCalculateFactors(container);

	//Show Parsing Result
	std::cout<<std::endl;
	std::cout<<"**************************************"<<std::endl;	
	std::cout<<"Parsing to kernelformat succesfully done."<<std::endl;
	std::cout<<"**************************************"<<std::endl;	
	std::cout<<container->elements.size()<<" Element(s) were created"<<std::endl;
	std::cout<<container->connectors.size()<<" Connector(s) were created"<<std::endl;
	std::cout<<container->speakers.size()<<" Speaker(s) were created"<<std::endl;
	std::cout<<container->microphones.size()<<" Microphone(s) were created"<<std::endl;
	std::cout<<container->openElements.size()<<" Infinite baffle(s) were created"<<std::endl;
	std::cout<<"**************************************"<<std::endl;	
	return NO_ERR; //pointer to buffer, buffersize in bytes
}

