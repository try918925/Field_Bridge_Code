#include <iostream>
#include <thread>
#include <gstnvdsmeta.h>
#include <nvbufsurface.h>
#include <nvbufsurftransform.h>
#include <cstring>
#include <map>
#include <mutex>
#include <unistd.h>
#include <string>
#include <opencv2/opencv.hpp>

#include<pybind11/pybind11.h>
#include<pybind11/numpy.h>

namespace py = pybind11;

int MTX_DS_cameraIds = 0; // 定义全局摄像头id(从0开始自增1)
std::map<int, bool> MTX_DS_idToRead;        // 摄像头id对应的图像帧是否被读过
std::map<int, std::mutex*> MTX_DS_idToMutex;  //  摄像头id对应的锁
std::map<int, GMainLoop*> MTX_DS_idToLoop;   //   摄像机id对应的gstreamer循环

std::map<int, NvBufSurface*> MTX_DS_idToSurface;  //  摄像头id对应的显存Surface缓存区
std::map<int, unsigned char*> MTX_DS_idToBuff;  //  摄像头id对应的内存帧缓存区

std::map<int, bool> MTX_DS_idToFrame; // 摄像头id对应的图像帧是否有更新
std::map<int, std::string> MTX_DS_idToUri; // 摄像头id对应的uri
std::map<int, int> MTX_DS_idToGpu; // gpu

bool initStatus = false; // 初始化标志
std::mutex mtx;

//获取每一帧图像的回调函数
GstPadProbeReturn MTX_DS_sink_pad_buffer_probe (GstPad * pad, GstPadProbeInfo * info, gpointer u_data)
{
    GstBuffer *buf = (GstBuffer *) info->data;
    GstMapInfo in_map_info;
    NvBufSurface *surface = NULL;

    memset (&in_map_info, 0, sizeof (in_map_info));

    if (gst_buffer_map (buf, &in_map_info, GST_MAP_READ))
    {
        // 解码后的NV12格式的图像帧
        surface = (NvBufSurface *) in_map_info.data;

        // 获取对应的摄像头id
        int id = GPOINTER_TO_INT(u_data);

        auto itm = MTX_DS_idToMutex.find(id);
        if (itm != MTX_DS_idToMutex.end())
        {
            itm->second->lock();
            auto itf = MTX_DS_idToSurface.find(id);
            if (itf != MTX_DS_idToSurface.end())
            {
                NvBufSurface* surface_buff = itf->second;
                // 将NV21的帧格式转换为BGR
                NvBufSurfTransformParams nvbufsurface_params;
                cudaError_t cuda_err;
                cudaStream_t cuda_stream;
                gint create_result;
                NvBufSurfTransformConfigParams transform_config_params;
                NvBufSurfTransform_Error err;

                int batch_size = surface->batchSize;
                int batch_id = 0;

                nvbufsurface_params.src_rect = NULL;
                nvbufsurface_params.dst_rect = NULL;
                nvbufsurface_params.transform_flag =  0;
                nvbufsurface_params.transform_filter = NvBufSurfTransformInter_Default;

                cuda_err = cudaSetDevice (surface->gpuId);
                cuda_err = cudaStreamCreate(&cuda_stream);
                
                transform_config_params.compute_mode = NvBufSurfTransformCompute_Default;
                transform_config_params.gpu_id = surface->gpuId;
                transform_config_params.cuda_stream = cuda_stream;
                err = NvBufSurfTransformSetSessionParams (&transform_config_params);
                
                NvBufSurfaceMemSet (surface_buff, 0, 0, 0);
                // surface转换
                err = NvBufSurfTransform (surface, surface_buff, &nvbufsurface_params);
                cudaStreamDestroy (cuda_stream);

                //将帧是否读过的状态设为false
                MTX_DS_idToRead[id] = false;
                MTX_DS_idToFrame[id] = true;
            }
            itm->second->unlock();
        }
    }
    gst_buffer_unmap (buf, &in_map_info);

    return GST_PAD_PROBE_OK;
}


// gstreamer的“child-added”信号对应的回调函数 --- 用来指定视频帧解码使用的gpu id
void MTX_DS_decodebin_child_added (GstChildProxy * child_proxy, GObject * object, gchar * name, gpointer user_data)
{
  if (g_strrstr (name, "decodebin") == name) {
      g_signal_connect (G_OBJECT (object), "child-added", G_CALLBACK (MTX_DS_decodebin_child_added), user_data);
  }
  if (g_strstr_len (name, -1, "nvv4l2decoder") == name) {
      g_object_set (object, "gpu-id", GPOINTER_TO_INT(user_data), NULL);
  }
}

// gstreamer的“pad-added”信号对应的回调函数 --- 过滤流中除视频外的内容
void MTX_DS_cb_newpad (GstElement * decodebin, GstPad * decoder_src_pad, gpointer data)
{
    GstCaps *caps = gst_pad_get_current_caps (decoder_src_pad);
    const GstStructure *str = gst_caps_get_structure (caps, 0);
    const gchar *name = gst_structure_get_name (str);
    GstElement *source_bin = (GstElement *) data;
    GstCapsFeatures *features = gst_caps_get_features (caps, 0);

    //过滤流中除视频外的内容
    if (!strncmp (name, "video", 5))
    {
        if (gst_caps_features_contains (features, "memory:NVMM"))
        {
            GstPad *bin_ghost_pad = gst_element_get_static_pad (source_bin, "src");
            if (!gst_ghost_pad_set_target (GST_GHOST_PAD (bin_ghost_pad), decoder_src_pad))
            {
                g_printerr ("Failed to link decoder src pad to source bin ghost pad\n");
            }
            gst_object_unref (bin_ghost_pad);
        } else {
            g_printerr ("Error: Decodebin did not pick nvidia decoder plugin.\n");
        }
    }
}

// 创建gstreamer读取rtsp流的pipeline
int MTX_DS_source(std::string uri, int id, int gpu_id)
{
    gchar* u = const_cast<gchar *>(uri.c_str());

    GMainLoop *loop = NULL;
    GstElement *pipeline = NULL, *sink = NULL;
    GstPad *osd_sink_pad = NULL;

    gst_init (NULL, NULL);
    // 创建gstreamer的loop
    loop = g_main_loop_new (NULL, FALSE);

    // 创建gstreamer的pipeline
    pipeline = gst_pipeline_new ("my-pipeline");
    if (!pipeline )
    {
        g_printerr ("One element could not be created. Exiting.\n");
        return -1;
    }

    // 创建gstreamer的element
    GstElement *bin = gst_bin_new ("MTX_DS_source");

    // gstreeamer的读取rtsp流的plugin
    GstElement *uri_decode_bin = gst_element_factory_make ("uridecodebin", "uri-decode-bin");
    if (!bin || !uri_decode_bin)
    {
        g_printerr ("One element in MTX_DS_source bin could not be created.\n");
        return -1;
    }

    // 设置element属性
    g_object_set (G_OBJECT (uri_decode_bin), "uri", u, NULL);

    // 配置信号处理函数
    g_signal_connect (G_OBJECT (uri_decode_bin), "pad-added", G_CALLBACK (MTX_DS_cb_newpad), bin);
    g_signal_connect (G_OBJECT (uri_decode_bin), "child-added", G_CALLBACK (MTX_DS_decodebin_child_added), GINT_TO_POINTER(gpu_id));
    
    // 往bin中添加element
    gst_bin_add (GST_BIN (bin), uri_decode_bin);
    if (!gst_element_add_pad (bin, gst_ghost_pad_new_no_target ("src", GST_PAD_SRC)))
    {
        g_printerr ("Failed to add ghost pad in MTX_DS_source bin\n");
        return -1;
    }

    gst_bin_add (GST_BIN (pipeline), bin);

    // gstreeamer不显示界面的plugin
    sink = gst_element_factory_make ("fakesink", "nvvideo-renderer");

    g_object_set (G_OBJECT (sink), "sync", FALSE, NULL);

    gst_bin_add_many (GST_BIN (pipeline), sink, NULL);

    // 链接bin和sink
    if (!gst_element_link_many (bin, sink, NULL)) {
        g_printerr ("Elements could not be linked.\n");
        return -1;
    }

    // 设置gstreamer解码后视频帧的回调函数
    osd_sink_pad = gst_element_get_static_pad (sink, "sink");
    if (!osd_sink_pad)
        g_print ("Unable to get sink pad\n");
    else
        gst_pad_add_probe (osd_sink_pad, GST_PAD_PROBE_TYPE_BUFFER,
                           MTX_DS_sink_pad_buffer_probe, GINT_TO_POINTER(id), NULL);

    // 设置pipeline状态
    gst_element_set_state (pipeline, GST_STATE_PLAYING);

    MTX_DS_idToLoop[id] = loop;

    // 开启pipeline循环
    g_main_loop_run (loop);

    gst_element_set_state (pipeline, GST_STATE_NULL);

    gst_object_unref (GST_OBJECT (pipeline));

    g_main_loop_unref (loop);

    return 0;
}

//检测摄像头的帧是否有更新
void detect_frame()
{
    while (true)
    {
        for (auto itf = MTX_DS_idToFrame.begin(); itf != MTX_DS_idToFrame.end(); itf++)
        {
            if (itf->second)
            {
                itf->second = false;
            }
            else
            {
                if (MTX_DS_idToLoop[itf->first] == NULL)
                {
                    std::thread t(MTX_DS_source, MTX_DS_idToUri[itf->first], itf->first, MTX_DS_idToGpu[itf->first]);
                    t.detach();
                }
                else
                {
                    if (g_main_loop_is_running(MTX_DS_idToLoop[itf->first]))
                    {
                        g_main_loop_quit(MTX_DS_idToLoop[itf->first]);
                        MTX_DS_idToLoop[itf->first] = NULL;
                    }
                }
            }
        }
        sleep(5);
    }
}

py::tuple init()
{
    mtx.lock();
    if (initStatus)
    {
        mtx.unlock();
        return py::make_tuple(true, 0);
    }
    std::thread t(detect_frame);
    t.detach();
    initStatus = true;
    mtx.unlock();
    return py::make_tuple(true, 0);
}

// 登录 --- 先登录再打开流
py::tuple login()
{
    mtx.lock();
    int id = MTX_DS_cameraIds;
    MTX_DS_cameraIds++;
    MTX_DS_idToMutex[id] = new std::mutex;
    MTX_DS_idToRead[id] = false;
    MTX_DS_idToFrame[id] = true;
    mtx.unlock();
    return py::make_tuple(true, id);
}

// 注销  --- 释放资源并清除对应的map
py::tuple logout(int id)
{
    mtx.lock();
    auto itl = MTX_DS_idToLoop.find(id);
    if (itl != MTX_DS_idToLoop.end())
    {
        MTX_DS_idToLoop.erase(itl);
    }

    auto itf = MTX_DS_idToFrame.find(id);
    if (itf != MTX_DS_idToFrame.end())
    {
        MTX_DS_idToFrame.erase(itf);
    }

    auto itu = MTX_DS_idToUri.find(id);
    if (itu != MTX_DS_idToUri.end())
    {
        MTX_DS_idToUri.erase(itu);
    }

    auto itg = MTX_DS_idToGpu.find(id);
    if (itg != MTX_DS_idToGpu.end())
    {
        MTX_DS_idToGpu.erase(itg);
    }


    auto itm = MTX_DS_idToMutex.find(id);
    if (itm != MTX_DS_idToMutex.end())
    {
        delete itm->second;
        MTX_DS_idToMutex.erase(itm);
    }

    auto its = MTX_DS_idToSurface.find(id);
    if (its != MTX_DS_idToSurface.end())
    {
        NvBufSurfaceDestroy(its->second);
        MTX_DS_idToSurface.erase(its);
    }

    auto itb = MTX_DS_idToBuff.find(id);
    if (itb != MTX_DS_idToBuff.end())
    {
        delete[] itm->second;
        MTX_DS_idToBuff.erase(itb);
    }
    mtx.unlock();
    return py::make_tuple(true, 0);
}

// 分配初始缓冲区资源并开启gstreamer的解码线程
py::tuple open(std::string uri, int id, int width, int height, int gpu_id = 0)
{
    //创建一个surface缓存区
    NvBufSurfaceCreateParams nvbufsurface_create_params;
    nvbufsurface_create_params.gpuId  = gpu_id;
    nvbufsurface_create_params.width  = width;
    nvbufsurface_create_params.height = height;
    nvbufsurface_create_params.size = 0;
    nvbufsurface_create_params.isContiguous = true;
    nvbufsurface_create_params.colorFormat = NVBUF_COLOR_FORMAT_BGR;
    nvbufsurface_create_params.layout = NVBUF_LAYOUT_PITCH;
    nvbufsurface_create_params.memType = NVBUF_MEM_CUDA_UNIFIED;

    NvBufSurface *surface_buff = NULL;
    NvBufSurfaceCreate(&surface_buff, 1, &nvbufsurface_create_params);

    mtx.lock();
    MTX_DS_idToSurface[id] = surface_buff;

    //帧缓存
    MTX_DS_idToBuff[id] = NULL;

    MTX_DS_idToUri[id] = uri;
    MTX_DS_idToGpu[id] = gpu_id;
    MTX_DS_idToLoop[id] = NULL;
    mtx.unlock();

    //开启解码线程
    std::thread t(MTX_DS_source, uri, id, gpu_id);
    t.detach();
    return py::make_tuple(true, id);
}

// 关闭gstreamer的循环
py::tuple closeCamera(int id)
{
    auto itl = MTX_DS_idToLoop.find(id);
    if (itl != MTX_DS_idToLoop.end())
    {
        g_main_loop_quit(itl->second);
    }
    return py::make_tuple(true, 0);
}

// 获取图像帧
py::tuple getFrame(int id, bool isForce=false)
{
    auto itm = MTX_DS_idToMutex.find(id);
    if (itm == MTX_DS_idToMutex.end())
    {
        return py::make_tuple(false, NULL, 0, 0);
    }
    itm->second->lock();
    auto itf = MTX_DS_idToSurface.find(id);
    if (itf == MTX_DS_idToSurface.end())
    {
        itm->second->unlock();
        return py::make_tuple(false, NULL, 0, 0);
    }
    if (itf->second == NULL)
    {
        itm->second->unlock();
        return py::make_tuple(false, NULL, 0, 0);
    }
    if (MTX_DS_idToRead[id] && !isForce) 
    {
        itm->second->unlock();
        return py::make_tuple(false, NULL, 0, 0);
    }
    gint frame_width = (gint)itf->second->surfaceList[0].width;
    gint frame_height = (gint)itf->second->surfaceList[0].height;
    void *frame_data = itf->second->surfaceList[0].dataPtr;
    size_t frame_step = itf->second->surfaceList[0].pitch;
    size_t length = itf->second->surfaceList[0].dataSize;
    // 获取视频帧对应的内存缓冲区，如果不存在则创建
    unsigned char* buff = NULL;
    if (MTX_DS_idToBuff[id] == NULL)
    {
        // buff = (unsigned char*)malloc(length * sizeof(unsigned char));
        buff = new unsigned char[length];
        MTX_DS_idToBuff[id] = buff;
    }
    else
    {
        buff = MTX_DS_idToBuff[id];
    }
    // 从显存中将帧信息从surface拷贝至内存
    cudaMemcpy(buff, frame_data, length, cudaMemcpyDeviceToHost);
    cv::Mat in_mat = cv::Mat(frame_height, frame_width, CV_8UC3, buff, frame_step);
    py::array_t<unsigned char> data(length);
    // TODO 直接从c++传递给python，不进行内存拷贝工作
    memcpy(data.mutable_data(), in_mat.data, length);
    MTX_DS_idToRead[id] = true;
    itm->second->unlock();
    return py::make_tuple(true, data, frame_width, frame_height);
}

PYBIND11_MODULE(DP, m) {
   m.doc() = "deepstream module";
   m.def("init", &init);
   m.def("login", &login);
   m.def("logout", &logout);
   m.def("get_frame", &getFrame, py::arg("id"), py::arg("isForce")=false);
   m.def("open", &open, py::arg("uri"), py::arg("id"), py::arg("width"), py::arg("height"), py::arg("gpu_id")=0);
   m.def("close", &closeCamera);
}
