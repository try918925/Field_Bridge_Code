import cv2

from camsdk import hksdk as camera_sdk

if __name__ == '__main__':
    import time

    cap = camera_sdk.Device('28', '10.141.1.115', 8000, 'admin', 'Dnt@QC2023', (2560, 1400))
    ret_flag, error_code = cap.login()
    if not ret_flag:
        print("登录失败:", error_code)
        exit()
    # time.sleep(1)
    flag, stutas = cap.open()
    print(flag, stutas)

    time.sleep(1)
    # while True:
    #     ret_flag, error_code, (p, t, z) = cap.get_ptz()
    #     if ret_flag:
    #         print((p, t, z))
    #     time.sleep(1)
    while True:
        time1 = time.time()
        ret_flag, frame = cap.read()
        time2 = time.time()
        print(time2 - time1, end="\t")
        if ret_flag:
            print("!!!")
            cv2.imwrite("frame.png", frame)

            scale_percet = 25

        # width = int(frame.shape[1] * scale_percet/100)
        # height = int(frame.shape[0] * scale_percet/100)
        # dim = (width,height)
        # resized_image = cv2.resize(frame,dim,interpolation=cv2.INTER_AREA)
        # cv2.imshow("resized_image", resized_image)

        # cv2.imshow("frame", frame)
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        # break
        # else:
        #     print('???')
        # time.sleep(20)
