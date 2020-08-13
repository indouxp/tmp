#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# 処理概要: 指定されたディレクトリを指定間隔毎に監視し、
# ファイルが作成された場合、指定コマンドをバックグラウンド実行する
#
# 仕掛かり: バックグラウンド
# loggingはデーモンとなる場合、使用できない
import common
import configparser
import daemon
import datetime
import os
import pathlib
import re
import shutil
import subprocess
import sys
import traceback
import time


# 大域変数
global g_fail
g_fail = {}

def init(setup_parameters):

    # 初期化(初期化ファイルの読み込み)

    global logger
    is_error = False

    # iniファイル読み込み
    script_path = pathlib.Path(os.path.abspath(__file__))
    ini_path = script_path.with_suffix('.ini')
    if not os.path.exists(ini_path):
        raise FileNotFoundError(errno.ENOENT,
                                os.strerror(errno.ENOENT),
                                ini_path)
    ini = configparser.ConfigParser()
    ini.read(ini_path, encoding='utf-8')

    # iniより値の取得
    setup_parameters['pid_path'] = os.path.join(
                                       ini.get('general', 'pid_dir'),
                                       "{}.pid".format(os.path.basename(__file__)))
    setup_parameters['log_dir'] = ini.get('general', 'log_dir')
    setup_parameters['stop_path'] = os.path.join(
                                       ini.get('general', 'stop_dir'),
                                       "{}.stop".format(os.path.basename(__file__)))
    setup_parameters['rcv_dir'] = ini.get('general', 'rcv_dir')
    setup_parameters['run_dir'] = ini.get('general', 'run_dir')
    setup_parameters['process_dir'] = ini.get('general', 'process_dir')
    setup_parameters['max_process'] = int(ini.get('general', 'max_process'))
    setup_parameters['suffix'] = ini.get('general', 'suffix')
    setup_parameters['monitoring_interval'] = int(ini.get('general', 'monitoring_interval'))
    setup_parameters['run_cmd'] = ini.get('general', 'run_cmd')
    decoration = common.make_filenameformat()
    setup_parameters['log_path'] = os.path.join(ini.get('general', 'log_dir'),
                                       "{}.{}.log".format(os.path.basename(__file__), decoration))


    # ログファイルレイアウト
    basicConfig(filename='{}/{}.{}.log'.format(setup_parameters['log_dir'],
                                               os.path.basename(__file__),
                                               common.make_filenameformat()),
                format='%(levelname)s: %(asctime)s: %(funcName)s: %(lineno)s:  %(message)s')
    logger = getLogger(__name__)
    logger.setLevel(INFO)

    logger.info("初期パラメータ")
    # パラメータ全件出力とパスに関する存在チェック
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

        logger.info("{0:<20}: {1} {2}".format(key, setup_parameters[key], comment))
    # 初期パラメータでエラー
    if is_error:
        raise Exception(reason)


def monitor(setup_parameters):

    # 監視ループ

    global logger
    write_log("開始", setup_parameters)
    logger.info("開始")
    while True:
        try:
            if os.path.exists(setup_parameters['stop_path']):  # stop_pathが存在した場合は、永久ループを抜ける
                logger.warning('停止ファイル{}により処理を停止します。'.format(setup_parameters['stop_path']))
                break
        except Exception as e:
            raise

        process_dir = pathlib.Path(setup_parameters['process_dir'])                # プロセス数監視ディレクトリ
        process_list = list(process_dir.glob("*.pid"))                    # 現実行中のプロセス
        if len(process_list) < setup_parameters['max_process']:                    # 現時点のプロセス数が最大値より小さい場合
            monitoring_dir = pathlib.Path(setup_parameters['rcv_dir'])             # 監視対象ディレクトリ
            discover_list = list(monitoring_dir.glob(setup_parameters['suffix']))  # 監視対象のサフィックス
            for discover in discover_list:
                discover_path = str(discover)
                if common.is_close(discover_path) == True:                # クローズしている
                    try:
                        if discover_path not in g_fail:                   # 失敗リストにない
                            shutil.move(discover_path, setup_parameters['run_dir'])              # 実行用ディレクトリに移動
                            proc = subprocess.run([setup_parameters['run_cmd'], discover_path])  # run_cmdの実行
                            if proc.returncode == 0:                                    # 戻り値が正常な場合
                                logger.info("OK: " + discover_path + ": " + discover_path)
                            else:
                                logger.info("NG: " + discover_path + ": " + discover_path)
                                raise Exception("{} {} RC={}".format(
                                                              setup_parameters['run_cmd'],
                                                              discover_path,
                                                              proc.returncode))
                    except Exception as e:
                        g_fail[discover_path] = str(e)
                        logger.info("NG: " + discover_path + ": [" + str(e) + "]")

        time.sleep(setup_parameters['monitoring_interval'])
    logger.info("終了")


# エントリーポイント
if __name__ == '__main__':
    from lockfile.pidlockfile import PIDLockFile
    dc = daemon.DaemonContext(
         pidfile = PIDLockFile(setup_parameters['pid_path'])
         )

    with dc:
        try:
            from logging import basicConfig, getLogger, DEBUG, INFO
            setup_parameters = {}
            init(setup_parameters)
            monitor(setup_parameters)
            sys.exit(0)
        except Exception as e:
            msg = "処理中に、エラーが発生しました。終了します。{}".format(str(e))
            line = common.make_line(msg)
            rc = subprocess.run(['/usr/bin/logger', line])
            logger.critical(msg)
            write_log(traceback.format_exc(), setup_parameters)
            logger.critical(traceback.format_exc())
            sys.exit(9)
        finally:
            if 0 < len(g_fail):
                logger.info("エラー件数: " + str(len(g_fail)))
                for key in g_fail.keys():
                    msg = "{}: {}".format(key, g_fail[key])
                    logger.info(msg)

