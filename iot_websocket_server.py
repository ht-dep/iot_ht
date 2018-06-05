import asyncio
import websockets
import threading
import datetime
import json
from config import RedisHelper, LOG, WX
import os

os.system("title 后台--WEBSOCKET服务")  # 修改命令行的显示标题
logger = LOG.end()

ids = set()  # flash.id列表
sensor_dt = {}
sdt = {}
sensor_CD = {}
# sensor_CD = {"123":{"wet":"1","tem":"2","id":"3","time":"4","gateway":5},
#              "125":{"wet":"1","tem":"2","id":"3","time":"4","gateway":5},
#              }  # 所有的网关

flag = False
video_data = ""  # 视频字节流
video_dt = {}
video_CD = {}


# 处理数据
# 接受摄像头监控的数据以及mac地址
def sub_video():
    obj = RedisHelper()
    redis_sub = obj.subscribe_video()  # 调用订阅方法
    global sensor_dt
    while True:
        data_byte = redis_sub.parse_response()[2]
        try:
            data = json.loads(data_byte.decode())
            # logger.info(data)
            s_img = "data:image/jpeg;base64," + data["img"]
            logger.info("base64 编码图片流")
            # logger.info(s_img)
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.debug("摄像头监控订阅者得到消息：{}   {}".format("", current_time))
            video_dt["video"] = s_img
            video_dt["id"] = data["id"]  # 传感器的Flash_id//
            video_dt["time"] = current_time

            id = data["id"]
            ids = video_CD.keys()
            if id in ids:
                video_CD[id] = dict(video_CD[id], **video_dt)
                # logger.info("该视频监控已存在：{}".format(video_CD[id]))
            else:
                video_num = len(ids)  # 集合转化为列表
                gw_name = "视频监控" + str(video_num + 1)
                logger.info("接入的第{}个摄像头监控{}".format(video_num + 1, gw_name))
                video_CD[id] = dict(video_dt, **{"gateway": gw_name})

        except Exception as e:
            logger.debug("*********************************")
            logger.debug("摄像头监控订阅者遇到错误：{}".format(e))
            logger.debug("*********************************")


# 微信报警  温度高于39度
def CallWX(tem):
    message = '''
    报警测试
    您室内温度--{}
    请注意降温防暑
    author：squirrel
    '''.format(tem)
    if int(tem) > 39:
        result = WX().CALL(message)
        flag = result['rawmsg']
        logger.info("微信报警：{}".format(flag))


def sub():
    obj = RedisHelper()
    redis_sub = obj.subscribe()  # 调用订阅方法
    global sensor_dt
    while True:
        msg = redis_sub.parse_response()[2]
        logger.info(msg)
        try:
            message = json.loads(msg.decode("utf8"))
            logger.debug(type(message))
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.debug("订阅者得到消息：{}   {}".format(message, current_time))
            # 解析数据
            sensor_dt["tem"] = message[0]
            sensor_dt["wet"] = message[1]
            sensor_dt["id"] = message[2]  # 传感器的Flash_id
            sensor_dt["time"] = current_time
            # sensor_dt["gateway"] = ""

            # 加入微信报警   ---HT 2018.3.2
            # CallWX(message[0])

            # 待完善
            # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
            if len(message) > 3:
                sensor_dt["ph"] = message[3]
                sensor_dt["voc"] = message[4]
            else:
                sensor_dt["ph"] = "未传入"
                sensor_dt["voc"] = "未传入"
            # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

            id = message[2]
            ids = sensor_CD.keys()
            if id in ids:
                sensor_CD[id] = dict(sensor_CD[id], **sensor_dt)
                logger.info("该传感器已存在：{}".format(sensor_CD[id]))
            else:
                sensor_num = len(ids)  # 集合转化为列表
                gw_name = "GATEWAY" + str(sensor_num + 1)
                logger.info("接入的第{}个传感器:{}".format(sensor_num + 1, gw_name))
                sensor_CD[id] = dict(sensor_dt, **{"gateway": gw_name})

        except Exception as e:
            logger.debug("*********************************")
            logger.debug("原始数据：{}".format(msg))
            logger.debug("订阅者遇到错误：{}".format(e))
            logger.debug("*********************************")


def check_key(json_data):
    key = json.loads(json_data)
    if key["key"] == "rinpo":
        return True
    return False


async def hello(websocket, path):
    while True:
        # logger.debug("websokcet服务端发送的数据:{}".format(sensor_dt))
        sensor_LS = [sensor for sensor in sensor_CD.values()]  # 数据格式转换 转换为
        # 修改数据格式
        video_LS = [video for video in video_CD.values()]
        # logger.info("监控列表")
        # logger.info(video_LS)
        # info = {"sensors": sensor_LS, "videos": video_LS}
        info = {"sensors": sensor_LS}
        # info = {"videos": video_LS}
        logger.info("发送的数据")
        logger.info(info)
        data_json = json.dumps(info, ensure_ascii=False)  # 修改为发送网关列表
        await websocket.send(data_json)

        logger.debug(">>>发送数据 {}".format(data_json))
        await asyncio.sleep(5)


if __name__ == "__main__":
    t1 = threading.Thread(target=sub)
    t1.start()
    # t2 = threading.Thread(target=sub_video())
    # t2.start()
    start_server = websockets.serve(hello, '0.0.0.0', 9999)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
