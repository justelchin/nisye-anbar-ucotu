import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Səhifə konfiqurasiyası
st.set_page_config(page_title="Nisyə və Anbar Uçotu", layout="wide", page_icon="📦")

# Məlumat fayllarının yoxlanılması və yaradılması
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

STORES_FILE = os.path.join(DATA_DIR, "stores.csv")
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.csv")
TRANSACTIONS_FILE = os.path.join(DATA_DIR, "transactions.csv")
PAYMENTS_FILE = os.path.join(DATA_DIR, "payments.csv")

def load_data(file_path, columns):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return pd.DataFrame(columns=columns)

def save_data(df, file_path):
    df.to_csv(file_path, index=False)

# Məlumat bazalarını yükləyirik
stores_df = load_data(STORES_FILE, ["id", "store_name", "phone", "note"])
products_df = load_data(PRODUCTS_FILE, ["id", "code_1c", "product_name", "unit_price", "stock_qty"])
transactions_df = load_data(TRANSACTIONS_FILE, ["id", "date", "store_name", "product_name", "qty", "price", "total_amount"])
payments_df = load_data(PAYMENTS_FILE, ["id", "date", "store_name", "amount", "note"])

st.title("📦 Qeyri-rəsmi Nisyə və Anbar Uçotu Sistemi")

# Yan menyu
menu = st.sidebar.radio("Bölmələr", [
    "📊 Əsas Hesabatlar (Dashboard)",
    "📥 1C / Excel Faylı İnteqrasiyası",
    "🏪 Mağazalar",
    "📦 Anbar / Məhsullar",
    "🚚 Nisyə Mal Çıxışı",
    "💰 Borc Ödənişi Qəbulu",
    "📜 Hərəkət Tarixçəsi (Akt Sverki)"
])

# --- 1. ƏSAS HESABATLAR ---
if menu == "📊 Əsas Hesabatlar (Dashboard)":
    st.header("📊 Ümumi Borc və Mal Qalıqları Hesabatı")
    
    total_sales = transactions_df.groupby("store_name")["total_amount"].sum() if not transactions_df.empty else pd.Series(dtype=float)
    total_paid = payments_df.groupby("store_name")["amount"].sum() if not payments_df.empty else pd.Series(dtype=float)
    
    stores_summary = pd.DataFrame({"store_name": stores_df["store_name"] if not stores_df.empty else []})
    if not stores_summary.empty:
        stores_summary["Ümumi Mal Alışı (AZN)"] = stores_summary["store_name"].map(total_sales).fillna(0)
        stores_summary["Ödənilən (AZN)"] = stores_summary["store_name"].map(total_paid).fillna(0)
        stores_summary["Qalan Borc (AZN)"] = stores_summary["Ümumi Mal Alışı (AZN)"] - stores_summary["Ödənilən (AZN)"]
    
    col1, col2, col3 = st.columns(3)
    total_debt = stores_summary["Qalan Borc (AZN)"].sum() if not stores_summary.empty else 0
    total_stock_val = (products_df["unit_price"] * products_df["stock_qty"]).sum() if not products_df.empty else 0
    
    col1.metric("💰 Ümumi Alacaq Borc Qalıqları", f"{total_debt:.2f} AZN")
    col2.metric("📦 Anbardakı Mal Dəyəri", f"{total_stock_val:.2f} AZN")
    col3.metric("🏪 Aktiv Mağaza Sayı", len(stores_df))
    
    st.divider()
    
    st.subheader("🔴 Mağazaların Borc Qalıqları Siyahısı")
    if not stores_summary.empty:
        st.dataframe(stores_summary, use_container_width=True)
    else:
        st.info("Hələ heç bir mağaza qeydiyyatı yoxdur.")

    st.divider()

    st.subheader("📦 Anbar Mal Qalıqları Siyahısı")
    if not products_df.empty:
        st.dataframe(products_df[["code_1c", "product_name", "unit_price", "stock_qty"]].rename(columns={
            "code_1c": "1C Kodu",
            "product_name": "Məhsulun Adı",
            "unit_price": "Satış Qiyməti (AZN)",
            "stock_qty": "Anbardakı Qalıq Miqdarı"
        }), use_container_width=True)
    else:
        st.info("Anbarda məhsul yoxdur.")

# --- 2. EXCEL İNTEQRASİYASI ---
elif menu == "📥 1C / Excel Faylı İnteqrasiyası":
    st.header("📥 Sizin Excel Faylınızdan Toplu Məlumat Yükləmə")
    st.info("Sizin cədvəl strukturunuza uyğun olaraq: **Tarix, Mağaza, Məhsulun 1C kod, Məhsulun adı, Miqdar, Qiymət, Məbləğ, Ödənilən pul** sütunları avtomatik oxunacaq.")
    
    uploaded_file = st.file_uploader("Excel (.xlsx və ya .csv) Faylını Bura Sürüşdürün", type=["xlsx", "csv"])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df_excel = pd.read_csv(uploaded_file)
            else:
                df_excel = pd.read_excel(uploaded_file)
            
            st.write("📋 Fayldan Oxunan Məlumat Nümunəsi:", df_excel.head())
            
            if st.button("🚀 Bütün Məlumatları Sistemə İnteqrasiya Et"):
                # 1. Mağazaların əlavə edilməsi
                if "Mağaza" in df_excel.columns:
                    unique_stores = df_excel["Mağaza"].dropna().unique()
                    for s in unique_stores:
                        if s not in stores_df["store_name"].values:
                            new_id = len(stores_df) + 1
                            stores_df = pd.concat([stores_df, pd.DataFrame([{"id": new_id, "store_name": s, "phone": "", "note": "Excel-dən yükləndi"}])], ignore_index=True)
                    save_data(stores_df, STORES_FILE)
                
                # 2. Məhsulların əlavə edilməsi və qalıqları
                if "Məhsulun adı" in df_excel.columns:
                    for _, row in df_excel.iterrows():
                        p_name = row.get("Məhsulun adı")
                        if pd.isna(p_name):
                            continue
                        code_1c = str(row.get("Məhsulun 1C kod", ""))
                        price = float(row.get("Qiymət", 0.0)) if not pd.isna(row.get("Qiymət")) else 0.0
                        stock = int(row.get("Mal qalığı (ədəd)", 0)) if not pd.isna(row.get("Mal qalığı (ədəd)")) else 0
                        
                        if p_name not in products_df["product_name"].values:
                            new_id = len(products_df) + 1
                            products_df = pd.concat([products_df, pd.DataFrame([{
                                "id": new_id, "code_1c": code_1c, "product_name": p_name, "unit_price": price, "stock_qty": stock
                            }])], ignore_index=True)
                        else:
                            # Mövcuddursa qalığı yeniləyirik
                            products_df.loc[products_df["product_name"] == p_name, "stock_qty"] = stock
                    save_data(products_df, PRODUCTS_FILE)
                
                # 3. Tarixçə (Verilən mallar və ödənişlər)
                for _, row in df_excel.iterrows():
                    date_val = str(row.get("Tarix", datetime.now().strftime("%Y-%m-%d")))
                    s_name = row.get("Mağaza")
                    p_name = row.get("Məhsulun adı")
                    qty = row.get("Miqdar", 0)
                    price = row.get("Qiymət", 0)
                    total = row.get("Məbləğ", 0)
                    paid = row.get("Ödənilən pul", 0)
                    
                    if not pd.isna(s_name) and not pd.isna(p_name) and qty > 0:
                        new_trans_id = len(transactions_df) + 1
                        transactions_df = pd.concat([transactions_df, pd.DataFrame([{
                            "id": new_trans_id, "date": date_val, "store_name": s_name,
                            "product_name": p_name, "qty": qty, "price": price, "total_amount": total
                        }])], ignore_index=True)
                    
                    if not pd.isna(s_name) and paid > 0:
                        new_pay_id = len(payments_df) + 1
                        payments_df = pd.concat([payments_df, pd.DataFrame([{
                            "id": new_pay_id, "date": date_val, "store_name": s_name, "amount": paid, "note": "Excel tarixi ödəniş"
                        }])], ignore_index=True)
                
                save_data(transactions_df, TRANSACTIONS_FILE)
                save_data(payments_df, PAYMENTS_FILE)
                
                st.success("✅ Məlumatlar uğurla yükləndi! Mağazalar, məhsullar, anbar qalıqları və keçmiş borclar bazaya əlavə olundu.")
                st.rerun()
                
        except Exception as e:
            st.error(f"Fayl oxunarkən xəta baş verdi: {e}")

# --- 3. MAĞAZALAR ---
elif menu == "🏪 Mağazalar":
    st.header("🏪 Mağazaların Siyahısı Və Əlavə Edilməsi")
    with st.form("add_store"):
        store_name = st.text_input("Mağaza / Obyekt Adı")
        phone = st.text_input("Telefon Nömrəsi")
        note = st.text_area("Qeyd")
        submit = st.form_submit_button("Əlavə Et")
        
        if submit and store_name:
            new_id = len(stores_df) + 1
            new_row = {"id": new_id, "store_name": store_name, "phone": phone, "note": note}
            stores_df = pd.concat([stores_df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(stores_df, STORES_FILE)
            st.success(f"'{store_name}' uğurla əlavə olundu!")
            st.rerun()

    st.subheader("Mövcud Mağazalar Siyahısı")
    st.dataframe(stores_df, use_container_width=True)

# --- 4. ANBAR / MƏHSULLAR ---
elif menu == "📦 Anbar / Məhsullar":
    st.header("📦 Məhsullar Və Anbar Qalıqları")
    with st.form("add_product"):
        code_1c = st.text_input("1C Kodu (Seçilməyə də bilər)")
        product_name = st.text_input("Məhsulun Adı")
        unit_price = st.number_input("Satış Qiyməti (AZN)", min_value=0.0, step=0.1)
        stock_qty = st.number_input("Anbardakı İlkin Miqdar", min_value=0, step=1)
        submit = st.form_submit_button("Məhsul Əlavə Et")
        
        if submit and product_name:
            new_id = len(products_df) + 1
            new_row = {"id": new_id, "code_1c": code_1c, "product_name": product_name, "unit_price": unit_price, "stock_qty": stock_qty}
            products_df = pd.concat([products_df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(products_df, PRODUCTS_FILE)
            st.success(f"'{product_name}' bazaya əlavə olundu!")
            st.rerun()

    st.subheader("Anbardakı Qalıqlar")
    st.dataframe(products_df, use_container_width=True)

# --- 5. NISYƏ MAL ÇIXIŞI ---
elif menu == "🚚 Nisyə Mal Çıxışı":
    st.header("🚚 Mağazaya Nisyə Mal Göndərilməsi")
    
    if stores_df.empty or products_df.empty:
        st.warning("Əvvəlcə Mağaza və Məhsul əlavə edin!")
    else:
        with st.form("sale_form"):
            selected_store = st.selectbox("Mağaza Seçin", stores_df["store_name"].tolist())
            selected_product = st.selectbox("Məhsul Seçin", products_df["product_name"].tolist())
            qty = st.number_input("Miqdar", min_value=1, step=1)
            
            p_price = products_df[products_df["product_name"] == selected_product]["unit_price"].values[0]
            price = st.number_input("Vahid Qiymət (AZN)", value=float(p_price))
            
            submit = st.form_submit_button("Təhvil Ver (Nisyə Yaz)")
            
            if submit:
                curr_stock = products_df[products_df["product_name"] == selected_product]["stock_qty"].values[0]
                if qty > curr_stock:
                    st.error(f"Anbarda kifayət qədər mal yoxdur! Qalıq: {curr_stock}")
                else:
                    total_amt = qty * price
                    new_id = len(transactions_df) + 1
                    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    new_trans = {
                        "id": new_id, "date": date_str, "store_name": selected_store,
                        "product_name": selected_product, "qty": qty, "price": price, "total_amount": total_amt
                    }
                    transactions_df = pd.concat([transactions_df, pd.DataFrame([new_trans])], ignore_index=True)
                    save_data(transactions_df, TRANSACTIONS_FILE)
                    
                    products_df.loc[products_df["product_name"] == selected_product, "stock_qty"] -= qty
                    save_data(products_df, PRODUCTS_FILE)
                    
                    st.success(f"{qty} ədəd {selected_product} -> {selected_store} mağazasına nisyə verildi. Məbləğ: {total_amt} AZN")
                    st.rerun()

# --- 6. BORC ÖDƏNİŞİ QƏBULU ---
elif menu == "💰 Borc Ödənişi Qəbulu":
    st.header("💰 Mağazadan Pul Qəbulu")
    
    if stores_df.empty:
        st.warning("Hələ heç bir mağaza yoxdur!")
    else:
        with st.form("payment_form"):
            selected_store = st.selectbox("Mağaza Seçin", stores_df["store_name"].tolist())
            amount = st.number_input("Ödənilən Məbləğ (AZN)", min_value=0.1, step=1.0)
            note = st.text_input("Qeyd (məs: Nağd, Köçürmə)")
            submit = st.form_submit_button("Ödənişi Qeyd Et")
            
            if submit:
                new_id = len(payments_df) + 1
                date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                new_pay = {"id": new_id, "date": date_str, "store_name": selected_store, "amount": amount, "note": note}
                payments_df = pd.concat([payments_df, pd.DataFrame([new_pay])], ignore_index=True)
                save_data(payments_df, PAYMENTS_FILE)
                st.success(f"{selected_store} tərəfindən {amount} AZN ödəniş qeydə alındı!")
                st.rerun()

# --- 7. AKT SVERKİ ---
elif menu == "📜 Hərəkət Tarixçəsi (Akt Sverki)":
    st.header("📜 Mağaza üzrə Hərəkət Tarixçəsi")
    if not stores_df.empty:
        selected_store = st.selectbox("Mağaza Seçin", stores_df["store_name"].tolist())
        
        st.subheader("📦 Verilən Mallar")
        st.dataframe(transactions_df[transactions_df["store_name"] == selected_store], use_container_width=True)
        
        st.subheader("💵 Edilən Ödənişlər")
        st.dataframe(payments_df[payments_df["store_name"] == selected_store], use_container_width=True)
