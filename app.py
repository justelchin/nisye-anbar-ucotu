import pandas as pd
import streamlit as st

st.set_page_config(page_title="Satılmamış Mal Qalıqları", layout="wide")

st.title("🏪 Mağazalardakı Satılmamış Mal Qalıqları")

# 1. Excel faylını yükləmək üçün düymə (və ya birbaşa fayl yolu)
uploaded_file = st.file_uploader("Excel faylını seçin", type=["xlsx", "xls"])

if uploaded_file is not None:
    # Excel faylını oxuyuruq
    df = pd.read_excel(uploaded_file)

    # Sütun adlarındakı artıq boşluqları təmizləyirik
    df.columns = df.columns.str.strip()

    # 2. Tarix sütununu datetime formatına salırıq
    if 'Tarix' in df.columns:
        df['Tarix'] = pd.to_datetime(df['Tarix'], dayfirst=True, errors='coerce')

    # 3. 'Mal qalığı (ədəd)' sütunundakı '-' (tire) və boş xanaları 0 ilə əvəz edirik
    if 'Mal qalığı (ədəd)' in df.columns:
        df['Mal qalığı (ədəd)'] = (
            df['Mal qalığı (ədəd)']
            .astype(str)
            .str.replace('-', '0')
            .str.strip()
        )
        df['Mal qalığı (ədəd)'] = pd.to_numeric(df['Mal qalığı (ədəd)'], errors='coerce').fillna(0)

    # 4. Mağaza və Məhsulun 1C kodu üzrə tarixləri sıralayırıq
    if 'Tarix' in df.columns:
        df = df.sort_values(by=['Mağaza', 'Məhsulun 1C kod', 'Tarix'])

    # 5. Hər mağaza və məhsul üzrə ən son tarixdəki sətri götürürük
    df_qaliq = df.groupby(['Mağaza', 'Məhsulun 1C kod'], as_index=False).last()

    # Yalnız lazımi sütunları seçirik
    df_qaliq = df_qaliq[['Mağaza', 'Məhsulun 1C kod', 'Mal qalığı (ədəd)']]

    # Sütun adlarını ekranda düzgün göstərmək üçün dəyişirik
    df_qaliq.columns = ['Mağaza', 'Məhsul', 'Obyektdə Qalan Mal (ədəd)']

    # 6. Nəticə cədvəlini göstəririk (hide_index=True indeksi gizlədir)
    st.dataframe(df_qaliq, hide_index=True, use_container_width=True)

else:
    st.info("Zəhmət olmasa, hesablamaq üçün Excel faylını yükləyin.")
