import datetime
import threading
from queue import Queue
import time
import json
from websocket import create_connection
import ssl
import traceback


class WebSocketClient(object):
    def __init__(self,unhandledQueue):
        """地址"""
        self.address = "wss://quotegateway.inquantstudio.com/"
        # 心跳间隔
        self.hbInternal = 5
        # 超时
        self.keepAliveTimeout = 30
        # 心跳内容
        self.hbContent = json.dumps({ 'requestType' : 'HeartBeat','reqID' : '' })

        # websocket
        self.__wsclinet = None
        # 消息队列
        self.__unhandledQueue = unhandledQueue
        # 上次活跃时间
        self.__lastActiveTime = datetime.datetime.now()
        self._hasAutoHeartBeat = False

        # ws 停止标志位
        self.ws_flag = False

        # 接收消息put队列里
        self.t1 = threading.Thread(target=self._ReceiveMsg)
        self.t1.start()


    def Connect(self):
        """连接"""
        if self.IsAvaliable():
            return True

        self.__wsclinet = create_connection(self.address, sslopt={"cert_reqs": ssl.CERT_NONE})
        print('{}  {}  websocket连接成功！'.format(self.address,self.__wsclinet.connected))  # True False

        self.ws_flag = True
        self.__lastActiveTime = datetime.datetime.now()
        return True


    def AutoHeartBeat(self):
        """启动自动心跳功能"""
        if self._hasAutoHeartBeat:
            return
        self._hasAutoHeartBeat = True
        self.t2 = threading.Thread(target=self.__AutoHeartBeat)
        self.t2.start()


    def IsAvaliable(self):
        """判断是否是有效连接"""
        if not self.__wsclinet:
            return False
        if not self.__wsclinet.connected:
            return False
        if (datetime.datetime.now() - self.__lastActiveTime).seconds > self.keepAliveTimeout:
            return False
        return True


    def Send(self, content):
        """发送消息"""
        if not content:
            return None
        if not self.IsAvaliable():
            return None
        data = bytes(content, encoding="utf8")
        return self.__wsclinet.send(data)


    def _ReceiveMsg(self):
        """接收消息"""
        while True:
            # print(str(datetime.datetime.now()) + ' put消息。。。。')
            try:
                if self.ws_flag:
                    if not self.IsAvaliable():
                        time.sleep(1)
                        continue
                    msg = self.__wsclinet.recv()
                    self.__lastActiveTime = datetime.datetime.now()
                    self.__unhandledQueue.put(msg)
                else:
                    pass
            except:
                print(traceback.format_exc())
                time.sleep(1)
            time.sleep(0.1)


    def __AutoHeartBeat(self):
        """心跳"""
        if not self.hbContent:  # 心跳内容
            return

        while True:
            # 心跳间隔
            time.sleep(self.hbInternal)
            # print(str(datetime.datetime.now()) + ' 心跳。。。。')
            try:
                # 如果ws标志位为True
                if self.ws_flag:
                    if not self.IsAvaliable():
                        self._Close()
                        self.Connect()
                    self.Send(self.hbContent)  # 心跳内容
                else:
                    pass
            except:
                print(traceback.format_exc())
                self._Close()


    def _Close(self):
        try:
            if self.__wsclinet:
                self.__wsclinet.close()
            self.__wsclinet = None
            self.ws_flag = False
        except:
            print(traceback.format_exc())








