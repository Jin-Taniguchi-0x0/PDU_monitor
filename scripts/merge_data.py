import pandas as pd
import numpy as np
import os

CURRENT_PATH = os.path.dirname(__file__).split('scripts')[0]
os.chdir(CURRENT_PATH)



DATA_PATH = CURRENT_PATH + '/data/'

DEVICE_DATA_NAME = 'DEVICE_data.csv'
SNMP_DATA_NAME = 'SNMP_data.csv'
STATUS_DATA_NAME = 'Status_data.csv'

SNMP_timestamp_LENGTH = 5

OUTPUT_NAME = 'MERGE.csv'

INDEX_COL_NAME = 'PDU'

OUTPUT_COLUMN_LIST = ['PDU',
                      'Latest power',
                      'Latest time',
                      'Monitor status',
                      'Status lock',
                      'Change time',
                      'Reason'
                      ]

def process_DEVICE_df(df):
    print('test')

def process_SNMP_df(df):
    latest_time = df.columns[df.shape[1] - 1]
    latest_power_sr = df[latest_time]
    return (latest_time, latest_power_sr)

def process_Status_df(df):
    print('test')


def merge_basic_data():
    df_DEVICE_data = pd.read_csv(DATA_PATH + DEVICE_DATA_NAME, index_col=INDEX_COL_NAME, encoding='utf-8-sig')
    df_SNMP_data = pd.read_csv(DATA_PATH + SNMP_DATA_NAME, index_col=INDEX_COL_NAME, encoding='utf-8-sig')
    df_Status_data = pd.read_csv(DATA_PATH + STATUS_DATA_NAME, index_col=INDEX_COL_NAME, encoding='utf-8-sig')

    #DEVICEリストにあるが、statusにないpduに、default statusで初期化
    missing_pdus = df_DEVICE_data[~df_DEVICE_data.index.isin(df_Status_data.index)]

    default_status = pd.DataFrame({'Latest power': [np.nan] * missing_pdus.shape[0],
                                   'Latest time': [np.nan] * missing_pdus.shape[0],
                                   'Monitor status': ['Enable'] * missing_pdus.shape[0],
                                  'Status lock': [np.nan] * missing_pdus.shape[0],
                                  'Change time': [np.nan] * missing_pdus.shape[0],
                                  'Reason': [np.nan] * missing_pdus.shape[0]
                                  },
                                  index=missing_pdus.index
                                  )

    missing_merge = pd.concat([missing_pdus, default_status], axis=1)

    # Monitor statusがEnableの行をフィルタリング
    enabled_status = df_Status_data[df_Status_data['Monitor status'] == 'Enable']

    # When performing the join or merge, specify suffixes for the overlapping columns
    enabled_merge = df_DEVICE_data.join(enabled_status, how='inner', lsuffix='_device', rsuffix='_status')



    # Monitor statusがDisableの行をフィルタリング
    disabled_status = df_Status_data[df_Status_data['Monitor status'] == 'Disable']

    disabled_merge = df_DEVICE_data.join(disabled_status, how='inner', lsuffix='_device', rsuffix='_status')


    # データフレーム結合
    df_merge = pd.concat([missing_merge, enabled_merge, disabled_merge])
    df_merge = df_merge.sort_index()

    # 結果の表示

    
    def update_latest_power(sr, latest_time, latest_power_sr):
        
        if sr.name in latest_power_sr.index:
            if sr['Monitor status'] == 'Disable':
                return sr
            elif latest_power_sr[sr.name] in ['Alert', np.nan]:
                sr['Latest result'] = 'Alert'
                return sr
            elif sr['Monitor status'] == 'Enable':
                sr['Latest power'] = latest_power_sr[sr.name]
                sr['Latest time'] = latest_time
                return sr
        else:
            return sr

        
        



    latest_time, latest_power_sr = process_SNMP_df(df_SNMP_data)

    print(latest_power_sr)

    df_merge = df_merge.apply(update_latest_power, latest_time = latest_time, latest_power_sr = latest_power_sr, axis=1)

    df_merge.to_csv(DATA_PATH + OUTPUT_NAME, encoding='utf-8-sig')



if __name__ == '__main__':
    print(SNMP_timestamp_LENGTH)

merge_basic_data()
