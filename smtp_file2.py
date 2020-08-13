# -*- coding: utf-8 -*-
#
# 処理概要: 引数で与えられたcsvファイルを読み込み、smtpを実行する。
#   引数1: SLFもしくは、RMFファイル
#
import common
import constant
import configparser
import csv
import datetime
from email.mime.text import MIMEText
from email.utils import formatdate
from logging import basicConfig, getLogger, DEBUG, INFO
import os
import pathlib
import re
import smtplib
import subprocess
from sys import argv, exit
import time
import traceback

logger = getLogger(__name__)
logger.setLevel(INFO)

def init(setup_parameters):

    # 初期処理 同一ディレクトリのiniファイルを読み込み

    #global logger
    is_error = False

    # iniファイル読み込み
    script_fullpath = pathlib.Path(os.path.abspath(__file__))
    ini_path = script_fullpath.with_suffix('.ini')
    if not os.path.exists(ini_path):
        raise FileNotFoundError(errno.ENOENT,
                                os.strerror(errno.ENOENT),
                                ini_path)
    ini = configparser.ConfigParser()
    ini.read(ini_path, encoding='utf-8')

    # iniより値の取得
    setup_parameters['rcv_dir'] = ini.get('general', 'rcv_dir')
    setup_parameters['run_dir'] = ini.get('general', 'run_dir')
    setup_parameters['log_dir'] = ini.get('general', 'log_dir')
    setup_parameters['result_dir'] = ini.get('general', 'result_dir')
    setup_parameters['in_path'] = argv[1]
    setup_parameters['in_base'] = re.sub('\.(slf|rmf)', '', os.path.basename(argv[1]))
    setup_parameters['success_path'] = os.path.join(ini.get('general', 'result_dir'),
                                             "{}.success".format(setup_parameters['in_base']))
    setup_parameters['fail_path'] = os.path.join(ini.get('general', 'result_dir'),
                                          "{}.fail".format(setup_parameters['in_base']))
    setup_parameters['done_path'] = os.path.join(ini.get('general', 'result_dir'),
                                          "{}.done".format(setup_parameters['in_base']))
    setup_parameters['from'] = ini.get('general', 'from')
    setup_parameters['retry_max'] = ini.get('general', 'retry_max')
    setup_parameters['retry_interval'] = ini.get('general', 'retry_interval')
    setup_parameters['sftp_cmd'] = ini.get('general', 'sftp_cmd')
    setup_parameters['sftp_user'] = ini.get('general', 'sftp_user')
    setup_parameters['sftp_host'] = ini.get('general', 'sftp_host')
    setup_parameters['sftp_dest'] = ini.get('general', 'sftp_dest')

    # ログファイルレイアウト
    log_path = '{}/{}'.format(setup_parameters['log_dir'],
                              common.make_lognameformat(
                                  re.sub('\.py', '',
                                         os.path.basename(__file__)),
                                  setup_parameters['in_base']))
    fmt = '%(levelname)s: %(asctime)s: %(funcName)s: %(lineno)s: %(message)s'
    basicConfig(filename=log_path, format=fmt)

    logger.info("初期パラメータ")
    #
    # パラメータ全件出力とパスに関する存在チェック
    #
    for key in setup_parameters:
        comment = ""
        if re.search(r'_dir', key):  # ディレクトリの場合存在チェック
            if os.path.isdir(setup_parameters[key]):
                comment = ": このパスは存在します。"
            else:
                comment = ": このパスは存在しません。"
                is_error = True
                reason = f"{setup_parameters[key]}が存在しません。"

        if re.search(r'_path', key):  # ファイルパスの場合存在チェック
            if os.path.isfile(setup_parameters[key]):
                comment = ": このパスは存在します。"
            else:
                comment = ": このパスは存在しません。"

        if re.search(r'_cmd', key):  # コマンドパスの場合存在チェック
            if os.path.isfile(setup_parameters[key]):
                comment = ": このパスは存在します。"
            else:
                comment = ": このパスは存在しません。"
                is_error = True
                reason = f"{setup_parameters[key]}が存在しません。"

        logger.info("{0:<20}: {1} {2}".format(key, setup_parameters[key], comment))

    # 初期パラメータでエラー
    if is_error:
        raise Exception(reason)


def main(setup_parameters):

    # 主処理

    #global logger

    try:
        logger.info("開始")

        row_count = 0
        success_count = 0
        failure_count = 0
        skip_count = 0
        success_file = open(setup_parameters['success_path'], "w", encoding="utf-8")
        success_csv = csv.writer(success_file, lineterminator='\n')
        fail_file = open(setup_parameters['fail_path'], "w", encoding="utf-8")
        fail_csv = csv.writer(fail_file, lineterminator='\n')

        # 完了ファイルが存在した場合
        done_count = 0
        if os.path.isfile(setup_parameters['done_path']):
            with open(setup_parameters['done_path']) as done:
                done_count = int(done.read())
            logger.info("{}レコードまでは終了しています。".format(done_count))

        # メール送付リストファイル処理
        with open(setup_parameters['in_path']) as infile:
            reader = csv.reader(infile)
            # メール送付リストファイル全件処理
            for row in reader:
                row_count += 1
                if row_count <= done_count: # 現在のレコード ≦ 済レコード数
                    skip_count += 1
                    continue

                field_count = 0
                mypage_id = ""
                mail_transmit_sequence = ""
                mail_address = ""
                mail_title = ""
                mail_maintext = ""
                for field in row:
                    if field_count == constant.MYPAGE_ID:
                        mypage_id = field
                    elif field_count == constant.MAIL_TRANSMIT_SEQUENCE:
                        mail_transmit_sequence = field
                    elif field_count == constant.MAIL_ADDRESS:
                        mail_address = field
                    elif field_count == constant.MAIL_TITLE:
                        mail_title = field
                    elif field_count == constant.MAIL_MAINTEXT:
                        mail_maintext = field
                    field_count += 1

                logger.debug("mypage_id: " + mypage_id)
                logger.debug("mail_transmit_sequence: " + mail_transmit_sequence)
                logger.debug("mail_address: " + mail_address)
                logger.debug("mail_title: " + mail_title)
                logger.debug("mail_maintext: " + mail_maintext)
                logger.info("{0}: {1} {2} {3} {4} {5}".format(row_count,
                                                        mypage_id,
                                                        mail_transmit_sequence,
                                                        mail_address,
                                                        mail_title,
                                                        mail_maintext))

                fmt = '%Y/%m/%d %H:%M:%S'
                now_ymdhms = datetime.datetime.now().strftime(fmt)

                # レコードとして妥当か
                err_cd, err_msg =  is_ok(mypage_id,
                                         mail_transmit_sequence,
                                         mail_address,
                                         mail_title,
                                         mail_maintext)
                logger.info("{0}: {1} {2}".format(row_count,
                                                  err_cd,
                                                  err_msg))
                if err_cd is None and err_msg is None:
                    msg = create_message(setup_parameters['from'],
                                         mail_address,
                                         mail_title,
                                         mail_maintext)
                    # メール送信
                    err_cd, err_msg =  send(setup_parameters['from'],
                                            mail_address,
                                            msg,
                                            setup_parameters)
                    if err_cd is None and err_msg is None:
                        success_count += 1 # 成功
                        success_csv.writerow([mypage_id,
                                              mail_transmit_sequence,
                                              mail_address,
                                              mail_title,
                                              mail_maintext,
                                              now_ymdhms])
                    else:
                        failure_count += 1 # 失敗
                        fail_csv.writerow([mypage_id,
                                           mail_transmit_sequence,
                                           mail_address,
                                           mail_title,
                                           #mail_maintext,
                                           now_ymdhms,
                                           err_cd,
                                           err_msg])
                else:
                    failure_count += 1 # チェックに失敗
                    fail_csv.writerow([mypage_id,
                                       mail_transmit_sequence,
                                       mail_address,
                                       mail_title,
                                       #mail_maintext,
                                       now_ymdhms,
                                       err_cd,
                                       err_msg])
            # 済ファイル書き込み
            with open(setup_parameters['done_path'], "w") as done:
                done.write(str(row_count))

    finally:
        if success_file:
            success_file.close()
            logger.debug('success_file close')
        if fail_file:
            fail_file.close()
            logger.debug('fail_file close')

    if 0 < failure_count:
        proc = subprocess.run([setup_parameters['sftp_cmd'],
                               setup_parameters['fail_path'],
                               setup_parameters['sftp_user'],
                               setup_parameters['sftp_host'],
                               setup_parameters['sftp_dest']])
        if proc.returncode == 0:  # 戻り値が正常な場合
            logger.info("sftp OK: " + setup_parameters['fail_path'])
        else:
            logger.critical("sftp NG: " + setup_parameters['fail_path'])
            raise Exception("{} {} RC={}".format(setup_parameters['sftp_cmd'],
                                                 setup_parameters['fail_path'],
                                                 proc.returncode))

    logger.info("入力ファイル                  : {0}".format(setup_parameters['in_path']))
    logger.info("全レコード数                  : {0}".format(str(row_count)))
    logger.info("済レコード数                  : {0}".format(str(done_count)))
    logger.info("スキップレコード数            : {0}".format(str(skip_count)))
    logger.info("SMTP成功                      : {0}".format(str(success_count)))
    logger.info("SMTP失敗、レコードチェック失敗: {0}".format(str(failure_count)))

    logger.info("終了")
    if row == failure_count:  # 処理全件がエラーの場合
        return 9

    return 0


def create_message(from_addr, to_addr, subject, body):

    # メールメッセージ作成

    #global logger
    logger.debug("from: {} to: {} Subject: {}".format(from_addr, to_addr, subject))
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Date'] = formatdate(localtime=True)
    return msg


def is_ok(mypage_id, mail_transmit_sequence, mail_address, mail_title, mail_maintext):

    # レコードチェック
    if mypage_id == "":
        return 'MFN-F-001-E', 'マイページIDが空です。'
    elif mail_transmit_sequence == "":
        return 'MFN-F-002-E', 'メール送付シーケンスが空です。'
    elif mail_address == "":
        return 'MFN-F-003-E', 'メールアドレスが空です。'
    elif mail_title == "":
        return 'MFN-F-004-E', 'メール件名が空です。'
    elif mail_maintext == "":
        return 'MFN-F-005-E', 'メール本文が空です。'
    else:
        return None, None


def send(from_addr, to_addr, msg, setup_parameters):

    # メール送信

    #global logger
    logger.debug("from: {} to: {}".format(from_addr, to_addr))
    try:
        smtpclient = None
        error_count = 0
        while True:
            try:
                # 自メールサーバに接続できないとき、ここで例外が起きる
                smtpclient = smtplib.SMTP('localhost', 25)
                break
            except Exception as e:
                logger.debug(str(e))
                error_count += 1
                if int(setup_parameters['retry_max']) <= error_count:
                    msg = "接続再試行回数{}回を超えました。".format(setup_parameters['retry_max'])
                    logger.warning(msg)
                    raise Exception(msg)
                time.sleep(int(setup_parameters['retry_interval']))

        # メール送信
        smtpclient.sendmail(from_addr, to_addr, msg.as_string())

        return None, None            # err_cd, err_msg
    except ConnectionRefusedError as e:
        logger.warning(str(e))
        return 'MPH-S-002-E', str(e) # err_cd, err_msg
    except Exception as e:
        logger.warning(str(e))
        return 'MPH-S-001-E', str(e) # err_cd, err_msg
    finally:
        if smtpclient is not None:
            logger.debug('smtpclient close')
            smtpclient.close()


# エントリーポイント
if __name__ == '__main__':
    #global logger
    try:
        setup_parameters = {}
        init(setup_parameters)
        rc = 0
        rc = main(setup_parameters)
        exit(rc)
    except Exception as e:
        msg = "処理中に、エラーが発生しました。終了します。{}".format(str(e))
        logger.critical(msg)
        logger.critical(traceback.format_exc())
        subprocess.run(['/usr/bin/logger', msg])
        exit(9)
