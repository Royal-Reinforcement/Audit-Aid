import streamlit as st
import pandas as pd
import smartsheet
import re

APP_NAME = 'Audit Aid: Liaison Assignments'


@st.cache_data(ttl=300)
def smartsheet_to_dataframe(sheet_id):
    ss_client = smartsheet.Smartsheet(st.secrets['smartsheet']['access_token'])
    sheet = ss_client.Sheets.get_sheet(sheet_id)

    columns = [col.title for col in sheet.columns]
    rows = []

    for row in sheet.rows:
        row_values = []
        for cell in row.cells:
            row_values.append(getattr(cell, 'display_value', cell.value) or cell.value)
        rows.append(row_values)

    return pd.DataFrame(rows, columns=columns)





st.set_page_config(page_title=APP_NAME, page_icon='📝', layout='wide')

st.image(st.secrets['images']["rr_logo"], width=100)

st.title('📝 ' + APP_NAME)
st.info('An audit of liaison assignments within: Escapia, Breezeway, or Smartsheets.')





df          = smartsheet_to_dataframe(st.secrets['smartsheet']['sheets']['liaisons'])
df          = df[['Unit_Code','HL','OL','OL Secondary/Transition']]
df.columns  = ['Unit_Code', 'HL', 'OL', 'OL2']
df['OL2']   = df['OL2'].str.replace(r'\s*\(.*\)', '', regex=True)

for col in ['HL', 'OL', 'OL2']: df[f'{col}_First'] = df[col].str.split().str[0]

df['Assignments']   = df.drop(['Unit_Code'], axis=1).apply(lambda row: [x for x in row if pd.notnull(x)], axis=1)
df                  = df[['Unit_Code', 'Assignments']]
df                  = df.dropna(subset=['Assignments'])





tabs = st.tabs(['🗓️ Escapia','💨 Breezeway','📋 Smartsheets'])





with tabs[0]: # Escapia

    file = st.file_uploader('**Amenity String Report** | Units / Reports / Amenity String Report', type=['CSV'])

    if file:

        adf                 = pd.read_csv(file)
        adf                 = adf[['Unit_Code','Amenity_Notes']]
        adf['Assignments']  = adf['Amenity_Notes'].str.split(r'\s*[/\-]\s*').apply(lambda x: [item.strip() for item in x] if isinstance(x, list) else [])
        adf                 = adf[['Unit_Code', 'Assignments']]

        temp_df                 = df.copy()
        temp_df['Assignments']  = temp_df['Assignments'].apply(lambda x: [item for item in x if ' ' not in item])

        ea_df           = pd.merge(temp_df, adf, on='Unit_Code', suffixes=('_Liaisons', '_Escapia'))
        ea_df['Match']  = ea_df.apply(lambda row: set(row['Assignments_Liaisons']) == set(row['Assignments_Escapia']), axis=1)

        ea_df = ea_df[ea_df['Match'] == False]
        ea_df = ea_df.drop(['Match'], axis=1)


        ea_df['Remove'] = ea_df.apply(lambda row: list(set(row['Assignments_Escapia']) - set(row['Assignments_Liaisons'])), axis=1)
        ea_df['Add']    = ea_df.apply(lambda row: list(set(row['Assignments_Liaisons']) - set(row['Assignments_Escapia'])), axis=1)

        st.dataframe(ea_df, hide_index=True)





    with tabs[1]: # Breezeway

        file = st.file_uploader('**Active Units Report** | Breezeway Support', type=['CSV'])

        with st.expander('How to get the needed file', expanded=False):

            'Send an email to **support@breezeway.io** with:'
            '**Subject**: Report Request'
            '**Body**: Can you please send over the \"Export of all Active Units\" report in a CSV format?'
        
        if file:

            adf                 = pd.read_csv(file)
            adf['Unit_Code']    = adf['Property Name'].str.extract(r'\(([^)]+)\)')
            adf                 = adf[['Unit_Code','Tags','Default Inspectors','Default Maintenance']]
            adf['Tags']         = adf['Tags'].str.split(',').apply(lambda x: [item.strip() for item in x] if isinstance(x, list) else [])
            adf['Inspectors']   = adf['Default Inspectors'].str.split(',').apply(lambda x: [item.strip() for item in x] if isinstance(x, list) else [])
            adf['Maintenance']  = adf['Default Maintenance'].str.split(',').apply(lambda x: [item.strip() for item in x] if isinstance(x, list) else [])



            st.subheader('Default Inspectors')

            idf = adf.copy()
            idf['Assignments']  = idf['Inspectors']
            idf['Assignments']  = idf['Assignments'].apply(lambda x: list(set(x)))
            idf['Assignments']  = idf['Assignments'].apply(lambda items: [x for x in items if x != ".Maintenance Dispatcher"])
            idf['Assignments']  = idf['Assignments'].apply(lambda items: [x for x in items if x != ".Inspector Dispatcher"])
            idf['Assignments']  = idf['Assignments'].apply(lambda lst: [re.sub(r'\s+', ' ', x).strip() for x in lst])
            idf                 = idf[['Unit_Code', 'Assignments']]

            temp_idf                 = df.copy()
            temp_idf['Assignments']  = temp_idf['Assignments'].apply(lambda x: [item for item in x if ' ' in item])

            iea_df = pd.merge(temp_idf, idf, on='Unit_Code', suffixes=('_Liaisons', '_Breezeway_Inspectors'))
            iea_df['Match'] = iea_df.apply(lambda row: set(row['Assignments_Liaisons']) == set(row['Assignments_Breezeway_Inspectors']), axis=1)

            iea_df = iea_df[iea_df['Match'] == False]
            iea_df = iea_df.drop(['Match'], axis=1)

            iea_df['Remove'] = iea_df.apply(lambda row: list(set(row['Assignments_Breezeway_Inspectors']) - set(row['Assignments_Liaisons'])), axis=1)
            iea_df['Add']    = iea_df.apply(lambda row: list(set(row['Assignments_Liaisons']) - set(row['Assignments_Breezeway_Inspectors'])), axis=1)

            st.dataframe(iea_df, hide_index=True)
            


            st.subheader('Default Maintenance')

            mdf = adf.copy()
            mdf['Assignments']  = mdf['Maintenance']
            mdf['Assignments']  = mdf['Assignments'].apply(lambda x: list(set(x)))
            mdf['Assignments']  = mdf['Assignments'].apply(lambda items: [x for x in items if x != ".Maintenance Dispatcher"])
            mdf['Assignments']  = mdf['Assignments'].apply(lambda items: [x for x in items if x != ".Inspector Dispatcher"])
            mdf['Assignments']  = mdf['Assignments'].apply(lambda lst: [re.sub(r'\s+', ' ', x).strip() for x in lst])
            mdf                 = mdf[['Unit_Code', 'Assignments']]

            temp_mdf                 = df.copy()
            temp_mdf['Assignments']  = temp_mdf['Assignments'].apply(lambda x: [item for item in x if ' ' in item])

            mea_df = pd.merge(temp_mdf, mdf, on='Unit_Code', suffixes=('_Liaisons', '_Breezeway_Maintenance'))
            mea_df['Match'] = mea_df.apply(lambda row: set(row['Assignments_Liaisons']) == set(row['Assignments_Breezeway_Maintenance']), axis=1)

            mea_df = mea_df[mea_df['Match'] == False]
            mea_df = mea_df.drop(['Match'], axis=1)

            mea_df['Remove'] = mea_df.apply(lambda row: list(set(row['Assignments_Breezeway_Maintenance']) - set(row['Assignments_Liaisons'])), axis=1)
            mea_df['Add']    = mea_df.apply(lambda row: list(set(row['Assignments_Liaisons']) - set(row['Assignments_Breezeway_Maintenance'])), axis=1)

            st.dataframe(mea_df, hide_index=True)



            st.subheader('Property Tags')

            tdf = adf.copy()
            tdf['Assignments']  = tdf['Tags']
            tdf['Assignments']  = tdf['Assignments'].apply(lambda x: list(set(x)))
            tdf['Assignments']  = tdf['Assignments'].apply(lambda items: [x for x in items if "'s Homes" in x])
            tdf['Assignments']  = tdf['Assignments'].apply(lambda lst: [re.sub(r"'s Homes", '', x).strip() for x in lst])
            tdf                 = tdf[['Unit_Code', 'Assignments']]

            temp_tdf                 = df.copy()
            temp_tdf['Assignments']  = temp_tdf['Assignments'].apply(lambda x: [item for item in x if ' ' not in item])

            tea_df = pd.merge(temp_tdf, tdf, on='Unit_Code', suffixes=('_Liaisons', '_Breezeway_Tags'))
            tea_df['Match'] = tea_df.apply(lambda row: set(row['Assignments_Liaisons']) == set(row['Assignments_Breezeway_Tags']), axis=1)

            tea_df = tea_df[tea_df['Match'] == False]
            tea_df = tea_df.drop(['Match'], axis=1)

            tea_df['Remove'] = tea_df.apply(lambda row: list(set(row['Assignments_Breezeway_Tags']) - set(row['Assignments_Liaisons'])), axis=1)
            tea_df['Add']    = tea_df.apply(lambda row: list(set(row['Assignments_Liaisons']) - set(row['Assignments_Breezeway_Tags'])), axis=1)

            st.dataframe(tea_df, hide_index=True)




    with tabs[2]: # Smartsheets

        @st.cache_data
        def load_sheet(sheet_id):
            return smartsheet_to_dataframe(sheet_id)

        sheet_id = st.text_input('**Smartsheet Sheet ID**', placeholder='Found on a Smartsheet, under: File, Properties, Sheet ID', key='sheet_id')

        if st.button('Load Sheet', key='load_sheet_btn'):
            st.session_state['adf'] = load_sheet(sheet_id)

        if 'adf' in st.session_state:
            adf = st.session_state['adf'].copy()
            
            col_unitcode = st.selectbox('**Unit_Code Column**', options=adf.columns.tolist(), key='col_unitcode')
            col_liaisons = st.multiselect('**Liaisons Column(s)**', options=adf.columns.tolist(), placeholder='Select one or more columns that contain liaison assignments', key='col_hl')

            if not col_unitcode or not col_liaisons:
                st.warning('Please select both the Unit Code column and at least one House Liaisons column.')
                st.stop()

            adf = adf[[col_unitcode] + col_liaisons]
            
            for column in col_liaisons:
                adf[column] = adf[column].str.split(',').apply(lambda x: [item.strip() for item in x] if isinstance(x, list) else [])
            
            adf['Assignments']  = adf[col_liaisons].apply(lambda row: [item for sublist in row for item in sublist], axis=1)
            adf['Assignments']  = adf['Assignments'].apply(lambda x: list(set(x)))
            adf['Assignments']  = adf['Assignments'].apply(lambda lst: [re.sub(r'\s+', ' ', x).strip() for x in lst])
            adf                 = adf[[col_unitcode, 'Assignments']]
            adf.columns         = ['Unit_Code', 'Assignments']

            temp_df                 = df.copy()
            temp_df['Assignments']  = temp_df['Assignments'].apply(lambda x: [item for item in x if ' ' in item])

            ea_df           = pd.merge(temp_df, adf, on='Unit_Code', suffixes=('_Liaisons', '_Smartsheet'))
            ea_df['Match']  = ea_df.apply(lambda row: set(row['Assignments_Liaisons']) == set(row['Assignments_Smartsheet']), axis=1)

            ea_df = ea_df[ea_df['Match'] == False]
            ea_df = ea_df.drop(['Match'], axis=1)


            ea_df['Remove'] = ea_df.apply(lambda row: list(set(row['Assignments_Smartsheet']) - set(row['Assignments_Liaisons'])), axis=1)
            ea_df['Add']    = ea_df.apply(lambda row: list(set(row['Assignments_Liaisons']) - set(row['Assignments_Smartsheet'])), axis=1)

            st.dataframe(ea_df, hide_index=True)