import pandas as pd
import streamlit as st

# 1. Excel faylını oxuyuruq
df = pd.read_excel("fayl_adiniz.xlsx")

# Sütun adlarındakı artıq boşluqları təmizləyirik
df.columns = df.columns.str.strip()

# 2. Tarix sütununu datetime formatına salırıq
df['Tarix'] = pd.to_datetime(df['Tarix'], dayfirst=True, errors='coerce')

# 3. 'Mal qalığı (ədəd)' sütununu ədəd formatına çeviririk (tire '-' və ya boşluqları 0 edirik)
df['Mal qalığı (ədəd)'] = pd.to_numeric(df['Mal qalığı (ədəd)'].astype(str).str.replace('-', '0'), errors='coerce').fillna(0)

# 4. Əgər hər bir Mağaza + Məhsul üçün son tarixdəki QALIĞI görmək istəyirsinizsə:
# Əvvəlcə tarixlərə görə sıralayırıq
df = df.sort_values(by=['Mağaza', 'Məhsulun 1C kod', 'Tarix'])

# Hər mağaza və məhsul üzrə ən son sətri (son vəziyyəti) götürürük
df_qaliq = df.groupby(['Mağaza', 'Məhsulun 1C kod']).last().reset_index()

# Yalnız lazımi sütunları seçirik
df_qaliq = df_qaliq[['Mağaza', 'Məhsulun 1C kod', 'Mal qalığı (ədəd)']]

# Şərti filter: Əgər yalnız qalığı 0-dan böyük olanları göstərmək istəyirsinizsə:
# df_qaliq = df_qaliq[df_qaliq['Mal qalığı (ədəd)'] > 0]

st.dataframe(df_qaliq, use_container_width=True)
