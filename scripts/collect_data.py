import pandas as pd
import numpy as np
import os

# 定数の定義
CURRENT_PATH = os.path.dirname(__file__).split('/pdu-monitor')[0]
MONITOR_PATH = os.path.join(CURRENT_PATH, 'pdu-monitor', 'monitor')
OUTPUT_PATH = os.path.join(MONITOR_PATH, 'data')
DEVICE_DATA_PATH = '/usr/local/dummy/dummy_PDU_list.csv' # dummy
USECOLS = ['hostname', 'ip', 'dc']
DC = ['dummy_DC1', 'dummy_DC2', 'dummy_DC3']

# カレントディレクトリの設定
os.chdir(MONITOR_PATH)

def import_device_data(path):
    """
    DEVICE42のデータを収集し、特定のDC以外とIPが空欄のマシンを削除する。
    """
    df = pd.read_csv(path, usecols=USECOLS)
    df = df[df['dc'].isin(DC)].dropna(how='any')
    return df

def extract_from_basic_DC(sr):
    """
    basic_DCフォーマットのhostnameからareaとrowを抽出する。
    """
    area_and_row = sr['hostname'].split('-')
    if len(area_and_row) < 3:
        sr['area'], sr['row'], sr['num'] = '-', '-', '-'
    else:
        area_and_row = area_and_row[1]
        sr['area'], sr['row'], sr['num'] = area_and_row[0], area_and_row[1], area_and_row[2:4]
    return sr

def extract_from_dummy_DC3(sr):
    """
    dummy_DC3フォーマットのhostnameからareaとrowを抽出する。
    """
    area_and_row = sr['hostname'].split('-')[1]
    sr['area'], sr['row'], sr['num'] = area_and_row[0], area_and_row[0], area_and_row[1:4]
    return sr


def extract_area_and_row(sr):
    """
    hostnameからareaとrowを抽出する。
    """
    if sr['dc'] == 'dummy_DC3':
        sr = extract_from_dummy_DC3(sr)
    else:
        sr = extract_from_basic_DC(sr)
    return sr

def process_device_data(df):
    """
    データフレームを適切に処理し、hostnameからareaとrowを抽出する。
    """
    df = df.apply(extract_area_and_row, axis=1)
    return df

def export_device_data(df):
    """
    処理したデータフレームから必要な情報を抽出し、CSVファイルに保存する。
    """
    df = df.rename(columns={'hostname': 'PDU', 'dc': 'DC'})
    df.to_csv(os.path.join(OUTPUT_PATH, 'DEVICE_data.csv'), encoding='utf-8-sig', index=False)

def main(path):
    """
    メイン処理
    """
    df = import_device_data(path)
    df['area'], df['row'], df['num'] = np.nan, np.nan, np.nan
    df = process_device_data(df)
    export_device_data(df)

main(DEVICE_DATA_PATH)