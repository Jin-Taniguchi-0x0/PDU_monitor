import pandas as pd
import os
import datetime
from easysnmp import snmp_get, EasySNMPTimeoutError
from email.mime.text import MIMEText
import smtplib

CURRENT_PATH = os.path.dirname(__file__).split('/pdu-monitor')[0]
os.chdir(CURRENT_PATH)

DATA_PATH = 'data/'

DEVICE_DATA_NAME = 'DEVICE_data.csv'
SNMP_DATA_NAME = 'SNMP_data.csv'

SNMP_timestamp_LENGTH = 5

INDEX_COL_NAME = 'PDU'

SCHNEIDER_OID = '.1.3.3.3.8.3.438.3.1.48.3.3.1.7.1' #dummy OID
RARITAN_OID = '.1.3.4.1.5.2.12527.3.5.2.5.1.4.7.8.5' #dummy OID




def assign_oid(dc):
    if dc == 'JPE1':
        oid = SCHNEIDER_OID
    else:
        oid = RARITAN_OID

    return oid

def snmpget_pdu(sr):
    oid = assign_oid(sr['DC'])
    ip = sr['ip']

    value = ''
    
    try:
        system_items = snmp_get(oid, hostname=ip, community='public', version=2)
        # 必要に応じて system_items を処理
        print(f"IP: {ip} のSNMPウォークが成功しました") #test
        value = system_items.value
    except EasySNMPTimeoutError:
        print(f"IP: {ip} への接続中にタイムアウトが発生しました") #test
        value = 'Alert'
    except Exception as e:
        print(f"IP: {ip} のSNMPウォーク中にエラーが発生しました。エラー: {e}")
        value = 'Alert'

    return value

def update_SNMP_data(df, current_time):
    #SNMP_dataを読み込み、古いデータを削除して新しいデータを書き込む
    #書き込むデータのカラム名は現在時刻
    # 現在時刻を取得し、カラム名として使用
    
    
    # 既存のSNMPデータを読み込む


    SNMP_data_df = pd.read_csv(DATA_PATH + SNMP_DATA_NAME, index_col=INDEX_COL_NAME, encoding='utf-8-sig')

    # 古いデータを削除（ここでは、SNMP_timestamp_LENGTHを超える古いデータを削除）
    if len(SNMP_data_df.columns) >= SNMP_timestamp_LENGTH:
        SNMP_data_df = SNMP_data_df.iloc[:, 1:SNMP_timestamp_LENGTH]

    # 新しいデータを追加
    SNMP_data_df = pd.merge(SNMP_data_df, df[current_time], left_index=True, right_index=True, how='outer')

    print(SNMP_data_df)

    SNMP_data_df.to_csv(DATA_PATH + SNMP_DATA_NAME, encoding='utf-8-sig')

    return 0


def mail_send(sr, timestamp):
    wattage, PDU = sr[timestamp], sr.name
    dlm = 'dummy-pdu-monitor-email@rakpd.pagerduty.com'
 
    # MIMEText
    message = ''
    message += f'Timestamp: {timestamp}' + '\n'
    message += 'Alert: PDU response error - ' + PDU + '\n'
    message += 'Link: http://dummy.prod.jp.local/' + '\n'
    msg = MIMEText(message, 'plain')
    
    msg["Subject"] = 'Alert: PDU response error:' + PDU
    msg["To"] = dlm
    msg["From"] = dlm

    server = smtplib.SMTP('localhost')
    server.send_message(msg)
    server.quit()
    

if __name__ == '__main__':
    df = pd.read_csv(DATA_PATH + DEVICE_DATA_NAME, index_col=INDEX_COL_NAME, encoding='utf-8-sig')
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    df[current_time] = df.apply(snmpget_pdu, axis=1)
    update_SNMP_data(df, current_time)
    df[df[current_time] == 'Alert'].apply(mail_send, timestamp = current_time, axis=1)
