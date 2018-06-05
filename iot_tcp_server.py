import socket
import asyncio
import websockets
import threading
import json
import datetime, time
from config import RedisHelper, LOG
import os

os.system("title 中间件---TCP服务")  # 修改命令行的显示标题
current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

obj = RedisHelper()
logger = LOG.middle()

# 数据结构
'''
{ "ip":{""} }

网关：发送数据
中间件：加入ip地址，但是是否属于同一个网关的还是需要在网关添加网关信息
'''


def server_socket(conn, addr):
    logger.debug("接入客户端的ip地址：{}".format(addr))
    while 1:
        res = conn.recv(100000)
        recv_json = res.decode()
        if not len(res):
            conn.close()

        logger.debug("当前时间：{}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        logger.debug("TcpServer接收到的数据：{}".format(recv_json))
        # print(type(recv_json))
        # print(recv_json)
        try:
            recv = json.loads(recv_json)
            print(type(recv))
            if isinstance(recv, dict):
                try:
                    logger.debug("摄像头数据")
                    logger.debug(recv)

                    obj.publish_video(recv_json)
                    logger.debug("发布者 发布：{}".format(recv_json))
                except Exception as e:
                    logger.warn("ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ")
                    logger.warn("REDIS_SERVER 未开启 ：{}".format(e))
                    logger.warn("ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ")
            else:
                try:
                    logger.info("传感器数据")
                    obj.publish(recv_json)
                    logger.debug("发布者 发布：{}".format(recv_json))
                except Exception as e:
                    logger.warn("ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ")
                    logger.warn("REDIS_SERVER 未开启 ：{}".format(e))
                    logger.warn("ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ")
        except Exception as e:
            print("json解析报错：{}".format(e))
        # todo 加入传感器类型判断  if sensor   if video


def main():
    s = socket.socket()
    s.bind(("0.0.0.0", 9876))
    s.listen(5)
    while 1:
        conn, addr = s.accept()
        t1 = threading.Thread(target=server_socket, args=(conn, addr))
        t1.start()


if __name__ == "__main__":
    main()
