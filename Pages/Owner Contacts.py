import streamlit as st
import pandas as pd
import re

APP_NAME = 'Audit Aid: Owner Contacts'

st.set_page_config(page_title=APP_NAME, page_icon='📝', layout='wide')

st.image(st.secrets['images']["rr_logo"], width=100)

st.title('📝 ' + APP_NAME)
st.info('An audit of owner contacts between Escapia and Salesforce.')

c1, c2     = st.columns(2)

escapia    = c1.file_uploader('**Owner Contact Report.csv** | Escapia / Admin / Reports / Owner Contact Report', type=['CSV'])
salesforce = c2.file_uploader('**Salesforce Contacts.xslx** | Salesforce', type=['XLSX'])


if escapia and salesforce:

    edf = pd.read_csv(escapia)
    sdf = pd.read_excel(salesforce)

    edf = edf[['Units','Email','Phone_1','Phone_2','Phone_3','Phone_4']]
    sdf = sdf[['Account Name','Email','Phone']]

    def extract_codes(text):

        if '(' in text and ')' in text:
            inside = re.search(r'\((.*?)\)', text)
            if inside:
                content = inside.group(1)
                parts = re.split(r'[&/]', content)
                return [p.strip() for p in parts]
        
        if ' - ' in text:
            return [text.split(' - ')[0].strip()]
        
        return [text.strip()]

    sdf = sdf.assign(Unit_Code=sdf['Account Name'].apply(extract_codes))
    sdf = sdf.explode('Unit_Code', ignore_index=True)

    def clean_phone(series, validate=True):

        cleaned = series.astype(str).str.replace(r'\D', '', regex=True).str[-10:]
    
        if validate: cleaned = cleaned.where(cleaned.str.len() == 10, pd.NA)
    
        return cleaned
    
    escapia_phone_columns    = ['Phone_1','Phone_2','Phone_3','Phone_4']
    salesforce_phone_columns = ['Phone']

    for col in escapia_phone_columns: edf[col] = clean_phone(edf[col])
    for col in salesforce_phone_columns: sdf[col] = clean_phone(sdf[col])

    edf = edf.rename(columns={'Units':'Unit_Code'})

    edf = edf[['Unit_Code','Email','Phone_1','Phone_2','Phone_3','Phone_4']]
    sdf = sdf[['Unit_Code','Email','Phone']]

    escapia_columns    = ['Email','Phone_1','Phone_2','Phone_3','Phone_4']
    salesforce_columns = ['Email','Phone']

    edf['List'] = edf[escapia_columns].apply(lambda row: set(row.dropna()), axis=1)
    sdf['List'] = sdf[salesforce_columns].apply(lambda row: set(row.dropna()), axis=1)

    edf = edf.groupby('Unit_Code', as_index=False).agg({'List': lambda x: set().union(*x)})
    sdf = sdf.groupby('Unit_Code', as_index=False).agg({'List': lambda x: set().union(*x)})

    df = edf.merge(sdf, on='Unit_Code', how='outer', suffixes=('_Escapia', '_Salesforce'))

    for col in ["List_Escapia", "List_Salesforce"]: df[col] = df[col].apply(lambda x: x if isinstance(x, set) else set())

    df.columns = ['Unit_Code','Escapia','Salesforce']

    df['Add to Salesforce'] = df.apply(lambda row: row['Escapia'] - row['Salesforce'], axis=1)
    df['Add to Escapia']    = df.apply(lambda row: row['Salesforce'] - row['Escapia'], axis=1)

    st.dataframe(df, width='stretch', hide_index=True)