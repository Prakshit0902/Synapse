#include "NetworkHandler.h"
#include <opencv2/imgcodecs.hpp>

NetworkHandler::NetworkHandler()  : context(1), publisher(context, ZMQ_PUB){
	// Constructor implementation
	/*
	* context := Ye ZMQ ka "Motherboard" hai. Saare sockets isi ke under kaam karte hain.
	* publisher := Ye ek ZMQ socket hai jo "Publish-Subscribe" pattern mein use hota hai.
	*			mujhe mtlb nahi koi sune yaa na sune mera kaam data hawa me fekna baaki tum tumhara dekho
	* 1  in context := iska matlab hai ZMQ ke background mein 1 Thread chalega IO (Input/Output) handle karne ke liye.
	*/

}

void NetworkHandler::init(std::string protocol) {
	publisher.bind(protocol);
	/*
	* protocol := Ye ek string hai jo batata hai ki hum kis address par data bhejenge. like "tcp://*5555"/ * isliye kisi bhi IP se connect ho sakta hai
	*  bind := ye socket se bind hota client connect karta hai
	*/
}

void NetworkHandler::sendFrame(cv::Mat& frame) { // &  reference pass by memory me copy nahi kar rhe
	if(frame.empty()) {
		return;
	}

	std::vector<uchar> buffer; // unsigined char range 0 -255
	std::vector<int> params;
	params.push_back(cv::IMWRITE_JPEG_QUALITY);
	params.push_back(80);
	cv::imencode(".jpg", frame, buffer, params);
	zmq::message_t message(buffer.size());
	// (Destination, Source, Size) ye niche galat hai
	// memcpy(buffer.data(), message.data(), buffer.size());
	memcpy(message.data(), buffer.data(), buffer.size());
	publisher.send(message, zmq :: send_flags :: none);

}
void NetworkHandler::sendAudioChunk(const void* data, size_t size) {
	// Raw bytes ka message banao
	zmq::message_t message(data, size);

	// ZMQ socket se bhej do (Don't wait/block if possible)
//	socket.send(message, zmq::send_flags::none);
	publisher.send(message, zmq::send_flags::none);

}