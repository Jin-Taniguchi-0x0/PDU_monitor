import streamlit as st
import pandas as pd
import numpy as np
import os
import datetime
from scripts import merge_data

# 定数の定義
#CURRENT_PATHは他ファイルで定義すべき？
CURRENT_PATH = os.path.dirname(__file__).split('/pdu-monitor')[0]
CURRENT_PATH = CURRENT_PATH
os.chdir(CURRENT_PATH)

DATA_PATH = CURRENT_PATH + '/data/'
MERGE_CSV_NAME = 'MERGE.csv'
STATUS_LOCK_FLAG = 'LOCK'
STATUS_MONITOR_FLAG = 'Enable'

# カレントディレクトリの設定
os.chdir(CURRENT_PATH)

# スタイル設定関数
def style_row_by_status(row):
    color = ''
    if row['Latest result'] == 'Alert':
        color = '#dc143c'
    if row['Monitor status'] == 'Disable':
        color = '#dcdcdc'
    if row['Status lock'] == STATUS_LOCK_FLAG:
        color = '#a9a9a9'
    return [f'background-color: {color}'] * len(row)

# Streamlitのページ設定
def set_config():
    st.set_page_config(
        page_title="DPU monitor function",
        page_icon="🖥️",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://www.extremelycoolapp.com/help',
            'Report a bug': "https://www.extremelycoolapp.com/bug",
            'About': "# This is a header. This is an *extremely* cool app!"
        }
    )

# データエディタのレンダリング
def render_data_editor():
    mask = filter_dataframe(st.session_state.df_pdu_display)
    st.session_state.df_pdu_display_editing = st.data_editor(
        st.session_state.df_pdu_display[mask].style.apply(style_row_by_status, axis=1),
        column_config={
            "Status": st.column_config.CheckboxColumn("check"),
            'Reason': st.column_config.TextColumn()
        },
        disabled=[col for col in st.session_state.df_pdu_display.columns if col not in ['Status', 'Reason']],
        hide_index=True,
        column_order=['Status', 'PDU', 'Latest power', 'Latest time', 'Latest result', 'Monitor status', 'Change time', 'Status lock', 'Reason'],
        key="data_editor_checkbox" + str(st.session_state.count)
    )


# データフレームのフィルタリング
def filter_dataframe(df):
    if 'filters' not in st.session_state:
        st.session_state.filters = [{'column': '', 'value': ''}]

    st.sidebar.header('Filters')
    for i, filter in enumerate(st.session_state.filters):
        col1, col2, col3 = st.sidebar.columns([1, 2, 2])
        with col1:
            st.markdown(f'<div style="display: flex; align-items: center;">'
                        f'<span style="margin-right: 5px;">rm filter {i+1}</span>'
                        f'</div>', unsafe_allow_html=True)
            if st.button('remove', key=f'remove_{i}'):
                st.session_state.filters.pop(i)
                rerun_holding_editing_status(status_flag=True, reason_flag=True)
        filter['column'] = col2.selectbox(f'Select column {i+1}', [''] + list(df.columns), key=f'column_{i}')
        if filter['column']:
            filter['value'] = col3.selectbox(f'Select value {i+1}', [''] + list(df[filter['column']].unique()), key=f'value_{i}')
            rerun_holding_editing_status(status_flag=False, reason_flag=True, rerun_flag=False)
        else:
            filter['value'] = col3.selectbox(f'Select value {i+1}', [''], key=f'value_{i}')

    if st.sidebar.button('Add filter condition'):
        st.session_state.filters.append({'column': '', 'value': ''})
        rerun_holding_editing_status(status_flag=True, reason_flag=True)

    mask = pd.Series([True] * len(df))
    for filter in st.session_state.filters:
        if filter['value']:
            mask &= df[filter['column']].astype(str).str.contains(filter['value'], case=False)
    return mask

# 編集状態を保持して再実行
def rerun_holding_editing_status(status_flag, reason_flag, rerun_flag=True):
    sr_flag_tmp = st.session_state.df_pdu_display['PDU'].isin(st.session_state.df_pdu_display_editing['PDU'])
    if status_flag:
        st.session_state.df_pdu_display.loc[sr_flag_tmp, 'Status'] = st.session_state.df_pdu_display_editing['Status']
    if reason_flag:
        st.session_state.df_pdu_display.loc[sr_flag_tmp, 'Reason'] = st.session_state.df_pdu_display_editing['Reason']
    if rerun_flag:
        st.session_state.count += 1
        st.rerun(scope='app')

# 現在時刻のフォーマット
def get_formatted_nowtime():
    nowtime = datetime.datetime.now()
    return nowtime.strftime('%Y/%m/%d %H:%M')

# サイドバーのボタン処理
def handle_sidebar_buttons():
    st.sidebar.header('Check')
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("Check all", use_container_width=True):
            st.session_state.df_pdu_display['Status'] = True
            rerun_holding_editing_status(status_flag=False, reason_flag=True)
    with col2:
        if st.button("Reset check", use_container_width=True):
            st.session_state.df_pdu_display['Status'] = False
            rerun_holding_editing_status(status_flag=False, reason_flag=True)

    st.sidebar.header('Enable/Disable monitor status')
    col3, col4 = st.sidebar.columns(2)
    with col3:
        if st.button("Enable", use_container_width=True):
            update_monitor_status('Enable')
    with col4:
        if st.button("Disable", use_container_width=True):
            update_monitor_status('Disable')

    st.sidebar.header('Lock status')
    col5, col6 = st.sidebar.columns(2)
    with col5:
        if st.button("Lock", use_container_width=True):
            update_lock_status(STATUS_LOCK_FLAG)
    with col6:
        if st.button("Lock off", use_container_width=True):
            update_lock_status(None)

    st.sidebar.header('Reset your edits')
    if st.sidebar.button("Reset", use_container_width=True):
        reset_edit()

    st.sidebar.header('Save edit')
    if st.sidebar.button('Save', use_container_width=True, type='primary'):
        save_selected_columns_to_csv(st.session_state.df_pdu_display, './data/Status_data.csv')

# モニターステータスの更新
def update_monitor_status(status):
    sr_flag_checkbox = st.session_state.df_pdu_display_editing['Status']
    sr_flag_lock = st.session_state.df_pdu_display_editing['Status lock'] != STATUS_LOCK_FLAG
    sr_flag_tmp = sr_flag_lock & sr_flag_checkbox

    if (sr_flag_checkbox != sr_flag_tmp).any():
        st.session_state.lock_warning = True

    sr_flag_tmp = st.session_state.df_pdu_display['PDU'].isin(st.session_state.df_pdu_display_editing.loc[sr_flag_tmp, 'PDU'])
    st.session_state.df_pdu_display.loc[sr_flag_tmp, 'Monitor status'] = status
    st.session_state.df_pdu_display.loc[sr_flag_tmp, 'Change time'] = get_formatted_nowtime()

    rerun_holding_editing_status(status_flag=True, reason_flag=True)

# ロックステータスの更新
def update_lock_status(lock_status):
    sr_flag_checkbox = st.session_state.df_pdu_display_editing['Status']
    sr_flag_monitor = st.session_state.df_pdu_display_editing['Monitor status'] != STATUS_MONITOR_FLAG
    sr_flag_tmp = sr_flag_monitor & sr_flag_checkbox

    if (sr_flag_checkbox != sr_flag_tmp).any():
        st.session_state.enable_warning = True

    sr_flag_tmp = st.session_state.df_pdu_display['PDU'].isin(st.session_state.df_pdu_display_editing.loc[sr_flag_tmp, 'PDU'])
    st.session_state.df_pdu_display.loc[sr_flag_tmp, 'Status lock'] = lock_status
    st.session_state.df_pdu_display.loc[sr_flag_tmp, 'Change time'] = get_formatted_nowtime()

    rerun_holding_editing_status(status_flag=True, reason_flag=True)

# データフレームの表示とチェックボックスの処理
def write_df_with_checkbox():
    st.title('PDU monitor')

    if 'count' not in st.session_state:
        st.session_state.count = 0

    if st.session_state.lock_warning:
        st.warning('Lock status warning: can\'t change monitor status which status is locked', icon="⚠️")
        st.session_state.lock_warning = False

    if st.session_state.enable_warning:
        st.warning('Monitor status warning: can\'t lock status which monitor status is enable', icon="⚠️")
        st.session_state.enable_warning = False
    

    render_data_editor()
    handle_sidebar_buttons()

# 編集のリセット
@st.dialog("Reset")
def reset_edit():
    st.write('Reset your edits?')
    if st.button("Reset"):
        st.session_state.clear()
        st.write()
        st.rerun(scope='app')

# CSVへの保存
@st.dialog("save")
def save_selected_columns_to_csv(df, output_file_path):
    st.write('Really save your edits? can\'t roll back')
    if st.button('Save', type='primary'):
        columns_to_extract = ['PDU', 'Latest power', 'Latest time', 'Latest result', 'Monitor status', 'Status lock', 'Change time', 'Reason']
        df_extracted = df[columns_to_extract]
        df_extracted.to_csv(output_file_path, index=False)
        merge_data.merge_basic_data()
        st.rerun(scope='app')

# メイン処理
if 'df_pdu_display' not in st.session_state:
    set_config()
    df_pdu_display = pd.read_csv(DATA_PATH + MERGE_CSV_NAME, encoding='utf-8-sig')
    df_pdu_display.insert(0, 'Status', False)
    df_pdu_display['Reason'] = df_pdu_display['Reason'].fillna('')
    df_pdu_display['Reason'] = df_pdu_display['Reason'].astype(str)  # Ensure 'Reason' column is of type string
    st.session_state.df_pdu_display = df_pdu_display
    st.session_state.lock_warning = False
    st.session_state.enable_warning = False

write_df_with_checkbox()
rerun_holding_editing_status(status_flag=False, reason_flag=False, rerun_flag=False)
