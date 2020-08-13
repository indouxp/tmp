# -*- coding: utf-8 -*-
#
# 処理概要: 共通
#
import datetime
import os
import subprocess
import sys
import traceback


def is_close(file_path):

    # file_pathがcloseしているかを、lsofにより判定する
    # 戻り値: False: open中
    #         True : close済み

    lsof = subprocess.run(['/usr/sbin/lsof', file_path],
                          encoding='utf-8',
                          stdout=subprocess.PIPE)
    if lsof.returncode == 0:
        return False  # open
    else:
        return True   # not open


def get_hostname():

    # ホスト名取得

    hostname = subprocess.run(['/usr/bin/hostname'],
                              encoding='utf-8',
                              stdout=subprocess.PIPE)
    result = str(hostname.stdout)
    return result.strip()


def make_lognameformat(name, file):

    # ログファイル名

    now = datetime.datetime.now()
    nameformat = "{0}.{1:04}{2:02}{3:02}T{4:02}{5:02}{6:02}.{7}.log".format(
                 name,
                 now.year,
                 now.month,
                 now.day,
                 now.hour,
                 now.minute,
                 now.second,
                 file)
    return nameformat


def make_line(msg):

    # ログメッセージ行作成

    now = datetime.datetime.now()
    line = "{0:04}-{1:02}-{2:02} {3:02}:{4:02}:{5:02},{6:06}: {7}".format(
           now.year,
           now.month,
           now.day,
           now.hour,
           now.minute,
           now.second,
           now.microsecond,
           msg)
    return line

# エントリーポイント
if __name__ == '__main__':
    try:
        print("hostname      : [{}]".format(get_hostname()))
        print("filenameformat: [{}]".format(make_filenameformat()))
        print("msg           : [{}]".format(make_line(u"テスト")))

        file_path = '/tmp/test.txt'
        print("open {}".format(file_path))
        file = open(file_path, 'a', encoding="utf-8")
        file.write(str(datetime.datetime.now()))

        print("is_close {}:[{}]".format(file_path, is_close(file_path)))

        file.close()

        print("close {}".format(file_path))

        print("is_close {}:[{}]".format(file_path, is_close(file_path)))

        sys.exit(0)
    except Exception as e:
        print(traceback.format_exc())
        sys.exit(9)
