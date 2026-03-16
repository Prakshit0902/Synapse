#include "CameraHandler.hpp"

// Constructor
CameraHandler::CameraHandler() {

}

bool CameraHandler::initCamera(int id) {
#ifdef __linux__
    // libcamerify already camera ko intercept karta hai,
    // toh V4L2 backend explicitly use karo - CAP_ANY se conflict hota hai
    cap.open(0, cv::CAP_V4L2);
#else
    cap.open(id);
#endif

    if (!cap.isOpened()) {
        return false;
    }

    cap.set(cv::CAP_PROP_FOURCC, cv::VideoWriter::fourcc('M', 'J', 'P', 'G'));
    /*
    * UDB Camers YUYV(Color Model) format me data deti hai jo uncompressed hota hai
    * jo usb bandwidth zyada leta hai aur processing slow kar deta hai
    * to isliye hum MJPG format set kar rahe hai jisse camera compressed frames dega
    * (Windows ke liye DSHOW, RPi/Linux ke liye V4L2)
    */
    cap.set(cv::CAP_PROP_FRAME_WIDTH, 1280);
    cap.set(cv::CAP_PROP_FRAME_HEIGHT, 720);
    cap.set(cv::CAP_PROP_FPS, 30);
    cap.set(cv::CAP_PROP_BUFFERSIZE, 1); // 1 isliye mujhe latest frame mile old nahi
    return true;
}

cv::Mat CameraHandler::getFrame() {
    cv::Mat tempFrame;
    cap >> tempFrame;
    if (tempFrame.empty())
        return tempFrame;
    cv::flip(tempFrame, tempFrame, 1);
    /*input and output dono same hai jisse
    in-place operation hota hai, new memory allocate nahi hoti
    */
    return tempFrame;
}