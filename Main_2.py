# 理念测试文件

# pyqt
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from resource.jiemian import Ui_Form
# mysql
import pymysql
#
import cv2
import copy
import datetime
import numpy as np
import time
import math
import operator
from functools import reduce
from PIL import Image  # pillow
from io import BytesIO

# 项目用 aip
from aip import AipBodyAnalysis


class Window(QWidget, Ui_Form):
    pb_s_click = pyqtSignal()
    pb_m_click = pyqtSignal(str)
    pb_e_click = pyqtSignal()
    pb_w_click = pyqtSignal()

    def __init__(self):
        super().__init__()
        # self.setWindowTitle("")      # 默认窗口设置
        self.setGeometry(300, 300, 350, 350)
        self.setupUi(self)
        self.init_tablewidget()
        # self.lineEdit.setText('乘坐电梯综合视频.mp4')
        self.init_end = False
        self.person = 0
        self.thread1 = None
        self.thread2 = None
        self.thread3 = None

    def init_tablewidget(self):
        self.tableWidget.clear()
        row = self.tableWidget.rowCount()
        for r in range(row):
            self.tableWidget.removeRow(0)
        col_list = ['id', 'time', 'status']
        # self.tableWidget.setRowCount(1)
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setHorizontalHeaderLabels(col_list)

    # -------------------------------分割线------以下是 控件 信号处理
    def le_url(self, url):
        # 视频地址 文本框
        # url 可以为 0，1 or mp4, rtsp,rtmp,http    opencv支持的流媒体网址
        self.url = url
        if len(url) > 0:
            # 假设 url 有效
            self.pushButton.setEnabled(True)
        else:
            self.init_end = True
            self.label_5.setPixmap(QPixmap(''))
            self.lineEdit_2.clear()
            self.lineEdit_2.setStyleSheet('')
            self.lineEdit_3.clear()
            self.lineEdit_3.setStyleSheet('')
            self.lineEdit_4.clear()
            self.lineEdit_4.setStyleSheet('')
            self.init_tablewidget()
        pass

    def pb_start(self):
        # 打开视频 按钮
        # print('pb_start', self.url)
        if self.pushButton.isEnabled() :
            self.pushButton_3.setEnabled(True)  # renshu
            self.pushButton_4.setEnabled(True)  # error
            self.pushButton_2.setEnabled(True)  # wupin
            self.lineEdit_2.setText('None')
            self.lineEdit_2.setStyleSheet('')
            self.lineEdit_3.setText('None')
            self.lineEdit_3.setStyleSheet('')
            self.lineEdit_4.setText('None')
            self.lineEdit_4.setStyleSheet('')
            self.init_tablewidget()
        self.pb_s_click.emit()      # 信号 启动视频
        pass

    def person_window(self, max):
        # 人数检测按钮触发后的 设置ui控件样式
        self.lineEdit_2.setText(str(max))
        self.lineEdit_2.setStyleSheet('color: cyan;')

    def pb_man(self):
        # self.pb_m_click.emit(self.url)      # 信号 人数检测
        self.thread1 = myThread(status='person', url=self.url)
        self.thread1.start()
        self.thread1.person_out.connect(self.person_window)
        pass

    def error_window(self, Alert):
        # 异常行为检测 按钮触发后的 设置ui控件样式
        if len(Alert) > 0:
            self.lineEdit_3.setText(str(Alert[-1]))
            self.lineEdit_3.setStyleSheet('color: red;')
            for i, item in enumerate(Alert):
                row = self.tableWidget.rowCount()
                col = self.tableWidget.colorCount()
                self.tableWidget.insertRow(row)
                self.tableWidget.setItem(row, 0, QTableWidgetItem(str(row + 1)))
                self.tableWidget.setItem(row, 1, QTableWidgetItem(str(item)))
                self.tableWidget.setItem(row, 2, QTableWidgetItem('出现异常行为'))

    def pb_error(self):
        # self.pb_e_click.emit()        # 信号
        self.thread2 = myThread(status='error', url=self.url)
        self.thread2.start()
        self.thread2.person_out.connect(self.person_window)
        self.thread2.error_out.connect(self.error_window)
        pass

    def wupin_window(self, A):
        # 物品遗留检测 按钮触发后的 设置ui控件样式
        if A:
            self.lineEdit_4.setText('YES!')
            self.lineEdit_4.setStyleSheet('background: red;')
        else:
            self.lineEdit_4.setText('None')
            self.lineEdit_4.setStyleSheet('')

    def pb_wupin(self):          # 物品检测 按钮
        # self.pb_w_click.emit()      # 信号 物品检测
        self.thread3 = myThread(status='wupin', url=self.url)
        self.thread3.start()
        self.thread3.wupin_out.connect(self.wupin_window)
        pass

    # -------------------------------分割线------以下是 数据处理 具体程序
    def video_show(self):

        print("-----开始 读取视频-----")
        self.init_end = False
        # print('signal', self.url)
        if self.url == '0':     #
            cap = cv2.VideoCapture(0)
        elif self.url == '1':
            cap = cv2.VideoCapture(1)
        else:
            try:
                cap = cv2.VideoCapture(self.url)
            except:
                QMessageBox.about(self, '警告！', 'url路径无效\n url 可以为 0,1 or mp4, rtsp,rtmp,http\n opencv支持的流媒体网址')
        frames_num = cap.get(7)
        # print(frames_num)
        fps = cap.get(cv2.CAP_PROP_FPS)
        print(f'fps: {fps}')
        ret, frame = cap.read()
        while ret:
            frame = cv2.flip(frame, 1)
            # # opencv 默认图像格式是rgb qimage要使用BRG,这里进行格式转换,不用这个的话,图像就变色了,困扰了半天,翻了一堆资料
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            if len(global_frame) == 2:
                global_frame.remove(global_frame[0])
            else:
                global_frame.append(frame)

            frame = cv2.resize(frame, dsize=(240, 180))      # 可以获取label 大小
            # # mat-->qimage
            img = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            self.label_5.setPixmap(QPixmap.fromImage(img))

            ret, frame = cap.read()
            cv2.waitKey(int(1000 / fps) + 20)
            if not self.init_end:
                continue
            else:
                break
        else:
            print("-----结束 视频-----")
        pass

    def person_num(self):
        print("-----开始 人数检测-----")
        # 乘坐电梯.mp4
        # 测试， 暂时测 5帧
        num = []
        for i in range(5):  # 采集的总帧数
            # frame = self.frame
            # ret, frame = self.cap.read()
            frame = copy.deepcopy(global_frame[-1])
            # frame = global_frame[0]
            # print(frame)
            ret, buf = cv2.imencode(".jpg", frame)       #
            del frame
            image_b = Image.fromarray(np.uint8(buf)).tobytes()
            try:
                fan = client.bodyNum(image_b)
                num.append(fan['person_num'])
                max = int(np.max(num))
            except Exception as e:
                # print(e)
                continue
        print('电梯中人数为', format(max))
        # -----mysql
        sql0 = "select * from test_list order by id desc limit 1;"
        cur.execute(sql0)
        row_last = cur.fetchall()
        if len(row_last) == 0:
            id = 0
        else:
            id = int(row_last[0][0])

        sql = "insert into test_list (id, person_num, time) values (%s, %s, %s)"
        now_time = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        cur.execute(sql, (id + 1, max, now_time))
        db.commit()
        # ------------
        if max == 0:
            print('0')
            self.pb_w_click.emit()
        print("-----结束 人数检测-----")
        return int(max)
        pass

    def error_find(self):
        print('-----开始 异常行为检测-----')
        # 效果差
        # 计算判断值v,w
        def flow_value(pre, now):
            size = (180, 240)
            flow = cv2.calcOpticalFlowFarneback(pre, now, None, 0.5, 3, 30, 3, 5, 1.2, 0)
            v = np.zeros(size)
            w = np.zeros(size)
            for i in range(flow.shape[0]):
                for j in range(flow.shape[1]):
                    if flow[i, j, 0] * flow[i, j, 1] > 5:  # 删掉部分小移动
                        try:        # 出错
                            v[i, j] = flow[i, j, 0] ** 2 + flow[i, j, 1] ** 2
                            w[i, j] = np.arctan(flow[i, j, 1] / flow[i, j, 0]) / 3.14
                        except Exception as e:
                            # print(e)
                            continue
            E = int(sum(sum(w * v)))
            return E

        count = []
        Alert = []
        # ret1, frame1 = self.cap.read()
        frame1 = copy.deepcopy(global_frame[0])
        for i in range(61):     # 采集的总帧数
            # time.sleep(1)     #
            frame2 = copy.deepcopy(global_frame[-1])
            img_pre = cv2.cvtColor(frame1, cv2.COLOR_RGB2GRAY)
            img_now = cv2.cvtColor(frame2, cv2.COLOR_RGB2GRAY)
            img_pre = cv2.resize(img_pre, dsize=(180, 240))
            img_now = cv2.resize(img_now, dsize=(180, 240))
            flow = flow_value(img_pre, img_now)
            del frame1
            frame1 = frame2
            if flow > 5000:
                count.append(1)
            else:
                count.append(0)

            if i > 13:
                if sum(count[i-11:i]) >= 6:
                    now_time = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    if len(Alert) > 0:
                        if now_time == Alert[-1]:
                            continue
                        else:
                            print('警报，有异常！时间为：%s'%now_time)   # 系统时间
                            Alert.append(now_time)  # 系统时间
                    else:
                        print('警报，有异常！时间为：%s' % now_time)  # 系统时间
                        Alert.append(now_time)  # 系统时间
        # -----mysql
        sql0 = "select * from test_list order by id desc limit 1;"
        cur.execute(sql0)
        row_last = cur.fetchall()
        if len(row_last) == 0:
            id = 0
        else:
            id = int(row_last[0][0])

        if len(Alert) > 0:
            now_time = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            sql = f"update test_list set error_start='{Alert[0]}', error_end='{Alert[-1]}', time='{now_time}' where id='{id}'"
            cur.execute(sql)
        db.commit()
        # ------------

        print(count)

        # print(Alert)
        print("-----结束 异常行为检测-----")
        return Alert
        pass

    def wupin_find(self):
        print('-----开始 物品遗留检测-----')
        img = []
        for i in range(10): # 采集总帧数 10
            print(i, end='..')
            img.append(copy.deepcopy(global_frame[0]))
            time.sleep(1)   # 时停 3s

        # 定义计算直方图差别函数
        def image_contrast(path1, path2):
            h1 = cv2.calcHist([path1], [0], None, [256], [0, 255])
            h2 = cv2.calcHist([path2], [0], None, [256], [0, 255])
            result = np.int(math.sqrt(reduce(operator.add, list(map(lambda a, b: (a - b) ** 2, h1, h2))) / len(h1)))
            return result

        delt_num = []
        for i in range(len(img)):
            path1 = img[i]
            path2 = img[-1]
            delt = image_contrast(path1, path2)
            delt_num.append(delt)

        print(delt_num)

        if np.mean(delt_num) < 2000:
            print('电梯空载，开始检查是否有物品遗留！')
            # 判定是否有物品遗留
            def image_delt(path1, path2, thr):
                img_0 = path1
                img_0 = img_0.astype(float)
                img_1 = path2
                img_1 = img_1.astype(float)
                delt = abs(img_0 - img_1)
                f = delt > thr
                diff = np.multiply(delt, f)
                return diff

            path1 = cv2.imread('kong.jpg', 0)       # 直接与空图作比较
            # ret, frame = self.cap.read()
            frame = copy.deepcopy(global_frame[-1])
            path2 = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            del frame
            path2 = cv2.resize(path2, dsize=(240, 180))
            delt = sum(sum(image_delt(path1, path2, 50)))
            # ------------mysql
            sql0 = "select * from test_list order by id desc limit 1;"
            cur.execute(sql0)
            row_last = cur.fetchall()
            if len(row_last) == 0:
                id = 0
            else:
                id = int(row_last[0][0])

            sql = "insert into test_list (id, wupin, time) values (%s,%s,%s)"
            now_time = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            # -------------
            A = False
            if delt > 240 * 180 * 1:
                print('有物品遗留，请调查视频！')
                A = True
                # -----mysql
                cur.execute(sql, (id+1, 'yes', now_time))
                db.commit()
                # ------------
            else:
                print('无物品遗留，电梯已清空！')
                # -----mysql
                cur.execute(sql, ('no', now_time))
                db.commit()
                # ------------

            print('-----结束 物品遗留检测-----')
            return A
        else:
            print('电梯未空载，不能进行遗留物判定！')
            print('-----结束 物品遗留检测-----')
            A = False
            return A
        pass

    def wl(self):
        for i in range(61):
            time.sleep(1)
            print(self.url)

class myThread(QThread):
    person_out = pyqtSignal(int)
    error_out = pyqtSignal(list)
    wupin_out = pyqtSignal(bool)

    def __init__(self, status, url):
        super(myThread, self).__init__()
        self.my_ui = Window()
        self.status = status
        self.url = url

    def run(self):
        if self.status == 'person':     # 人数检测
            print('开始线程', self.status)
            max = self.my_ui.person_num()
            self.person_out.emit(max)
            print('结束线程', self.status)

        elif self.status == 'error':    # 异常检测
            print('开始线程', self.status)
            max = self.my_ui.person_num()
            Alert =  self.my_ui.error_find()
            self.person_out.emit(max)
            self.error_out.emit(Alert)
            print('结束线程', self.status)

        elif self.status == 'wupin':    # 物品遗留检测
            print('开始线程', self.status)
            A = self.my_ui.wupin_find()
            self.wupin_out.emit(A)
            print('结束线程', self.status)


if __name__ == '__main__':

    """ 你的 APPID AK SK """
    APP_ID = '17741063'
    API_KEY = 'ibeFmMDI5mtfVGYtucQ3LcXi'
    SECRET_KEY = '0tdbttKFnZPBaLYEhPIkvQ9yG8Vckvk5'
    client = AipBodyAnalysis(APP_ID, API_KEY, SECRET_KEY)

    # ---------------mysql
    db = pymysql.connect(host='101.200.48.138', user='nick', password='mysql', database='test', charset='utf8')
    cur = db.cursor()
    # ------------------

    # 缓存 frame  全局变量
    global_frame = []
    # 
    app = QApplication(sys.argv)  # sys.argv 反馈窗口输入
    window = Window()
    window.show()               # 窗口显示

    window.pb_s_click.connect(window.video_show)    # 连接 def
    window.pb_m_click.connect(window.person_num)
    window.pb_e_click.connect(window.error_find)
    window.pb_w_click.connect(window.wupin_find)

    sys.exit(app.exec_())  # app.exec_() 保持窗口刷新 sys.exit反馈错误类型
