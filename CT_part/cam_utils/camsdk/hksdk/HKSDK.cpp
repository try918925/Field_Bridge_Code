#include <iostream>
#include <stdio.h>
#include "hikvision/HCNetSDK.h"
#include "hikvision/LinuxPlayM4.h"
#include <unistd.h>
#include <map>
#include <mutex>
#include <string>
#include<pybind11/pybind11.h>
#include<pybind11/numpy.h>
#include<pybind11/stl.h>
using namespace std;

namespace py = pybind11;

class Frame
{
public:
    Frame()
    {
        this->width = 0;
        this->height = 0;
        this->frame_content = NULL;
        this->isRead = false;
    }
    Frame(int width, int height, int length, unsigned char* buf)
    {
        this->width = width;
        this->height = height;
        this->length = length;
        this->frame_content = new unsigned char[length];
        memcpy(this->frame_content, buf, length);
        this->isRead = false;
    }
    ~Frame()
    {   
        if (frame_content != NULL)
        {
            delete [] frame_content;
            frame_content = NULL;
        }       
    }
    int width;
    int height;
    int length;
    bool isRead;
    unsigned char* frame_content;
    
    // unsigned char* convertRGB();
};

map<int, int> handleToPort;
map<int, int> portToHandle;
map<int, Frame*> handleToFrame;
map<int, mutex*> handleToMutex;
bool initStatus = false;
mutex mut;

//视频为YUV数据(YV12)，音频为PCM数据
void CALLBACK DecFun(int lPort, char *pBuf, int nSize, FRAME_INFO *pFrameInfo, void *nReserved1, int nReserved2)
{
    auto ph = portToHandle.find(lPort);
    if (ph == portToHandle.end())
    {
        return;
    }
    long lFrameType = pFrameInfo->nType;
    int giCameraFrameWidth = pFrameInfo->nWidth;
	int giCameraFrameHeight = pFrameInfo->nHeight;
    if (lFrameType == T_YV12)
    {
        Frame* frame = new Frame(giCameraFrameWidth, giCameraFrameHeight, nSize, (unsigned char*)pBuf);

        auto hm = handleToMutex.find(ph->second);
        if (hm == handleToMutex.end())
        {
            return;
        }
        hm->second->lock();
        auto hf = handleToFrame.find(ph->second);
        // delete[] hf->second;
        if (hf->second != NULL)
        {
            delete hf->second;
        }
        hf->second = frame;
        hm->second->unlock();
    }
}

void CALLBACK fRealDataCallBack(LONG lRealHandle, DWORD dwDataType, BYTE *pBuffer,DWORD dwBufSize,void* dwUser)
{
    if (handleToPort.find(lRealHandle) == handleToPort.end())
    {
        // cout << "handlerId not found !!!=====>" << lRealHandle << endl;
        return;
    }
    int nPort = handleToPort.find(lRealHandle)->second;
    switch (dwDataType)
    {
        case NET_DVR_SYSHEAD:  //系统头
            if (!PlayM4_GetPort(&nPort))   //获取播放库未使用的通道号
            {
                break;
            }
            // std::cout << "系统头" << dwBufSize << std::endl;
            if (dwBufSize > 0)
            {
                if (!PlayM4_SetStreamOpenMode(nPort, STREAME_REALTIME)) //设置实时流播放模式
                {
                    break;
                }
                if (!PlayM4_OpenStream(nPort, pBuffer, dwBufSize, 1024 * 1024))  //打开流接口
                {
                    break;
                }
                //解码实时回调
                if (!PlayM4_SetDecCallBack(nPort, DecFun))
                {
                    break;
                }
                if (!PlayM4_Play(nPort, NULL)) //播放开始
                {
                    break;
                }
            }
            // cout << "port===============" << nPort << endl;
            handleToPort[lRealHandle] = nPort;
            portToHandle[nPort] = lRealHandle;
            break;
        case NET_DVR_STREAMDATA:
            if (dwBufSize > 0 && nPort != -1)
            {
                if (!PlayM4_InputData(nPort, pBuffer, dwBufSize))
                {
                    break;
                }
            }
            break;
    }
}

py::tuple getFrame(int handleId, bool isForce=false)
{
    int width = 0;
    int height = 0;
    auto hm = handleToMutex.find(handleId);
    if (hm == handleToMutex.end())
    {
        return py::make_tuple(false, NULL, 0, 0);
    }
    hm->second->lock();
    auto hf = handleToFrame.find(handleId);
    if (hf == handleToFrame.end())
    {
        hm->second->unlock();
        return py::make_tuple(false, NULL, 0, 0);
    }
    if (hf->second == NULL)
    {
        hm->second->unlock();
        return py::make_tuple(false, NULL, 0, 0);
    }
    if (hf->second->isRead && !isForce) {
        hm->second->unlock();
        return py::make_tuple(false, NULL, 0, 0);
    }
    width = hf->second->width;
    height = hf->second->height;
    int length = hf->second->length;
    py::array_t<unsigned char> data(length);
    memcpy(data.mutable_data(), hf->second->frame_content, length);
    hf->second->isRead = true;
    hm->second->unlock();
    return py::make_tuple(true, data, width, height);
}

py::tuple init()
{
    mut.lock();
    if (initStatus)
    {
        mut.unlock();
        return py::make_tuple(true, 0);
    }
    bool rsCode = NET_DVR_Init();
    if (rsCode) 
    {
        initStatus = true;
        mut.unlock();
        return py::make_tuple(true, 0);
    }
    mut.unlock();
    return py::make_tuple(false, NET_DVR_GetLastError());
}

py::tuple login(char* ip, char* username, char* password)
{
    NET_DVR_USER_LOGIN_INFO struLoginInfo = {0};
    NET_DVR_DEVICEINFO_V40 struDeviceInfoV40 = {0};
    struLoginInfo.bUseAsynLogin = false;

    struLoginInfo.wPort = 8000;
    strcpy(struLoginInfo.sDeviceAddress, ip);
    strcpy(struLoginInfo.sUserName, username);
    strcpy(struLoginInfo.sPassword, password);

    int userId = NET_DVR_Login_V40(&struLoginInfo, &struDeviceInfoV40);
    if (userId < 0)
    {
        return py::make_tuple(userId, NET_DVR_GetLastError());
    }
    return py::make_tuple(userId, 0);
}

py::tuple open(int userId)
{
    NET_DVR_PREVIEWINFO struPlayInfo = { 0 };
    struPlayInfo.hPlayWnd = NULL;         //需要SDK解码时句柄设为有效值，仅取流不解码时可设为空
    struPlayInfo.lChannel = 1;       //预览通道号
    struPlayInfo.dwStreamType = 0;       //0-主码流，1-子码流，2-码流3，3-码流4，以此类推
    struPlayInfo.dwLinkMode = 0;       //0- TCP方式，1- UDP方式，2- 多播方式，3- RTP方式，4-RTP/RTSP，5-RSTP/HTTP
    struPlayInfo.bBlocked = 0;    //0- 非阻塞取流,1- 阻塞取流

    int handlerId = NET_DVR_RealPlay_V40(userId, &struPlayInfo, fRealDataCallBack, NULL);
    if (handlerId < 0)
    {
        return py::make_tuple(handlerId, NET_DVR_GetLastError());
    }
    handleToPort[handlerId] = -1;
    handleToMutex[handlerId] = new mutex();
    handleToFrame[handlerId] = NULL;
    return py::make_tuple(handlerId, 0);
}

py::tuple logout(int userId)
{
    bool rsCode = NET_DVR_Logout(userId);
    if (rsCode)
    {
        return py::make_tuple(true, 0);
    }
    return py::make_tuple(false, NET_DVR_GetLastError());
}

py::tuple closeCamera(int handler) {
    auto hp = handleToPort.find(handler);
    if (hp == handleToPort.end())
    {
        return py::make_tuple(true, 0);
    }
    handleToPort.erase(hp->first);
    int port = hp->second;
    PlayM4_Stop(port);
    PlayM4_CloseStream(port);
    PlayM4_FreePort(port);
    NET_DVR_StopRealPlay(handler);
    auto ph = portToHandle.find(port);
    if (ph != portToHandle.end())
    {
        portToHandle.erase(port);
    }
    auto hm = handleToMutex.find(handler);
    if (hm != handleToMutex.end())
    {
        hm->second->lock();
        auto hf = handleToFrame.find(handler);
        if (hf != handleToFrame.end())
        {
            delete hf->second;
            handleToFrame.erase(hf->first);
        }
        hm->second->unlock();
        handleToMutex.erase(hm->first);
        delete hm->second;
    }
    return py::make_tuple(true, 0);
}

py::tuple getPTZ(int userId, int handler)
{
    auto hp = handleToPort.find(handler);
    if (hp == handleToPort.end())
    {
        return py::make_tuple(false, NET_DVR_GetLastError());
    }
    int port = hp->second;
    DWORD dwReturnLen;
    NET_DVR_PTZPOS struParams = {0};
    bool iRet = NET_DVR_GetDVRConfig(userId, NET_DVR_GET_PTZPOS, port, &struParams, sizeof(NET_DVR_PTZPOS), &dwReturnLen);
    if (!iRet)
    {
        return py::make_tuple(false, NET_DVR_GetLastError(), 0, 0, 0);
    }
    return py::make_tuple(true, 0, struParams.wPanPos, struParams.wTiltPos, struParams.wZoomPos);
}

py::tuple setPTZ(int userId, int handler, int P, int T, int Z)
{
    auto hp = handleToPort.find(handler);
    if (hp == handleToPort.end())
    {
        return py::make_tuple(false, NET_DVR_GetLastError());
    }
    int port = hp->second;
    DWORD dwReturnLen;
    NET_DVR_PTZPOS struParams = {0};
    bool iRet = NET_DVR_GetDVRConfig(userId, NET_DVR_GET_PTZPOS, port, &struParams, sizeof(NET_DVR_PTZPOS), &dwReturnLen);
    if (!iRet)
    {
        return py::make_tuple(false, NET_DVR_GetLastError());
    }
    struParams.wPanPos = P;
    struParams.wTiltPos = T;
    struParams.wZoomPos = Z;
    iRet = NET_DVR_SetDVRConfig(userId, NET_DVR_SET_PTZPOS, port, &struParams, sizeof(NET_DVR_PTZPOS));
    if (!iRet) {
        return py::make_tuple(false, NET_DVR_GetLastError());
    }
    return py::make_tuple(true, 0);
}

py::tuple getResolution(int userId)
{
    DWORD dwReturnLen;
    NET_DVR_COMPRESSIONCFG_V30 struParams = {0};
    bool iRet = NET_DVR_GetDVRConfig(userId, NET_DVR_GET_COMPRESSCFG_V30, 1, &struParams, sizeof(NET_DVR_COMPRESSIONCFG_V30), &dwReturnLen);
    if (!iRet)
    {
        return py::make_tuple(false, NET_DVR_GetLastError());
    }
    return py::make_tuple(true, struParams.struNormHighRecordPara.byResolution);
}

py::tuple setResolution(int userId, int resolution)
{
    DWORD dwReturnLen;
    NET_DVR_COMPRESSIONCFG_V30 struParams = {0};
    bool iRet = NET_DVR_GetDVRConfig(userId, NET_DVR_GET_COMPRESSCFG_V30, 1, &struParams, sizeof(NET_DVR_COMPRESSIONCFG_V30), &dwReturnLen);
    if (!iRet)
    {
        return py::make_tuple(false, NET_DVR_GetLastError());
    }
    //设置分辨率参数
    struParams.struNormHighRecordPara.byResolution = resolution;
    iRet = NET_DVR_SetDVRConfig(userId, NET_DVR_SET_COMPRESSCFG_V30, 1, &struParams, sizeof(NET_DVR_COMPRESSIONCFG_V30));
    if (!iRet)
    {
        return py::make_tuple(false, NET_DVR_GetLastError());
    }
    return py::make_tuple(true, 0);
}

PYBIND11_MODULE(HKSDK, m) {
    m.doc() = "hksdk module";
    // Add bindings here
    m.def("init", &init);
    m.def("login", &login);
    m.def("logout", &logout);
    m.def("get_frame", &getFrame);
    m.def("open", &open);
    m.def("close", &closeCamera);
    m.def("get_ptz", &getPTZ);
    m.def("set_ptz", &setPTZ);
    m.def("set_resolution", &setResolution);
    m.def("get_resolution", &getResolution);
}
