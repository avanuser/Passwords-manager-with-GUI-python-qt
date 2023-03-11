# This is a Qt Passwords Manager
# v1.0

from PySide2.QtWidgets import *
from PySide2.QtCore import Qt
from PySide2.QtGui import QClipboard
from Cryptodome.Cipher import AES
import sys, threading, time
import hashlib
from ctypes import windll

###############################################################

win_title = 'Passwords\' manager'

window_min_height = 150
window_min_width = 300

label_style = """
              vertical-align: middle;
              color: #555555;
              font-size: 12px;
              """

spec = '!'    # special symbols one of which will be included in generated passwords
len_min = 10    # minimal length of generated passwords
len_max = 18    # maximum length of generated passwords

###############################################################


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(win_title)
        self.statusBar().showMessage('Welcome!')
        # create menu
        main_menu = self.menuBar()
        file_menu = main_menu.addMenu("File")
        file_menu.addAction("Open file")
        file_menu.triggered[QAction].connect(self.file_open)   # incorrect?
        # central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.vbox = QVBoxLayout(self.central_widget)
        h1_box = QHBoxLayout()
        h2_box = QHBoxLayout()
        self.vbox.addLayout(h1_box)
        self.vbox.addLayout(h2_box)
        # create info label and fields (h1_box)
        self.status = QLabel('READY')
        self.status.setStyleSheet('color: green;')
        self.info2_label = QLabel(' '*20)
        self.info2_label.setAlignment(Qt.AlignCenter)
        self.info3_label = QLabel('')
        self.info3_label.setAlignment(Qt.AlignCenter)
        self.counter = QLCDNumber()
        self.counter.setDigitCount(2)
        self.counter.setMinimumSize(40, 40)
        # self.counter.setAlignment(Qt.AlignCenter)
        self.counter.setStyleSheet('color: red;')
        # create master key label and field (h2_box)
        self.key_label = QLabel('Master key:')
        self.key_label.setStyleSheet(label_style)
        self.key = QLineEdit()
        self.key.setAlignment(Qt.AlignCenter)
        self.key.setEchoMode(QLineEdit.Password)
        # 
        h1_box.addWidget(self.status)
        h1_box.addWidget(self.info2_label)
        h1_box.addWidget(self.info3_label)
        h1_box.addWidget(self.counter)
        #
        h2_box.addWidget(self.key_label)
        h2_box.addWidget(self.key)
        #
        # vbox.addWidget(self.term)
        #
        self.calc_en = 1    # used to lock (TBD)
        self.btns_list = []
        self.spec = spec
        self.len_min = len_min
        self.len_max = len_max

    def btn_pressed(self):
        if self.key.text():
            btn = self.sender()      # get object created received signal
            btn_name = btn.text()    # name of the button
            for item in self.btns_list:
                if item[0] == btn_name:
                    self.login = item[1]
                    self.service = item[2]
                    self.clipboard = QClipboard()
                    self.clipboard.setText(self.login)    # copy login to clipboard
                    self.clipboard.deleteLater()
            self.create_msg_box()
        else:
            self.status.setStyleSheet('color: red;')
            self.status.setText('Master key is empty!')

    def create_msg_box(self):
        msg_box = QMessageBox()
        msg_box.setText("Please copy login now")
        msg_box.setIcon(QMessageBox.Information)
        msg_box.exec()
        if msg_box.clickedButton():
            self.msg_box_ok()

    def msg_box_ok(self):
        seed = self.key.text() + self.login + self.service
        self.calc_pass(seed, self.spec)
        t1 = threading.Thread(target=self.timer)
        t1.start()

    def timer(self):
        self.disable_widgets(QPushButton)
        self.disable_widgets(QLineEdit)
        n = 10
        while(n >= 0):
            self.counter.display(n)
            time.sleep(1)
            n = n - 1
        self.clear()

    def clear(self):
        if windll.user32.OpenClipboard(None):
            windll.user32.EmptyClipboard()
            windll.user32.CloseClipboard()
            self.status.setStyleSheet('color: green;')
            self.status.setText('READY')
            self.info2_label.setText('')
            self.info3_label.setText('')
        else:
            self.status.setStyleSheet('color: red;')
            self.status.setText('Filed to clear clipboard!')
            self.info2_label.setText('')
            self.info3_label.setText('')
        self.key.setText('')    # erase master key
        self.enable_widgets(QPushButton)    # enable buttons
        self.enable_widgets(QLineEdit)    # enable fields QLineEdit

    def enable_widgets(self, w_type):
        kids = self.findChildren(w_type)
        for item in kids:
            item.setEnabled(True)

    def disable_widgets(self, w_type):
        kids = self.findChildren(w_type)
        for item in kids:
            item.setEnabled(False)

    def calc_pass(self, msg, sps):    # sps - string of special symbols
        if (self.calc_en and msg):
            n = 0
            # self.calc_en = 0
            while (n < 100000):
                alphaOK = 0
                digitOK = 0
                if (sps):
                    specOK = 0
                else:
                    specOK = 1
                n = n + 1
                m1 = bytes(msg, 'utf-8')
                m2 = hashlib.sha512(m1).digest()       # get digest
                m3 = ''
                for i in range(len(m2)):
                    x = ord(m2[i:i+1])
                    if (0x20 < x < 0x7F):
                        m3 = m3 + m2[i:i+1].decode('utf-8')
                m4 = ''
                for i in range(len(m3)):
                    if (m3[i:i+1].isalpha()):
                        m4 = m4 + m3[i:i+1]
                        alphaOK = 1                        # at least 1 alpha in the message
                    elif (m3[i:i+1].isdigit()):
                        m4 = m4 + m3[i:i+1]
                        digitOK = 1                        # at least 1 digit in the message
                    elif (m3[i:i+1] in list(sps)):
                        m4 = m4 + m3[i:i+1]
                        specOK = 1                         # at least 1 special symbol in the message
                if (alphaOK and digitOK and specOK and (self.len_min <= len(m4) <= self.len_max)):     # exit the loop if there are letters, digits, spec symbols in the message and its length is OK
                    break
                else:
                    msg = m4
            self.clipboard = QClipboard()
            self.clipboard.setText(m4)
            self.clipboard.deleteLater()
            self.status.setStyleSheet('color: green;')
            self.status.setText('SUCCESS')
            self.info2_label.setStyleSheet('color: green;')
            self.info2_label.setText('Length: '+ str(len(m4)))
            self.info3_label.setText('Iterations: '+ str(n))

    def closeEvent(self, event):
        if windll.user32.OpenClipboard(None):
            windll.user32.EmptyClipboard()    # empty clipboard before closing app
            windll.user32.CloseClipboard()
        event.accept()

    def file_open(self):
        kids = self.findChildren(QPushButton)
        for kid in kids:
            kid.deleteLater()   # delete 'old' buttons if any
        name = QFileDialog.getOpenFileName(self, 'Open')
        f_name = name[0]    # name of file to open (to parse)
        f_data = self.read_from_file(f_name)
        self.btns_list = self.convert_data(f_data)
        for item in self.btns_list:
            if len(item)>2:
                btn = QPushButton(item[0])
                self.vbox.addWidget(btn)
                btn.clicked.connect(self.btn_pressed)
    
    def read_from_file(self, filename):
        try:
            File = open(filename, 'r')
            data = File.read()
            File.close()
        except Exception:
            data = None
        return data

    def convert_data(self, data):
        new_data = []
        data = data.replace('\r', '\n')    # replace '\r' with '\n'
        data_list = data.split('\n')    # split data using separator '\n'
        for line in data_list:
            if len(line):
                line = line.split(';')
                new_data.append(line)
        return new_data


def main():
    app = QApplication([])
    main_win = MainWindow()
    main_win.resize(window_min_width, window_min_height)
    main_win.show()
    # sys.exit(app.exec())  # PySide6
    sys.exit(app.exec_())  # PySide2


if __name__ == '__main__':
    main()
