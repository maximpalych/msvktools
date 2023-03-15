import ftplib
import logging
import math
import os
import random
import re
import shutil
import subprocess
import threading
import time
import tkinter as tk
import uuid
from datetime import datetime
from tabulate import tabulate
from colorama import init, Fore, Back, Style

import arrow
import paramiko
import shortuuid
from pyfiglet import Figlet

VERSION = 'v28.12'

BG_COLOR = '#3D3D3D'
SELECT_COLOR = '#28b463'
TXT_COLOR = '#FAE5D3'
TXT_SELECT_COLOR = '#000000'

UNIQ_SN = '#FFD700'
PIRATE_SN = '#228B22'
NOT_CONNECT = '#FF4500'
TXT_BLACK_COLOR = '#000000'

init(autoreset=True)

KEK_SN = '1423219080397'
BUTTON_STATE = {}
for button_number in range(10, 30):
    BUTTON_STATE[f'b_{button_number}'] = False
SSH_LOGIN = "user"
SSH_PWD = "synergo2020"
SSH_PORT = 22
SSH_MIKROTIK_PORT = 25
TIME_OUT = 3
LOCAL_PATH = (os.getcwd()).replace('\\', '/')
KEYCATALOG = (os.path.join(os.getcwd(), 'keycatalog')).replace('\\', '/')
TICKETS = '/opt/AxxonSoft/AxxonNext/Tickets/'
PATH = r'/opt/AxxonSoft/AxxonNext/instance.conf'
BASE_PORT = 20111  # Base port ноды
LICENSE_TYPE = 13  # Universe
COMPLETED_HOST = 0

CNT_N = 0
CNT_P = 0
CNT_U = 0

logging.getLogger("paramiko").setLevel(logging.WARNING)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', '%Y-%m-%d %H:%M:%S')


def setup_logger(name, log_file, level=logging.INFO):
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger


nodeNamesLog = setup_logger('nodeNamesLog', 'getNodeNames.log')
synergoTool = setup_logger('synergoTool', 'synergoTool.log')


def _create_default_directories(default_directory):
    if not os.path.exists(default_directory):
        try:
            if os.makedirs(default_directory):
                return True
            else:
                return False
        except Exception as ex:
            synergoTool.error(str(ex))
            return False
    else:
        return True
        # synergoTool.info('Catalog already exists.')


if not _create_default_directories(KEYCATALOG):
    synergoTool.error('Catalog cannot be created ' + KEYCATALOG)


def counting_status():
    global CNT_N, CNT_U, CNT_P
    CNT_N = 0
    CNT_U = 0
    CNT_P = 0
    for label_number in range(10, 30):
        if getattr(m_window, f'l_{label_number}').cget('text') == 'N':
            CNT_N += 1
        elif getattr(m_window, f'l_{label_number}').cget('text') == 'U':
            CNT_U += 1
        elif getattr(m_window, f'l_{label_number}').cget('text') == 'P':
            CNT_P += 1
    getattr(m_window, f'cnt_n_t').configure(text=f': {CNT_N}')
    getattr(m_window, f'cnt_u_t').configure(text=f': {CNT_U}')
    getattr(m_window, f'cnt_p_t').configure(text=f': {CNT_P}')


def setFontColor(string, color):
    text = ''
    if color == 'YELLOW':
        text = Fore.YELLOW + string + Fore.RESET
    if color == 'RED':
        text = Fore.RED + string + Fore.RESET
    if color == 'GREEN':
        text = Fore.GREEN + string + Fore.RESET
    if color == 'CYAN':
        text = Fore.CYAN + string + Fore.RESET
    if color == 'MAGENTA':
        text = Fore.MAGENTA + string + Fore.RESET
    return text


class StartThread:
    def __init__(self, name, target, *args):
        self.name = name
        self.target = target
        self.args = args
        thread = threading.Thread(target=self.target, name=self.name, args=self.args)
        self.thread = thread
        thread.start()


class MainWindow:
    def __init__(self, parent):
        self.parent = parent
        self.parent.title(f'MSVKTOOL {VERSION}')
        # self.parent.wm_attributes('-topmost', True)
        screen_width = self.parent.winfo_screenwidth() // 2
        screen_height = self.parent.winfo_screenheight() // 3
        self.parent.geometry('+{}+{}'.format(screen_width, screen_height))
        self.parent.resizable(False, False)

        # self.parent.attributes('-toolwindow', True)

        def button_press(pressed_button):
            if not BUTTON_STATE[pressed_button]:
                BUTTON_STATE[pressed_button] = True
                getattr(m_window, f'{pressed_button}').configure(bg=SELECT_COLOR)
                getattr(m_window, f'{pressed_button}').configure(activebackground=SELECT_COLOR)
                getattr(m_window, f'{pressed_button}').configure(fg=TXT_SELECT_COLOR)
            else:
                BUTTON_STATE[pressed_button] = False
                getattr(m_window, f'{pressed_button}').configure(bg=BG_COLOR)
                getattr(m_window, f'{pressed_button}').configure(activebackground=BG_COLOR)
                getattr(m_window, f'{pressed_button}').configure(fg=TXT_COLOR)

        def cAll():
            for b_number in range(10, 30):
                pressed_button = f'b_{b_number}'
                if BUTTON_STATE[pressed_button]:
                    BUTTON_STATE[pressed_button] = False
                button_press(pressed_button)

        def unAll():
            for b_number in range(10, 30):
                pressed_button = f'b_{b_number}'
                if not BUTTON_STATE[pressed_button]:
                    BUTTON_STATE[pressed_button] = True
                button_press(pressed_button)

        def button_selection(pressed_label):
            pressed_text = getattr(m_window, f'{pressed_label}').cget('text')
            unAll()
            for label_number in range(10, 30):
                text = getattr(m_window, f'l_{label_number}').cget('text')
                if pressed_text == text:
                    BUTTON_STATE[f'b_{label_number}'] = True
                    getattr(m_window, f'b_{label_number}').configure(bg=SELECT_COLOR)
                    getattr(m_window, f'b_{label_number}').configure(activebackground=SELECT_COLOR)
                    getattr(m_window, f'b_{label_number}').configure(fg=TXT_SELECT_COLOR)

        def reset_status():
            for status_number in range(10, 30):
                getattr(m_window, f'l_{status_number}').configure(bg=BG_COLOR)
                getattr(m_window, f'l_{status_number}').configure(text='  ')
            counting_status()

        def cnt_buttons_flash(button):
            if button == 'plus':
                times = int(m_window.b_flashMikrotik88_times['text'])
                times += 1
                m_window.b_flashMikrotik88_times['text'] = str(times)
            if button == 'minus':
                times = int(m_window.b_flashMikrotik88_times['text'])
                if times > 0:
                    times -= 1
                m_window.b_flashMikrotik88_times['text'] = str(times)

        def cnt_buttons_ip(button):
            if button == 'plus':
                times = int(m_window.b_changeIP_times['text'])
                times += 1
                m_window.b_changeIP_times['text'] = str(times)
            if button == 'minus':
                times = int(m_window.b_changeIP_times['text'])
                if times > 0:
                    times -= 1
                m_window.b_changeIP_times['text'] = str(times)

        def set_buttons_ip(button):
            if button == '15':
                m_window.b_changeIP_times['text'] = str(15)
            if button == '19':
                m_window.b_changeIP_times['text'] = str(19)
            if button == '0':
                m_window.b_changeIP_times['text'] = str(0)

        self.main_frame = tk.Frame(parent, bg=BG_COLOR)
        self.main_frame.grid(row=0, column=0)

        self.button_frame = tk.Frame(self.main_frame, bg=BG_COLOR)
        self.button_frame.grid(row=1, column=0)
        self.b_plug = tk.Label(self.main_frame, text='', width=3, bg=BG_COLOR, fg=TXT_COLOR)
        self.b_plug.grid(row=1, column=1, padx=5, pady=5)

        self.cnt_frame = tk.Frame(self.main_frame, bg=BG_COLOR)
        self.cnt_frame.grid(row=0, column=0, padx=5, pady=5)

        self.cnt_n = tk.Label(self.cnt_frame, text=f'N', bg=NOT_CONNECT, fg=TXT_COLOR, width=3)
        self.cnt_n.grid(row=0, column=0, padx=5, pady=1)
        self.cnt_n_t = tk.Label(self.cnt_frame, text=f': {CNT_N}', bg=BG_COLOR, fg=TXT_COLOR)
        self.cnt_n_t.grid(row=0, column=1, padx=5, pady=1)
        self.cnt_p = tk.Label(self.cnt_frame, text=f'P', bg=PIRATE_SN, fg=TXT_COLOR, width=3)
        self.cnt_p.grid(row=0, column=4, padx=5, pady=1)
        self.cnt_p_t = tk.Label(self.cnt_frame, text=f': {CNT_P}', bg=BG_COLOR, fg=TXT_COLOR)
        self.cnt_p_t.grid(row=0, column=5, padx=5, pady=1)
        self.cnt_u = tk.Label(self.cnt_frame, text=f'U', bg=UNIQ_SN, fg=TXT_BLACK_COLOR, width=3)
        self.cnt_u.grid(row=0, column=2, padx=5, pady=1)
        self.cnt_u_t = tk.Label(self.cnt_frame, text=f': {CNT_U}', bg=BG_COLOR, fg=TXT_COLOR)
        self.cnt_u_t.grid(row=0, column=3, padx=5, pady=1)

        self.together_tool_frame = tk.Frame(self.main_frame, bg=BG_COLOR)
        self.together_tool_frame.grid(row=1, column=2, padx=5, pady=5)

        self.axxon_tool_frame = tk.LabelFrame(self.together_tool_frame, bg=BG_COLOR, fg=TXT_COLOR, text='axxonTools')
        self.axxon_tool_frame.grid(row=0, column=0, padx=5, pady=5)

        self.check_tool_frame = tk.Frame(self.axxon_tool_frame, bg=BG_COLOR)
        self.check_tool_frame.grid(row=0, column=0, padx=5, pady=5)

        self.system_tool_frame = tk.LabelFrame(self.together_tool_frame, bg=BG_COLOR, fg=TXT_COLOR, text='systemTools')
        self.system_tool_frame.grid(row=1, column=0, padx=5, pady=5)
        self.b_plug = tk.Label(self.main_frame, text='', width=3, bg=BG_COLOR, fg=TXT_COLOR)
        self.b_plug.grid(row=1, column=3, padx=5, pady=5)

        self.key_tool_frame = tk.Frame(self.main_frame, bg=BG_COLOR)
        self.key_tool_frame.grid(row=1, column=4, padx=5, pady=5)

        self.b_plug = tk.Label(self.main_frame, text='', width=3, bg=BG_COLOR, fg=TXT_COLOR)
        self.b_plug.grid(row=1, column=5, padx=5, pady=5)

        self.tool_frame = tk.Frame(self.main_frame, bg=BG_COLOR)
        self.tool_frame.grid(row=1, column=6, padx=5, pady=5)

        self.b_10 = tk.Button(self.button_frame, text='.10', command=lambda: button_press('b_10'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_10.grid(row=0, column=1, padx=5, pady=5)

        self.l_10 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_10.grid(row=0, column=0, padx=5, pady=5)
        self.l_10.bind("<Button-1>", lambda e: button_selection('l_10'))

        self.b_11 = tk.Button(self.button_frame, text='.11', command=lambda: button_press('b_11'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_11.grid(row=1, column=1, padx=5, pady=5)
        self.l_11 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_11.grid(row=1, column=0, padx=5, pady=5)
        self.l_11.bind("<Button-1>", lambda e: button_selection('l_11'))

        self.b_12 = tk.Button(self.button_frame, text='.12', command=lambda: button_press('b_12'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_12.grid(row=2, column=1, padx=5, pady=5)
        self.l_12 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_12.grid(row=2, column=0, padx=5, pady=5)
        self.l_12.bind("<Button-1>", lambda e: button_selection('l_12'))

        self.b_13 = tk.Button(self.button_frame, text='.13', command=lambda: button_press('b_13'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_13.grid(row=3, column=1, padx=5, pady=5)
        self.l_13 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_13.grid(row=3, column=0, padx=5, pady=5)
        self.l_13.bind("<Button-1>", lambda e: button_selection('l_13'))

        self.b_14 = tk.Button(self.button_frame, text='.14', command=lambda: button_press('b_14'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_14.grid(row=4, column=1, padx=5, pady=5)
        self.l_14 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_14.grid(row=4, column=0, padx=5, pady=5)
        self.l_14.bind("<Button-1>", lambda e: button_selection('l_14'))

        self.b_15 = tk.Button(self.button_frame, text='.15', command=lambda: button_press('b_15'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_15.grid(row=5, column=1, padx=5, pady=5)
        self.l_15 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_15.grid(row=5, column=0, padx=5, pady=5)
        self.l_15.bind("<Button-1>", lambda e: button_selection('l_15'))

        self.b_16 = tk.Button(self.button_frame, text='.16', command=lambda: button_press('b_16'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_16.grid(row=6, column=1, padx=5, pady=5)
        self.l_16 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_16.grid(row=6, column=0, padx=5, pady=5)
        self.l_16.bind("<Button-1>", lambda e: button_selection('l_16'))

        self.b_17 = tk.Button(self.button_frame, text='.17', command=lambda: button_press('b_17'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_17.grid(row=7, column=1, padx=5, pady=5)
        self.l_17 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_17.grid(row=7, column=0, padx=5, pady=5)
        self.l_17.bind("<Button-1>", lambda e: button_selection('l_17'))

        self.b_18 = tk.Button(self.button_frame, text='.18', command=lambda: button_press('b_18'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_18.grid(row=8, column=1, padx=5, pady=5)
        self.l_18 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_18.grid(row=8, column=0, padx=5, pady=5)
        self.l_18.bind("<Button-1>", lambda e: button_selection('l_18'))

        self.b_19 = tk.Button(self.button_frame, text='.19', command=lambda: button_press('b_19'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_19.grid(row=9, column=1, padx=5, pady=5)
        self.l_19 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_19.grid(row=9, column=0, padx=5, pady=5)
        self.l_19.bind("<Button-1>", lambda e: button_selection('l_19'))

        self.b_20 = tk.Button(self.button_frame, text='.20', command=lambda: button_press('b_20'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_20.grid(row=0, column=2, padx=5, pady=5)
        self.l_20 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_20.grid(row=0, column=3, padx=5, pady=5)
        self.l_20.bind("<Button-1>", lambda e: button_selection('l_20'))

        self.b_21 = tk.Button(self.button_frame, text='.21', command=lambda: button_press('b_21'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_21.grid(row=1, column=2, padx=5, pady=5)
        self.l_21 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_21.grid(row=1, column=3, padx=5, pady=5)
        self.l_21.bind("<Button-1>", lambda e: button_selection('l_21'))

        self.b_22 = tk.Button(self.button_frame, text='.22', command=lambda: button_press('b_22'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_22.grid(row=2, column=2, padx=5, pady=5)
        self.l_22 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_22.grid(row=2, column=3, padx=5, pady=5)
        self.l_22.bind("<Button-1>", lambda e: button_selection('l_22'))

        self.b_23 = tk.Button(self.button_frame, text='.23', command=lambda: button_press('b_23'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_23.grid(row=3, column=2, padx=5, pady=5)
        self.l_23 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_23.grid(row=3, column=3, padx=5, pady=5)
        self.l_23.bind("<Button-1>", lambda e: button_selection('l_23'))

        self.b_24 = tk.Button(self.button_frame, text='.24', command=lambda: button_press('b_24'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_24.grid(row=4, column=2, padx=5, pady=5)
        self.l_24 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_24.grid(row=4, column=3, padx=5, pady=5)
        self.l_24.bind("<Button-1>", lambda e: button_selection('l_24'))

        self.b_25 = tk.Button(self.button_frame, text='.25', command=lambda: button_press('b_25'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_25.grid(row=5, column=2, padx=5, pady=5)
        self.l_25 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_25.grid(row=5, column=3, padx=5, pady=5)
        self.l_25.bind("<Button-1>", lambda e: button_selection('l_25'))

        self.b_26 = tk.Button(self.button_frame, text='.26', command=lambda: button_press('b_26'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_26.grid(row=6, column=2, padx=5, pady=5)
        self.l_26 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_26.grid(row=6, column=3, padx=5, pady=5)
        self.l_26.bind("<Button-1>", lambda e: button_selection('l_26'))

        self.b_27 = tk.Button(self.button_frame, text='.27', command=lambda: button_press('b_27'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_27.grid(row=7, column=2, padx=5, pady=5)
        self.l_27 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_27.grid(row=7, column=3, padx=5, pady=5)
        self.l_27.bind("<Button-1>", lambda e: button_selection('l_27'))

        self.b_28 = tk.Button(self.button_frame, text='.28', command=lambda: button_press('b_28'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_28.grid(row=8, column=2, padx=5, pady=5)
        self.l_28 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_28.grid(row=8, column=3, padx=5, pady=5)
        self.l_28.bind("<Button-1>", lambda e: button_selection('l_28'))

        self.b_29 = tk.Button(self.button_frame, text='.29', command=lambda: button_press('b_29'), bg=BG_COLOR,
                              fg=TXT_COLOR, activebackground=BG_COLOR,
                              width='4')
        self.b_29.grid(row=9, column=2, padx=5, pady=5)
        self.l_29 = tk.Label(self.button_frame, text='  ', width=3, bg=BG_COLOR, fg=TXT_BLACK_COLOR)
        self.l_29.grid(row=9, column=3, padx=5, pady=5)
        self.l_29.bind("<Button-1>", lambda e: button_selection('l_29'))

        self.b_plug = tk.Label(self.button_frame, text='', width=3, bg=BG_COLOR, fg=TXT_COLOR)
        self.b_plug.grid(row=10, column=1, padx=5, pady=5)

        self.b_cAll = tk.Button(self.button_frame, text='All', width=4, command=cAll, bg=BG_COLOR, fg=TXT_COLOR,
                                activebackground=BG_COLOR)
        self.b_cAll.grid(row=11, column=1, padx=5, pady=5)

        self.b_unAll = tk.Button(self.button_frame, text='None', command=unAll, bg=BG_COLOR, fg=TXT_COLOR,
                                 activebackground=BG_COLOR)
        self.b_unAll.grid(row=11, column=2, padx=5, pady=5)
        self.b_reset = tk.Button(self.button_frame, text='   RESET   ', command=reset_status, bg=BG_COLOR, fg=TXT_COLOR,
                                 activebackground=BG_COLOR)
        self.b_reset.grid(row=12, column=1, padx=5, pady=5, columnspan=2)

        self.s_fastNodeName_status = tk.IntVar()
        self.c_fastNodeName_status = tk.Checkbutton(self.check_tool_frame, variable=self.s_fastNodeName_status,
                                                    bg=BG_COLOR)
        self.c_fastNodeName_status.grid(row=0, column=0, padx=5, pady=5)

        self.l_fastNodeName = tk.Label(self.check_tool_frame, text='fastNodename', bg=BG_COLOR, fg=TXT_COLOR)
        self.l_fastNodeName.grid(row=0, column=1, padx=5, pady=5)

        self.b_getNodeName = tk.Button(self.axxon_tool_frame, text='getNodeName', width=15, command=thread_getNodeName,
                                       bg=BG_COLOR, fg=TXT_COLOR,
                                       activebackground=SELECT_COLOR)
        self.b_getNodeName.grid(row=1, column=0, padx=5, pady=5)

        self.b_restartAxxon = tk.Button(self.axxon_tool_frame, text='restartAxxon', width=15,
                                        command=thread_restartAxxon, bg=BG_COLOR, fg=TXT_COLOR,
                                        activebackground=SELECT_COLOR)
        self.b_restartAxxon.grid(row=2, column=0, padx=5, pady=5)

        self.b_changeAltAddr = tk.Button(self.axxon_tool_frame, text='changeAltAddr', width=15,
                                         command=thread_changeAltAddr, bg=BG_COLOR, fg=TXT_COLOR,
                                         activebackground=SELECT_COLOR)
        self.b_changeAltAddr.grid(row=3, column=0, padx=5, pady=5)

        self.b_rebootJetson = tk.Button(self.system_tool_frame, text='rebootJetson', width=15,
                                        command=thread_rebootJetson, bg=BG_COLOR, fg=TXT_COLOR,
                                        activebackground=SELECT_COLOR)
        self.b_rebootJetson.grid(row=0, column=0, padx=5, pady=5)

        self.b_startSSH = tk.Button(self.system_tool_frame, text='startSSH', width=15,
                                    command=startSSH, bg=BG_COLOR, fg=TXT_COLOR,
                                    activebackground=SELECT_COLOR)
        self.b_startSSH.grid(row=1, column=0, padx=5, pady=5)

        self.b_resetDHCP = tk.Button(self.system_tool_frame, text='resetDHCP', width=15,
                                     command=resetDHCP, bg=BG_COLOR, fg=TXT_COLOR,
                                     activebackground=SELECT_COLOR)
        self.b_resetDHCP.grid(row=2, column=0, padx=5, pady=5)

        self.b_copyKey = tk.Button(self.system_tool_frame, text='copyKey', width=15, command=copyKey, bg=BG_COLOR,
                                   fg=TXT_COLOR,
                                   activebackground=SELECT_COLOR)
        self.b_copyKey.grid(row=3, column=0, padx=5, pady=5)

        self.b_beepMikrotik = tk.Button(self.system_tool_frame, text='beepMikrotik', width=15, command=beepMikrotik,
                                        bg=BG_COLOR, fg=TXT_COLOR,
                                        activebackground=SELECT_COLOR)
        self.b_beepMikrotik.grid(row=4, column=0, padx=5, pady=5)

        self.b_beepMikrotik = tk.Button(self.system_tool_frame, text='clear', width=15, command=clearConsole,
                                        bg=BG_COLOR, fg=TXT_COLOR,
                                        activebackground=SELECT_COLOR)
        self.b_beepMikrotik.grid(row=5, column=0, padx=5, pady=5)

        self.f_scriptSwitcher = tk.LabelFrame(self.tool_frame, text='scriptSwitcher', bg=BG_COLOR, fg=TXT_COLOR)
        self.f_scriptSwitcher.grid(row=0, column=0, padx=5, pady=5)

        self.b_scriptOn = tk.Button(self.f_scriptSwitcher, text='On', width=4, command=setScriptOn, bg=BG_COLOR,
                                    fg=TXT_COLOR,
                                    activebackground=SELECT_COLOR)
        self.b_scriptOn.grid(row=0, column=0, padx=5, pady=5)
        self.b_scriptOff = tk.Button(self.f_scriptSwitcher, text='Off', width=4, command=setScriptOff, bg=BG_COLOR,
                                     fg=TXT_COLOR,
                                     activebackground=SELECT_COLOR)
        self.b_scriptOff.grid(row=0, column=1, padx=5, pady=5)
        #
        self.f_flashMikrotik88 = tk.LabelFrame(self.tool_frame, text='flashMikrotik88', bg=BG_COLOR, fg=TXT_COLOR)
        self.f_flashMikrotik88.grid(row=1, column=0, padx=5, pady=5)

        self.b_flashMikrotik88_start = tk.Button(self.f_flashMikrotik88, text='Start', width=13,
                                                 command=thread_flashMikrotik88, bg=BG_COLOR, fg=TXT_COLOR,
                                                 activebackground=SELECT_COLOR)
        self.b_flashMikrotik88_start.grid(row=0, column=0, padx=5, pady=5, columnspan=3)

        self.b_flashMikrotik88_minus = tk.Button(self.f_flashMikrotik88, text='-', width=2,
                                                 command=lambda: cnt_buttons_flash('minus'), bg=BG_COLOR, fg=TXT_COLOR,
                                                 activebackground=SELECT_COLOR)
        self.b_flashMikrotik88_minus.grid(row=1, column=0, padx=5, pady=5)

        self.b_flashMikrotik88_times = tk.Label(self.f_flashMikrotik88, text='0', width=2, bg=BG_COLOR, fg=TXT_COLOR)
        self.b_flashMikrotik88_times.grid(row=1, column=1, padx=5, pady=5)

        self.b_flashMikrotik88_plus = tk.Button(self.f_flashMikrotik88, text='+', width=2,
                                                command=lambda: cnt_buttons_flash('plus'), bg=BG_COLOR, fg=TXT_COLOR,
                                                activebackground=SELECT_COLOR)
        self.b_flashMikrotik88_plus.grid(row=1, column=2, padx=5, pady=5)
        #
        self.f_changeIP = tk.LabelFrame(self.tool_frame, text='changeIP', bg=BG_COLOR, fg=TXT_COLOR)
        self.f_changeIP.grid(row=2, column=0, padx=5, pady=5)

        self.b_changeIP_start = tk.Button(self.f_changeIP, text='Start', width=13, command=changeIP, bg=BG_COLOR,
                                          fg=TXT_COLOR,
                                          activebackground=SELECT_COLOR)
        self.b_changeIP_start.grid(row=0, column=0, padx=5, pady=5, columnspan=3)

        self.b_changeIP_minus = tk.Button(self.f_changeIP, text='-', width=2, command=lambda: cnt_buttons_ip('minus'),
                                          bg=BG_COLOR, fg=TXT_COLOR,
                                          activebackground=SELECT_COLOR)
        self.b_changeIP_minus.grid(row=1, column=0, padx=5, pady=5)

        self.b_changeIP_times = tk.Label(self.f_changeIP, text='0', width=2, bg=BG_COLOR, fg=TXT_COLOR)
        self.b_changeIP_times.grid(row=1, column=1, padx=5, pady=5)

        self.b_changeIP_plus = tk.Button(self.f_changeIP, text='+', width=2, command=lambda: cnt_buttons_ip('plus'),
                                         bg=BG_COLOR, fg=TXT_COLOR,
                                         activebackground=SELECT_COLOR)
        self.b_changeIP_plus.grid(row=1, column=2, padx=5, pady=5)

        self.b_changeIP_16 = tk.Button(self.f_changeIP, text='15', width=3, command=lambda: set_buttons_ip('15'),
                                       bg=BG_COLOR, fg=TXT_COLOR,
                                       activebackground=SELECT_COLOR)
        self.b_changeIP_16.grid(row=2, column=0, padx=5, pady=5)

        self.b_changeIP_20 = tk.Button(self.f_changeIP, text='19', width=3, command=lambda: set_buttons_ip('19'),
                                       bg=BG_COLOR, fg=TXT_COLOR,
                                       activebackground=SELECT_COLOR)
        self.b_changeIP_20.grid(row=2, column=1, padx=5, pady=5)

        self.b_changeIP_0 = tk.Button(self.f_changeIP, text='0', width=3, command=lambda: set_buttons_ip('0'),
                                      bg=BG_COLOR, fg=TXT_COLOR,
                                      activebackground=SELECT_COLOR)
        self.b_changeIP_0.grid(row=2, column=2, padx=5, pady=5)

        #
        # self.f_uploadKey = tk.Label(self.tool_frame2, text=' ', height=1, bg=BG_COLOR, fg=TXT_COLOR)
        # self.f_uploadKey.grid(row=7, column=0, padx=5, pady=5)

        self.f_static_nodeName = tk.LabelFrame(self.key_tool_frame, text='staticNodeName', bg=BG_COLOR, fg=TXT_COLOR)
        self.f_static_nodeName.grid(row=0, column=0, padx=5, pady=5)
        self.s_static_nodeName_status = tk.IntVar()
        self.c_static_nodeName = tk.Checkbutton(self.f_static_nodeName, variable=self.s_static_nodeName_status,
                                                bg=BG_COLOR)
        self.c_static_nodeName.grid(row=0, column=0, padx=5, pady=5)
        self.t_static_nodeName = tk.Entry(self.f_static_nodeName, bg=BG_COLOR)
        self.t_static_nodeName.insert(0, 'JrB6fmrkfjMiJno')
        self.t_static_nodeName.grid(row=0, column=1, padx=5, pady=5)

        self.f_changeNodeName = tk.LabelFrame(self.key_tool_frame, text='Step 1', bg=BG_COLOR, fg=TXT_COLOR)
        self.f_changeNodeName.grid(row=1, column=0, padx=5, pady=5)
        self.b_changeNodeName = tk.Button(self.f_changeNodeName, text='changeNodeName', width=15,
                                          command=changeNodeName, bg=BG_COLOR, fg=TXT_COLOR,
                                          activebackground=SELECT_COLOR)
        self.b_changeNodeName.grid(row=0, column=0, padx=5, pady=5)

        self.f_collectHID = tk.LabelFrame(self.key_tool_frame, text='Step 2', bg=BG_COLOR, fg=TXT_COLOR)
        self.f_collectHID.grid(row=2, column=0, padx=5, pady=5)
        self.b_collectHID = tk.Button(self.f_collectHID, text='collectHID', width=15, command=collectHID, bg=BG_COLOR,
                                      fg=TXT_COLOR,
                                      activebackground=SELECT_COLOR)
        self.b_collectHID.grid(row=0, column=0, padx=5, pady=5)

        self.f_uploadKey = tk.LabelFrame(self.key_tool_frame, text='Step 3', bg=BG_COLOR, fg=TXT_COLOR)
        self.f_uploadKey.grid(row=3, column=0, padx=5, pady=5)
        self.b_uploadKey = tk.Button(self.f_uploadKey, text='uploadKey', width=15, command=uploadKey, bg=BG_COLOR,
                                     fg=TXT_COLOR, activebackground=SELECT_COLOR)
        self.b_uploadKey.grid(row=0, column=0, padx=5, pady=5)


def thread_getNodeName():
    print('getNodeName')

    def send_cmd(ssh_client, ip, cmd_name, cmd_sn, cmd_hdd_sn, cmd_date):

        """
        Данный метод предназначен для выполнения консольных команд нерутовым пользователем
        """
        channel = ssh_client.get_transport().open_session()
        channel.get_pty()
        channel.settimeout(5.0)
        channel.exec_command(cmd_name)
        answer = channel.recv(999).decode('utf-8')
        name = ''
        alt_addr = ''
        serial_number = ''
        onvifserver = onvifserver = setFontColor('NotExist', 'RED')
        hdd_sn = ''
        jetson_date = ''
        global CNT_U
        global CNT_P
        if f'password for {SSH_LOGIN}' in answer:
            channel.send(SSH_PWD + '\n')
            time.sleep(2)
            answer_node = channel.recv(999).decode('utf-8')
            for line in answer_node.split('\n'):
                if 'NGP_NODE_NAME' in line:
                    # print(line)
                    parts = line.split('=')
                    name = parts[1].replace('"', '')
                    if 'USER-DESKTOP' in name:
                        name = setFontColor('USER-DESKTOP', 'YELLOW')
                    else:
                        name = setFontColor(name.strip(), 'GREEN')
                if 'NGP_ALT_ADDR' in line:
                    # print(line)
                    parts = line.split('=')
                    alt_addr = parts[1].replace('"', '')
                if 'NGP_ONVIFSERVER_ENDPOINT' in line:
                    # print('NGP_ONVIFSERVER_ENDPOINT EXIST')
                    onvifserver = setFontColor('Exist', 'GREEN')
                    # print(re.search(r'"(.+?)\"', line).group(1))
        # print("\n")
        channel.close()
        if m_window.s_fastNodeName_status.get() == 0:
            channel = ssh_client.get_transport().open_session()
            channel.get_pty()
            channel.settimeout(5.0)
            channel.exec_command(cmd_sn)
            serial_number = channel.recv(999).decode('utf-8').strip()
            serial_number = serial_number.replace('\x00', '').strip()
            if serial_number == KEK_SN:
                serial_number = setFontColor('---> WARNING ---> ', 'RED') + setFontColor(serial_number,
                                                                                         'GREEN') + setFontColor(
                    ' <--- WARNING <---', 'RED')
                getattr(m_window, f'l_{ip}').configure(bg=PIRATE_SN)
                getattr(m_window, f'l_{ip}').configure(text='P')
                counting_status()
            else:
                # print('SN: ' + serial_number)
                serial_number = setFontColor(f'{serial_number}', 'YELLOW')
                getattr(m_window, f'l_{ip}').configure(bg=UNIQ_SN)
                getattr(m_window, f'l_{ip}').configure(text='U')
                counting_status()
            channel.close()

            channel = ssh_client.get_transport().open_session()
            channel.get_pty()
            channel.settimeout(5.0)
            channel.exec_command(cmd_hdd_sn)
            hdd_sn = channel.recv(999).decode('utf-8')
            parts = hdd_sn.split('=')
            hdd_sn = parts[1]
            # print('HDD_SN: ' + hdd_sn)
            channel.close()

            channel = ssh_client.get_transport().open_session()
            channel.get_pty()
            channel.settimeout(5.0)
            channel.exec_command(cmd_date)
            jetson_date = channel.recv(999).decode('utf-8')
            # print('DATE: ' + jetson_date + '\n')
            channel.close()
        return [name, serial_number, alt_addr, onvifserver, hdd_sn, jetson_date]

    def getNodeName():
        global CNT_N
        host_to_restart = []
        for ip in range(10, 30):
            if BUTTON_STATE[f'b_{ip}']:
                host_to_restart.append(ip)
        print(f'Hosts to get: {host_to_restart}\n')
        now = datetime.now()
        nodeNamesLog.info(now.strftime("%d-%m-%Y_%H-%M-%S"))
        for ip in host_to_restart:
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                print(f'10.10.10.{ip}')
                client.connect(hostname=f'10.10.10.{ip}', username=SSH_LOGIN, password=SSH_PWD, timeout=TIME_OUT)
                answers = send_cmd(client, ip, 'sudo cat ~ngp/instance.conf',
                                   'cat /sys/firmware/devicetree/base/serial-number',
                                   'udevadm info --query=all --name=/dev/mmcblk0 | grep ID_SERIAL',
                                   'date')

                print(tabulate(
                    [['NODENAME', answers[0]], ['SN', answers[1]], ['ALT_ADDR', answers[2]], ['HDD_SN', answers[4]],
                     ['ONVIFSERVER', answers[3]], ['JETSONDATE', answers[5]]]))
                print('\n')

                nodeNamesLog.info(
                    f'10.10.10.{ip} {answers[0]} SN: {answers[1]} ALT_ADDR: {answers[2]} HDD_SN: {answers[4]} ONVIFSERVER: {answers[3]} JETSONDATE: {answers[5]}')
                client.close()
            except Exception as error:
                print(f'{error}')
                getattr(m_window, f'l_{ip}').configure(bg=NOT_CONNECT)
                getattr(m_window, f'l_{ip}').configure(text='N')
                counting_status()
        print('getNodeName complete')

    find_thread = None
    for thread in threading.enumerate():
        if thread.name == f'thread_getNodeName':
            find_thread = thread
            print('already thread_getNodeName')
    if find_thread is None:
        StartThread('thread_getNodeName', getNodeName)


def thread_restartAxxon():
    print('restartAxxon')

    def send_cmd(ssh_client, cmd, password=SSH_PWD):
        """
        Данный метод предназначен для выполнения консольных команд нерутовым пользователем
        """
        channel = ssh_client.get_transport().open_session()
        channel.get_pty()
        channel.settimeout(5.0)
        channel.exec_command(cmd)
        answer = channel.recv(999).decode('utf-8')
        if f'password for {SSH_LOGIN}' in answer:
            channel.send(password + '\n')
        status = channel.recv_exit_status()
        channel.close()
        return status

    def restart_Axxon(ip):
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            print(f'10.10.10.{ip}')
            client.connect(hostname=f'10.10.10.{ip}', username=SSH_LOGIN, password=SSH_PWD, timeout=TIME_OUT)
            send_cmd(client, 'sudo systemctl restart axxon-next')
            print(f'Restart .{ip} complete')
            client.close()
        except Exception as error:
            print(f'{error}')

    def thread_restart():
        host_to_restart = []
        for ip in range(10, 30):
            if BUTTON_STATE[f'b_{ip}']:
                host_to_restart.append(ip)
        print(f'Hosts to restart: {host_to_restart}\n')
        for ip in host_to_restart:
            StartThread(f'thread_restart_{ip}', restart_Axxon, ip)

    find_thread = None
    for thread in threading.enumerate():
        if thread.name == f'thread_restartAxxon':
            print('already thread_restartAxxon')
            find_thread = thread
    if find_thread is None:
        StartThread('thread_restartAxxon', thread_restart)


def thread_rebootJetson():
    print('rebootJetson')

    def send_cmd(ssh_client, cmd, password=SSH_PWD):
        """
        Данный метод предназначен для выполнения консольных команд нерутовым пользователем
        """
        channel = ssh_client.get_transport().open_session()
        channel.get_pty()
        channel.settimeout(5.0)
        channel.exec_command(cmd)
        answer = channel.recv(999).decode('utf-8')
        if f'password for {SSH_LOGIN}' in answer:
            channel.send(password + '\n')
        status = channel.recv_exit_status()
        channel.close()
        return status

    def restart_Axxon(ip):
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            print(f'10.10.10.{ip}')
            client.connect(hostname=f'10.10.10.{ip}', username=SSH_LOGIN, password=SSH_PWD, timeout=TIME_OUT)
            send_cmd(client, 'sudo reboot')
            print(f'Reboot .{ip} complete')
            client.close()
        except Exception as error:
            print(f'{error}')

    def thread_restart():
        host_to_restart = []
        for ip in range(10, 30):
            if BUTTON_STATE[f'b_{ip}']:
                host_to_restart.append(ip)
        print(f'Hosts to reboot: {host_to_restart}\n')
        for ip in host_to_restart:
            StartThread(f'thread_reboot_{ip}', restart_Axxon, ip)

    find_thread = None
    for thread in threading.enumerate():
        if thread.name == f'thread_rebootJetson':
            print('already thread_rebootJetson')
            find_thread = thread
    if find_thread is None:
        StartThread('thread_rebootJetson', thread_restart)


def thread_changeAltAddr():
    print('changeAltAddr')

    def send_cmd(ssh_client, cmd, password=SSH_PWD):
        """
        Данный метод предназначен для выполнения консольных команд нерутовым пользователем
        """
        channel = ssh_client.get_transport().open_session()
        channel.get_pty()
        channel.settimeout(5.0)
        channel.exec_command(cmd)
        answer = channel.recv(999).decode('utf-8')
        if f'password for {SSH_LOGIN}' in answer:
            channel.send(password + '\n')
        status = channel.recv_exit_status()
        channel.close()
        return status

    def change_AltAddr(ip):
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            print(f'10.10.10.{ip}')
            client.connect(hostname=f'10.10.10.{ip}', username=SSH_LOGIN, password=SSH_PWD, timeout=TIME_OUT)
            cmd = "sudo sed -i '" + 's/NGP_ALT_ADDR=.*/NGP_ALT_ADDR="${' + f'NGP_ALT_ADDR:-10.10.10.{ip}' + '}"/\' ~ngp/instance.conf'
            send_cmd(client, cmd)
            print(f'Change .{ip} complete')
            client.close()
        except Exception as error:
            print(f'{error}')

    def thread_change():
        host_to_restart = []
        for ip in range(10, 30):
            if BUTTON_STATE[f'b_{ip}']:
                host_to_restart.append(ip)
        print(f'Hosts to change: {host_to_restart}\n')
        for ip in host_to_restart:
            StartThread(f'thread_change_{ip}', change_AltAddr, ip)

    find_thread = None
    for thread in threading.enumerate():
        if thread.name == f'thread_changeAltAddr':
            print('already thread_changeAltAddr')
            find_thread = thread
    if find_thread is None:
        StartThread('thread_changeAltAddr', thread_change)


def copyKey():
    if m_window.s_static_nodeName_status.get() == 1:
        if os.path.exists(f'{KEYCATALOG}\\license-pirate.key'):
            lasttime = time.ctime(os.path.getmtime(f'{KEYCATALOG}\\license-pirate.key'))
            size = math.ceil(os.path.getsize(f'{KEYCATALOG}\\license-pirate.key') / 1024)
            for i in range(10, 30):
                shutil.copy(
                    os.path.join(f'{KEYCATALOG}\\license-pirate.key'),
                    os.path.join(f'{KEYCATALOG}\\10.10.10.{i}.key')
                )
            print(f"license-pirate.key copy complete\nSize: {size}kb\nLast modified date: {lasttime}")
        else:
            print("File license-pirate.key not exist")
    else:
        if os.path.exists(f'{KEYCATALOG}\\license.key'):
            lasttime = time.ctime(os.path.getmtime(f'{KEYCATALOG}\\license.key'))
            size = math.ceil(os.path.getsize(f'{KEYCATALOG}\\license.key') / 1024)
            for i in range(10, 30):
                shutil.copy(
                    os.path.join(f'{KEYCATALOG}\\license.key'),
                    os.path.join(f'{KEYCATALOG}\\10.10.10.{i}.key')
                )
            print(f"license.key copy complete\nSize: {size}kb\nLast modified date: {lasttime}")
        else:
            print("File license.key not exist")


def thread_flashMikrotik88():
    print('start flashMikrotik88')

    def flashMikrotik88():
        def ftp_upload(ftp_obj, path, ftype='TXT'):
            if ftype == 'RSC':
                with open(path) as fobj:
                    ftp_obj.storlines('STOR ' + path, fobj)
            else:
                with open(path, 'rb') as fobj:
                    ftp_obj.storbinary('STOR ' + path, fobj, 1024)

        def mikrotik_configure(connect_ip, times):
            result_ftp = False
            ftp = ftplib.FTP()
            result_ssh = False
            cl = paramiko.SSHClient()
            cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            path_os = 'routeros-mipsbe-6.48.4.npk'
            path_ntp = 'ntp-6.48.4-mipsbe.npk'
            path_rsc = '29.12.2021_10.10.10.10_mikrotik_MSVK.rsc'
            command = f'/system reset-configuration no-defaults=yes skip-backup=yes ' \
                      f'run-after-reset=flash/29.12.2021_10.10.10.10_mikrotik_MSVK.rsc'
            try:
                print(f"= {times} = Try connect FTP")
                ftp.connect(connect_ip, 21)
                print(f"= {times} = Connect FTP successful")
                result_ftp = True
            except Exception:
                print(f"= {times} = Connect FTP failed")
                return False
            if result_ftp:
                try:
                    cl = paramiko.SSHClient()
                    cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    print(f"= {times} = Try connect SSH")
                    cl.connect(connect_ip, username='admin', password='', look_for_keys=False, allow_agent=False)
                    print(f"= {times} = Connect SSH successful")
                    result_ssh = True
                except Exception:
                    # ftp.quit()
                    result_ftp = False
                    print(f"= {times} = Connect SSH failed")
                    return False
            if result_ftp and result_ssh:
                ftp.login('admin')
                print(f"= {times} = Upload OS")
                ftp_upload(ftp, path_os)
                print(f"= {times} = Upload NTP")
                ftp_upload(ftp, path_ntp)
                ftp.cwd('flash')
                print(f"= {times} = Upload RSC")
                ftp_upload(ftp, path_rsc)
                ftp.quit()

                print(f"= {times} = Send command")
                cl.exec_command(command)
                cl.close()
                return True

        times = int(m_window.b_flashMikrotik88_times.cget('text'))
        complete_times = 0
        run = 0
        while complete_times != times:
            run += 1
            print(f'_ _ _ complete_times {complete_times}')
            result = mikrotik_configure('192.168.88.1', run)
            if result:
                complete_times += 1
                time.sleep(10)
            else:
                time.sleep(5)
        print('flashMikrotik88 complete')

    find_thread = None
    for thread in threading.enumerate():
        if thread.name == f'thread_flashMikrotik88':
            print('already thread_flashMikrotik88')
            find_thread = thread
    if find_thread is None:
        StartThread('thread_flashMikrotik88', flashMikrotik88)


def changeIP():
    print('start changeIP')

    def thread_changeIP():
        def mikrotik_changeIP(connect_ip, times, new_ip):
            cl = paramiko.SSHClient()
            cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            command = f'/ip address set address=10.10.10.{new_ip}/24 numbers=1'
            try:
                cl = paramiko.SSHClient()
                cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                print(f"= {times} = Try connect SSH")
                cl.connect(connect_ip, username='admin', password='synergo2020', port=SSH_MIKROTIK_PORT,
                           look_for_keys=False, allow_agent=False)
                print(f"= {times} = Connect SSH successful")
                result_ssh = True
            except Exception as ex:
                print(f"= {times} = Connect SSH failed")
                print(ex)
                print()
                return False
            if result_ssh:
                try:
                    print(f"= {times} = Send command")
                    cl.exec_command(command)
                    cl.close()
                    return True
                except Exception:
                    print(f"= {times} = Send command failed")
                    return False

        times = int(m_window.b_changeIP_times.cget('text'))
        complete_times = 0
        run = 0
        new_ip = 11
        while complete_times != times:
            run += 1
            print(f'_ _ _ complete_times {complete_times}')
            result = mikrotik_changeIP('10.10.10.10', run, new_ip)
            if result:
                complete_times += 1
                new_ip += 1
                time.sleep(10)
            else:
                time.sleep(5)
        print('changeIP complete')

    find_thread = None
    for thread in threading.enumerate():
        if thread.name == f'thread_changeIP':
            print('already thread_changeIP')
            find_thread = thread
    if find_thread is None:
        StartThread('thread_changeIP', thread_changeIP)


def beepMikrotik():
    print('start beepMikrotik')

    def thread_beep():
        status_ips = {}
        IPS = []
        result_ssh = False
        cl = paramiko.SSHClient()
        cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        command = ':for i from=1 to=25 do={ :beep ;:delay 0.5}'

        for ip in range(10, 30):
            if BUTTON_STATE[f'b_{ip}']:
                IPS.append(f'10.10.10.{ip}')
        print(IPS)
        if len(IPS) > 1:
            print('Too much for beep. Choose one')
            return
        if len(IPS) < 1:
            print('Choose one for beep')
            return
        if len(IPS) == 1:
            try:
                cl = paramiko.SSHClient()
                cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                print(f"=BEEP= Try connect SSH {IPS[0]}")
                cl.connect(IPS[0], username='admin', password='synergo2020', port=SSH_MIKROTIK_PORT,
                           look_for_keys=False, allow_agent=False)
                print(f"=BEEP= Connect SSH successful {IPS[0]}")
                result_ssh = True
            except Exception:
                print(f"=BEEP= Connect SSH failed {IPS[0]}")
                return
            if result_ssh:
                print(f"=BEEP= Send command {IPS[0]}")
                cl.exec_command(command)
                time.sleep(10)
                cl.close()

    find_thread = None
    for thread in threading.enumerate():
        if thread.name == f'thread_beep':
            print('already thread_beep')
            find_thread = thread
    if find_thread is None:
        StartThread('thread_beep', thread_beep)


def resetDHCP():
    print('start resetDHCP')
    cmd_disable = '/ip dhcp-server disable defconf'
    cmd_remove = '/ip dhcp-server lease remove numbers=0'
    cmd_enable = '/ip dhcp-server enable defconf'

    def fresetDHCP(ip):
        try:
            cl = paramiko.SSHClient()
            cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            print(f"=resetDHCP= Try connect SSH 10.10.10.{ip}")
            cl.connect(f'10.10.10.{ip}', username='admin', password='synergo2020', port=SSH_MIKROTIK_PORT,
                       look_for_keys=False, allow_agent=False)
            print(f"=resetDHCP= Connect SSH successful 10.10.10.{ip}")
            cl.exec_command(cmd_disable)
            time.sleep(0.5)
            cl.exec_command(cmd_remove)
            time.sleep(0.5)
            cl.exec_command(cmd_enable)
        except Exception as error:
            print(f'{error}')

    def thread_fresetDHCP():
        host_to_restart = []
        for ip in range(10, 30):
            if BUTTON_STATE[f'b_{ip}']:
                host_to_restart.append(ip)
        print(f'Hosts to resetDHCP: {host_to_restart}\n')
        for ip in host_to_restart:
            StartThread(f'thread_resetDHCP_{ip}', fresetDHCP, ip)

    find_thread = None
    for thread in threading.enumerate():
        if thread.name == f'thread_resetDHCP':
            print('already thread_resetDHCP')
            find_thread = thread
    if find_thread is None:
        StartThread('thread_resetDHCP', thread_fresetDHCP)


def startSSH():
    print('start startSSH')

    def thread_startSSH():
        IPS = []

        for ip in range(10, 30):
            if BUTTON_STATE[f'b_{ip}']:
                IPS.append(f'10.10.10.{ip}')
        print(IPS)
        if len(IPS) > 1:
            print('Too much for beep. Choose one')
            return
        if len(IPS) < 1:
            print('Choose one for beep')
            return
        if len(IPS) == 1:
            try:
                # subprocess.call(f'C:\Program Files (x86)\Mobatek\MobaXterm\MobaXterm.exe -newtab "ping 8.8.8.8"')
                subprocess.call(
                    f'C:\Program Files (x86)\Mobatek\MobaXterm\MobaXterm.exe -newtab "ssh -l user {IPS[0]}"')
            except Exception:
                print('MobaXterm error')

    find_thread = None
    for thread in threading.enumerate():
        if thread.name == f'startSSH':
            print('already startSSH')
            find_thread = thread
    if find_thread is None:
        StartThread('startSSH', thread_startSSH)


def clearConsole():
    os.system('cls')


def setScriptOn():
    print('start setScriptOn')

    def send_scriptOn(ip):
        result_ssh = False
        cl = paramiko.SSHClient()
        cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        command = '/system scheduler enable numbers=0,1,2'

        try:
            cl = paramiko.SSHClient()
            cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            cl.connect(hostname=f'10.10.10.{ip}', username='admin', password='synergo2020', port=SSH_MIKROTIK_PORT,
                       look_for_keys=False, allow_agent=False)
            result_ssh = True
        except Exception:
            print(f"=SWITCH ON= Connect SSH failed .{ip}\n")
            return
        if result_ssh:
            cl.exec_command(command)
            print(f'=SWITCH ON= Complete .{ip}')
            time.sleep(5)
            cl.close()

    def thread_scriptOn():
        host_to_restart = []
        for ip in range(10, 30):
            if BUTTON_STATE[f'b_{ip}']:
                host_to_restart.append(ip)
        print(f'Hosts to switch: {host_to_restart}\n')
        for ip in host_to_restart:
            time.sleep(random.randint(1, 2))
            StartThread(f'thread_restart_{ip}', send_scriptOn, ip)

    find_thread = None
    for thread in threading.enumerate():
        if thread.name == f'thread_setScriptOn':
            print('already thread_setScriptOn')
            find_thread = thread
    if find_thread is None:
        StartThread('thread_setScriptOn', thread_scriptOn)


def setScriptOff():
    print('start setScriptOff')

    def send_scriptOff(ip):
        result_ssh = False
        cl = paramiko.SSHClient()
        cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        command = '/system scheduler disable numbers=0,1,2'

        try:
            cl = paramiko.SSHClient()
            cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            cl.connect(hostname=f'10.10.10.{ip}', username='admin', password='synergo2020', port=SSH_MIKROTIK_PORT,
                       look_for_keys=False, allow_agent=False)
            result_ssh = True
        except Exception:
            print(f"=SWITCH ON= Connect SSH failed 10.10.10.{ip}")
            return
        if result_ssh:
            cl.exec_command(command)
            time.sleep(5)
            cl.close()

    def thread_scriptOff():
        host_to_restart = []
        for ip in range(10, 30):
            if BUTTON_STATE[f'b_{ip}']:
                host_to_restart.append(ip)
        print(f'Hosts to switch: {host_to_restart}\n')
        for ip in host_to_restart:
            StartThread(f'thread_restart_{ip}', send_scriptOff, ip)

    find_thread = None
    for thread in threading.enumerate():
        if thread.name == f'thread_setScriptOff':
            print('already thread_setScriptOff')
            find_thread = thread
    if find_thread is None:
        StartThread('thread_setScriptOff', thread_scriptOff)


def changeNodeName():
    print('start changeNodeName')

    def startStep1():
        status_ips = {}
        IPS = {}
        for ip in range(10, 30):
            if BUTTON_STATE[f'b_{ip}']:
                IPS[f'10.10.10.{ip}'] = ''

        def check_len(list_1, list_2):
            if len(list_1) == len(list_2):
                return True
            else:
                time.sleep(1)
                return False

        def thread_change_nodename(status_list, host):
            error = ''
            log_history = ''

            def send_cmd(ssh_client, cmd, password=SSH_PWD):
                """
                Данный метод предназначен для выполнения консольных команд нерутовым пользователем
                """
                channel = ssh_client.get_transport().open_session()
                channel.get_pty()
                channel.settimeout(5.0)
                channel.exec_command(cmd)
                answer = channel.recv(999).decode('utf-8')
                if f'password for {SSH_LOGIN}' in answer:
                    channel.send(password + '\n')
                status = channel.recv_exit_status()
                channel.close()
                return status

            def send_cmd_get_uuid(ssh_client, cmd, password=SSH_PWD):
                """
                Данный метод предназначен для выполнения консольных команд нерутовым пользователем
                """
                channel = ssh_client.get_transport().open_session()
                channel.get_pty()
                channel.settimeout(5.0)
                channel.exec_command(cmd)
                answer = channel.recv(999).decode('utf-8')
                if f'password for {SSH_LOGIN}' in answer:
                    channel.send(password + '\n')
                status = channel.recv_exit_status()
                channel.close()
                return [answer, status]

            try:
                log_history = ''
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(hostname=host, username=SSH_LOGIN, password=SSH_PWD, port=SSH_PORT, timeout=TIME_OUT)

                # change nodename and alt address commands set
                if m_window.s_static_nodeName_status.get() == 1:
                    newnodename = m_window.t_static_nodeName.get()
                else:
                    cmd_get_uuid1 = "python -c 'import uuid; print uuid.uuid1()'"
                    answer = send_cmd_get_uuid(client, cmd_get_uuid1)
                    status = answer[1]
                    log_history = log_history + f'{host}- cmd_nodename is completed {status}' + '\n'
                    newnodename = str(answer[0])
                    newnodename = re.sub('[^0-9a-zA-Z]+', '', newnodename)
                    newnodename = uuid.UUID(newnodename)
                    newnodename = shortuuid.encode(newnodename)
                    newnodename = newnodename[:15]

                log_history = log_history + f'{host}- New Node name is ' + newnodename + '\n'
                conf = f"""axxon-next-client	axxon-next-client/ui_log_level	select	INFO
                        axxon-next	axxon-next/nodename	string	{newnodename}
                        axxon-next-client	axxon-next-client/ui_log_only_digits_error	error	
                        axxon-next	axxon-next/event_db_user	string	ngp
                        axxon-next	axxon-next/event_db_password	string	ngp
                        axxon-next	axxon-next/ngp_log_maxsize	string	10
                        axxon-next-core	axxon-next-core/username	string	ngp
                        axxon-next-client	axxon-next-client/ui_first_start_default_culture_name	select	[OS Language]
                        axxon-next	axxon-next/event_db_host	string	localhost
                        axxon-next-core	axxon-next-core/allowprivports	boolean	false
                        axxon-next	axxon-next/ngp_log_maxsize_error	error	
                        axxon-next-client	axxon-next-client/ui_log_maxsize	string	10
                        axxon-next	axxon-next/domain	string	__KEEP__
                        axxon-next-core	axxon-next-core/fbuser	string	ngpfb
                        axxon-next	axxon-next/event_db_schema	string	__KEEP__
                        axxon-next	axxon-next/ngp_port_base	string	20111
                        axxon-next	axxon-next/ngp_iface_whitelist	string	
                        axxon-next-core	axxon-next-core/usergroups	multiselect	audio, video, disk, dialout
                        axxon-next	axxon-next/ngp_port_span	string	100
                        axxon-next	axxon-next/ngp_log_level	select	INFO
                        axxon-next	axxon-next/ngp_alt_addr	string	{host}
                        axxon-next	axxon-next/ngp_log_maxage	string	7
                        axxon-next	axxon-next/event_db_database	string	ngp
                        axxon-next	axxon-next/ngp_log_maxage_error	error	
                        axxon-next	axxon-next/event_db_port	string	20110
                        """

                check = 'sudo touch ~ngp/somefile.txt'
                pwd = 'pwd'
                cmd_set_sshd_config = "sudo sed 's/#ClientAliveInterval 0/#ClientAliveInterval 150/' /etc/ssh/sshd_config > ~/Documents/sshd_config"
                cmd_mv_sshd_config = 'sudo mv ~/Documents/sshd_config /etc/ssh/'
                cmd_restart_ssh = 'sudo systemctl reload sshd'
                cmd_stop_service = 'sudo systemctl stop axxon-next'
                cmd_start_service = 'sudo systemctl start axxon-next'
                cmd_debconf_set_selections = 'sudo debconf-set-selections -u < conf.conf'
                cmd_del_old_nodename = "sudo sed -i '/export NGP_NODE_NAME=/d' ~ngp/instance.conf"
                cmd_del_old_altaddress = "sudo sed -i '/NGP_ALT_ADDR=/d' ~ngp/instance.conf"
                cmd_dpkg_reconfigure = 'sudo env DEBIAN_FRONTEND=noninteractive dpkg-reconfigure axxon-next'
                cmd_ngpsh_addToDomain = f'sudo ~ngp/bin/start_app ngpsh hostagent proclaim {newnodename}'
                cmd_ngpsh_friendlynameDomain = f'sudo ~ngp/bin/start_app ngpsh hostagent domain fname {newnodename}'
                cmd_add_onvifserver_env = f"echo 'export NGP_ONVIFSERVER_ENDPOINT=\"172.16.100.5\"' | sudo tee -a /opt/AxxonSoft/AxxonNext/instance.conf"
                synergoTool.info(f'Host {host} processing...')

                send_cmd(client, cmd_stop_service)
                log_history = log_history + f'{host}- cmd_stop_service is completed' + '\n'

                sftp_client = client.open_sftp()
                stdin, stdout, stderr = client.exec_command('pwd')
                home_path = stdout.readline().strip('\n')
                file_path = f'{home_path}/conf.conf'
                remote_file = sftp_client.open(file_path, mode='wb')
                remote_file.writelines(conf.replace('\n\r', '\r'))
                remote_file.close()

                status = send_cmd(client, cmd_set_sshd_config)
                log_history = log_history + f'{host}- cmd_set_sshd_config is completed {status}' + '\n'

                status = send_cmd(client, cmd_mv_sshd_config)
                log_history = log_history + f'{host}- cmd_mv_sshd_config is completed {status}' + '\n'

                status = send_cmd(client, cmd_mv_sshd_config)
                log_history = log_history + f'{host}- cmd_mv_sshd_config is completed {status}' + '\n'

                status = send_cmd(client, cmd_restart_ssh)
                log_history = log_history + f'{host}- cmd_restart_ssh is completed {status}' + '\n'

                status = send_cmd(client, cmd_debconf_set_selections)
                log_history = log_history + f'{host}- cmd_debconf_set_selections is completed {status}' + '\n'

                status = send_cmd(client, cmd_del_old_nodename)
                log_history = log_history + f'{host}- cmd_del_old_nodename is completed {status}' + '\n'

                status = send_cmd(client, cmd_del_old_altaddress)
                log_history = log_history + f'{host}- cmd_del_old_altaddress is completed {status}' + '\n'

                status = send_cmd(client, cmd_dpkg_reconfigure)
                log_history = log_history + f'{host}- cmd_dpkg_reconfigure is completed {status}' + '\n'

                status = send_cmd(client, cmd_ngpsh_addToDomain)
                log_history = log_history + f'{host}- cmd_ngpsh_addToDomain is completed {status}' + '\n'

                time.sleep(40)
                try:
                    status = send_cmd(client, cmd_ngpsh_friendlynameDomain)
                    log_history = log_history + f'{host}- cmd_ngpsh_friendlynameDomain is completed {status}' + '\n'
                    time.sleep(25)

                    status = send_cmd(client, cmd_add_onvifserver_env)
                    log_history = log_history + f'{host}- cmd_add_onvifserver_env is completed {status}' + '\n'

                    send_cmd(client, cmd_stop_service)
                    log_history = log_history + f'{host}- cmd_stop_service is completed {status}' + '\n'

                    send_cmd(client, cmd_start_service)
                    log_history = log_history + f'{host}- cmd_start_service is completed {status}' + '\n'
                except Exception as ex:
                    print(f'{host} error: {ex}')

                client.close()
                IPS[host] = newnodename
                synergoTool.info(f'{host}- change_nodename() results: {IPS[host]}')
            except Exception as ex:
                # synergoTool.error(log_history)
                error = f'{host}- {str(ex)}'

            if len(error) == 0:
                status_list[host] = [True, error, log_history]
                return True, error
            else:
                status_list[host] = [False, error, log_history]
                return False, error

        def startingThreads(status_list):
            for host in IPS:
                StartThread(f'{host}_thread', thread_change_nodename, status_list, host)
                time.sleep(random.randint(1, 2))

        StartThread('startingThreads', startingThreads, status_ips)

        same_len = False
        while not same_len:
            same_len = check_len(IPS, status_ips)
        errors_host = []
        for host_status in status_ips:
            if status_ips[host_status][0]:
                # synergoTool.info(f'{host_status} "Changing nodename and alt-addrr completed"')
                print(f'{host_status} Operation Changing nodename and alt address completed.')
            else:
                errors_host.append(host_status)
                # synergoTool.error(f'{host_status} "Changing nodename and alt-addrr ERROR", results: ')
                # synergoTool.error(f'{host_status} {status_ips[host_status][2]}')
        if len(errors_host) > 0:
            for host in errors_host:
                synergoTool.error(f'Uncompleted host: {host}')
                synergoTool.error(f'{status_ips[host][1]}')

    find_thread = None
    for thread in threading.enumerate():
        if thread.name == f'startStep1':
            print('already startStep1')
            find_thread = thread
    if find_thread is None:
        StartThread('startStep1', startStep1)


def collectHID():
    print('start collectHID')
    IPS = {}
    for ip in range(10, 30):
        if BUTTON_STATE[f'b_{ip}']:
            IPS[f'10.10.10.{ip}'] = ''

    print(f'Host to collect: {len(IPS)}')

    def startStep2():
        def make_activation_request():
            CURRENT_TIME = arrow.now().format('YYYY-MM-DD HH-mm-ss')
            PATH_TO_SAVE = os.path.join(os.getcwd(), CURRENT_TIME)
            errors = []
            problem_hosts = []
            os.mkdir(PATH_TO_SAVE)
            for host in IPS:
                try:
                    synergoTool.info(f'Host {host} processing...')
                    print(f'Host {host} processing...')
                    client = paramiko.SSHClient()
                    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    client.connect(hostname=host, username=SSH_LOGIN, password=SSH_PWD, port=SSH_PORT, timeout=TIME_OUT)
                    channel = client.get_transport().open_session()
                    channel.get_pty()
                    channel.settimeout(5)
                    channel.exec_command('sudo cat ~ngp/instance.conf')
                    answer = channel.recv(999).decode('utf-8')
                    if f'password for {SSH_LOGIN}' in answer:
                        channel.send(SSH_PWD + '\n')
                        time.sleep(2)
                        answer_node = channel.recv(999).decode('utf-8')
                        for line in answer_node.split('\n'):
                            if 'NGP_NODE_NAME' in line:
                                newnodename = re.search(r'"(.+?)\"', line).group(1)  # имя ноды без ковычек
                                synergoTool.info(f'Nodename {newnodename} find')
                                print(f'Nodename {newnodename} find')
                                IPS[host] = newnodename

                    cmd = f'sudo ~ngp/bin/start_app LS_tool ' \
                          f'--create keys+=goodsSystemType={LICENSE_TYPE},NGPVersion=4.1.0 ' \
                          f'--add-ngp {IPS[host]} ' \
                          f'--sponsor-node {IPS[host]},172.16.100.5:{BASE_PORT},{IPS[host]}.loopback:{BASE_PORT} ' \
                          f'hosts.{IPS[host]}.restr=DeviceIpint=2,NeuralTracker=2,TextChannel=0,NvrLogic=1,' \
                          f'ObjectTracker=2147483647,DeviceNVR16=0,VmdaChannelBinding=2,VmdaChannelBindingLight=2147483647,' \
                          f'TagAndTrackPro=0,LPRDetector_Any=0,OfflineAnalytics=0,MultimediaStorage=2147483647,' \
                          f'MultimediaStorage_Space=2147483647 > {host}.txt'

                    # sudo ~ngp/bin/start_app LS_tool --create keys+=goodsSystemType=13,NGPVersion=4.1.0 --add-ngp 121-10101014 --sponsor-node 121-10101014,172.16.100.5:20111,121-10101014.loopback:20111 hosts.121-10101014 .restr=DeviceIpint=2,NeuralTracker=2,TextChannel=0,NvrLogic=1,ObjectTracker=2147483647,DeviceNVR16=0,VmdaChannelBinding=2,VmdaChannelBindingLight=2147483647,TagAndTrackPro=0,LPRDetector_Any=0,OfflineAnalytics=0,MultimediaStorage=2147483647,MultimediaStorage_Space=2147483647 > 10.10.10.14.txt
                    synergoTool.debug(f"LS_TOOL call with parameters: {cmd}")

                    channel = client.get_transport().open_session()
                    channel.get_pty()
                    channel.settimeout(5)
                    channel.exec_command(cmd)
                    answer = channel.recv(999).decode('utf-8')
                    if f'password for {SSH_LOGIN}' in answer:
                        channel.send(SSH_PWD + '\n')
                    channel.recv_exit_status()
                    channel.close()

                    sftp_client = client.open_sftp()

                    stdin, stdout, stderr = client.exec_command('pwd')
                    home_path = stdout.readline().strip('\n')
                    file_path = f'{home_path}/{host}.txt'
                    sftp_client.get(file_path, os.path.join(f'{CURRENT_TIME}', f'{host}_{IPS[host]}.txt'))

                except Exception as ex:
                    errors.append(f'{ex}')
                    problem_hosts.append(f'{host}')
            if len(errors) == 0:
                return True, problem_hosts, errors
            else:
                return False, problem_hosts, errors

        status, problem_host, errors = make_activation_request()
        if status:
            synergoTool.info('step2 "Collecting hardware info completed"')
            print('Operation "Collecting hardware info completed".')
        else:
            synergoTool.error('step2 "Collecting hardware info" ERROR, results: ')
            synergoTool.error(str(list(zip(problem_host, errors))))
            print('Operation incomplete:')
            for er in errors:
                synergoTool.error(er)
                print(er)

    find_thread = None
    for thread in threading.enumerate():
        if thread.name == f'startStep2':
            print('already startStep2')
            find_thread = thread
    if find_thread is None:
        StartThread('startStep2', startStep2)


def uploadKey():
    print('start uploadKey')
    IPS = {}
    for ip in range(10, 30):
        if BUTTON_STATE[f'b_{ip}']:
            IPS[f'10.10.10.{ip}'] = ''
    print(f'Host to upload: {len(IPS)}')

    global COMPLETED_HOST
    COMPLETED_HOST = 0

    def startStep3():

        def license_activation():
            errors = []
            problem_hosts = []

            def send_cmd(ssh_client, cmd, password=SSH_PWD):
                """
                Данный метод предназначен для выполнения консольных команд нерутовым пользователем
                """

                channel = ssh_client.get_transport().open_session()
                channel.get_pty()
                channel.settimeout(5.0)
                channel.exec_command(cmd)
                answer = channel.recv(999).decode('utf-8')
                if f'password for {SSH_LOGIN}' in answer:
                    channel.send(password + '\n')
                status = channel.recv_exit_status()
                channel.close()
                return status

            def thread_SendKey(host):
                global COMPLETED_HOST
                try:
                    synergoTool.info(f'Host {host} processing...')
                    client = paramiko.SSHClient()
                    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    client.connect(hostname=host, username=SSH_LOGIN, password=SSH_PWD, port=SSH_PORT, timeout=TIME_OUT)
                    stdin, stdout, stderr = client.exec_command('pwd')
                    home_path = stdout.readline().strip('\n')

                    cmd_stop_service = 'sudo systemctl stop axxon-next'
                    cmd_0 = f"sudo rm {TICKETS}*.key"
                    cmd_1 = f"sudo mv {home_path}/{host}.key {TICKETS}"
                    cmd_2 = f"sudo chown ngp:ngp {TICKETS}{host}.key;" \
                            f"sudo chmod 444 {TICKETS}{host}.key;" \
                            f"sudo mv {TICKETS}{host}.key {TICKETS}license.key"

                    cmd_3 = "sudo service axxon-next restart"

                    status = send_cmd(client, cmd_stop_service)
                    # synergoTool.info(f'cmd_stop_service is completed {status}')

                    status = send_cmd(client, cmd_0)
                    # synergoTool.info(f'rm TICKETS is completed {status}')

                    sftp_client = client.open_sftp()
                    sftp_client.put(os.path.join(KEYCATALOG, f'{host}.key'), f"{home_path}/{host}.key")

                    status = send_cmd(client, cmd_1)
                    # synergoTool.info(f'mv TICKETS is completed {status}')
                    status = send_cmd(client, cmd_2)
                    # synergoTool.info(f'chown chmod mv is completed {status}')
                    status = send_cmd(client, cmd_3)
                    COMPLETED_HOST += 1
                    synergoTool.info(f'{host} upload key is completed - completed_hosts: {COMPLETED_HOST}')
                    if COMPLETED_HOST == len(IPS):
                        print(setFontColor('All keys uploaded :)', 'GREEN'))

                except Exception as ex:
                    errors.append(f'{str(ex)}')
                    problem_hosts.append(f'{host}')
                    synergoTool.info(f'Host {host} upload error')

            def startingThreads():
                for host in IPS:
                    StartThread(f'{host}_thread_SendKey', thread_SendKey, host)

            StartThread('startingThreads', startingThreads)

            # assert not errors, f'Сервера, на которых операция завершилась с ошибкой {list(zip(problem_hosts, errors))}, \n' \
            #                    f'Cписок IP проблемных серверов: {problem_hosts}'

            if len(errors) == 0:
                return True, problem_hosts, errors
            else:
                return False, problem_hosts, errors

        status, problem_host, errors = license_activation()
        # if status:
        #     synergoTool.info('step3 "License activation completed"')
        #     print('Operation "License activation completed".')
        # else:
        #     synergoTool.error('step3 "License activation" ERROR, results: ')
        #     synergoTool.error(str(list(zip(problem_host, errors))))
        #     print('Operation incomplete:')
        #     for er in errors:
        #         synergoTool.error(er)
        #         print(er)

    find_thread = None
    for thread in threading.enumerate():
        if thread.name == f'startStep3':
            print('already startStep3')
            find_thread = thread
    if find_thread is None:
        StartThread('startStep3', startStep3)


if __name__ == "__main__":
    main_window = tk.Tk()
    m_window = MainWindow(main_window)
    f = Figlet()
    print(f.renderText(f'MSVK TOOLS {VERSION}'))
    main_window.mainloop()
