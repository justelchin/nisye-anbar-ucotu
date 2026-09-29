import streamlit as st
import pandas as pd
import os
import shutil
from datetime import datetime

# Səhifə konfiqurasiyası
st.set_page_config(
    page_title="Nisyə və Anbar Uçotu",
    layout="wide",
    page_icon="📦",
    initial_sidebar_state="collapsed"
)

# Məlumat faylları
DATA_DIR = "data"
BACKUP_DIR = "data_backup"

for directory in [DATA_DIR, BACKUP_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

STORES_FILE = os.path.join(DATA_DIR, "stores.csv")
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.csv")
TRANSACTIONS_FILE = os.path.join(DATA_DIR, "transactions.csv")
PAYMENTS_FILE = os.path.join(DATA_DIR, "payments.csv")

FILES = [STORES_FILE, PRODUCTS_FILE, TRANSACTIONS_FILE, PAYMENTS_FILE]

def load_data(file_path, columns):
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        for col in columns:
            if col not in df.columns:
                df[col] = 0 if any(x in col for x in ["qty", "amount", "price"]) else ""
        return df
    return pd.DataFrame(columns=columns)

def save_data(df, file_path):
    df.to_csv(file_path, index=False)

def create_backup():
    for file in FILES:
        if os.path.exists(file):
            shutil.copy(file, os.path.join(BACKUP_DIR, os.path.basename(file)))

def restore_backup():
    has_backup = False
    for file in FILES:
        backup_file = os.path.join(BACKUP_DIR, os.path.basename(file))
        if os.path.exists(backup_file):
            shutil.copy(backup_file, file)
            has_backup = True
    return has_backup

def reset_database():
    create_backup() # Silmədən öncə də yedək götürürük
    for file in FILES:
        if os.path.exists(file):
            os.remove(file)

# Məlumatları yükləyirik
stores_df = load_data(STORES_FILE, ["id", "store_name", "phone", "note"])
products_df = load_data(PRODUCTS_FILE, ["id", "code_1c", "product_name", "unit_price", "our_stock_qty"])
transactions_df = load_data(TRANSACTIONS_FILE, ["id", "date", "store_name", "product_name", "qty", "price", "total_amount", "store_stock_qty"])
payments_df = load_data(PAYMENTS_FILE, ["id", "date", "store_name", "amount", "note"])

# Başlıq
st.title("📦 Nisyə və Anbar Uçotu Sistemi")

# Tablar
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Dashboard",
    "📥 Excel Yüklə",
    "🚚 Mal Çıxışı",
    "💰 Pul Qəbulu",
    "📜 Hərəkət Tarixçəsi",
    "🏪 Mağaza və Bizim Anbar",
    "⚙️ Baza İdarəsi"
])

# ================= 1. DASHBOARD =================
with tab1:
    st.subheader("📊 Ümumi Vəziyyət")
    
    total_sales = transactions_df.groupby("store_name")["total_amount"].sum() if not transactions_df.empty and "total_amount" in transactions_df.columns else pd.Series(dtype=float)
    total_paid = payments_df.groupby("store_name")["amount"].sum() if not payments_df.empty and "amount" in payments_df.columns else pd.Series(dtype=float)
    
    stores_summary = pd.DataFrame({"store_name": stores_df["store_name"] if not stores_df.empty and "store_name" in stores_df.columns else []})
    if not stores_summary.empty:
        stores_summary["Ümumi Mal Alışı (AZN)"] = stores_summary["store_name"].map(total_sales).fillna(0)
        stores_summary["Ödənilən (AZN)"] = stores_summary["store_name"].map(total_paid).fillna(0)
        stores_summary["Qalan Borc (AZN)"] = stores_summary["Ümumi Mal Alışı (AZN)"] - stores_summary["Ödənilən (AZN)"]
    
    col1, col2, col3 = st.columns(3)
    total_debt = stores_summary["Qalan Borc (AZN)"].sum() if not stores_summary.empty else 0
    
    stock_col = "our_stock_qty" if "our_stock_qty" in products_df.columns else ("stock_qty" if "stock_qty" in products_df.columns else None)
    if not products_df.empty and stock_col and "unit_price" in products_df.columns:
        valid_prices = pd.to_numeric(products_df["unit_price"], errors="coerce").fillna(0)
        valid_stocks = pd.to_numeric(products_df[stock_col], errors="coerce").fillna(0)
        our_stock_val = (valid_prices * valid_stocks).sum()
    else:
        our_stock_val = 0.0
    
    col1.metric("💰 Ümumi Alacaq Borc", f"{total_debt:.2f} AZN")
    col2.metric("🏢 Bizim Anbardakı Mal Dəyəri", f"{max(0.0, our_stock_val):.2f} AZN")
    col3.metric("🏪 Qeydiyyatlı Mağazalar", len(stores_df))
    
    st.divider()
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔴 Mağazaların Borc Qalıqları")
        if not stores_summary.empty:
            st.dataframe(stores_summary.rename(columns={"store_name": "Mağaza"}), use_container_width=True)
        else:
            st.info("Məlumat yoxdur.")
            
    with c2:
        st.subheader("🏪 Mağazalardakı Satılmamış Mal Qalıqları")
        if not transactions_df.empty and "store_stock_qty" in transactions_df.columns:
            latest_store_stock = transactions_df[["store_name", "product_name", "store_stock_qty"]].copy()
            latest_store_stock["store_stock_qty"] = pd.to_numeric(latest_store_stock["store_stock_qty"], errors="coerce").fillna(0)
            latest_store_stock = latest_store_stock.drop_duplicates(subset=["store_name", "product_name"], keep="last")
            st.dataframe(latest_store_stock.rename(columns={
                "store_name": "Mağaza",
                "product_name": "Məhsul",
                "store_stock_qty": "Obyektdə Qalan Mal (Ədəd)"
            }), use_container_width=True)
        else:
            st.info("Obyekt üzrə mal qalığı qeydə alınmayıb.")

# ================= 2. EXCEL YÜKLƏ =================
with tab2:
    st.subheader("📥 Excel Faylı İlə Toplu Məlumat Yükləmə")
    st.caption("Excel faylındakı 'Mal qalığı' obyektdə (mağazada) qalan satılmamış mal kimi saxlanılacaq.")
    
    uploaded_file = st.file_uploader("Excel (.xlsx və ya .csv) faylınızı bura atın", type=["xlsx", "csv"])
    
    if uploaded_file is not None:
        try:
            df_excel = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
            st.dataframe(df_excel.head(10), use_container_width=True)
            
            def find_col(keywords, df):
                for col in df.columns:
                    for kw in keywords:
                        if kw.lower() in str(col).lower():
                            return col
                return None

            store_col = find_col(["mağaza", "magaza", "obyekt", "müşdəri", "musteri"], df_excel)
            prod_col = find_col(["məhsulun adı", "mehsulun adi", "məhsul", "mehsul", "ad"], df_excel)
            code_col = find_col(["1c", "kod"], df_excel)
            qty_col = find_col(["miqdar", "say"], df_excel)
            price_col = find_col(["qiymət", "qiymet"], df_excel)
            total_col = find_col(["məbləğ", "mebleg", "cəm"], df_excel)
            paid_col = find_col(["ödənilən", "odenilen", "ödeniş"], df_excel)
            stock_col_excel = find_col(["qalığı", "qaliq", "qalıq", "məhsul qalığı"], df_excel)

            if st.button("🚀 Məlumatları Bazaya Köçür", type="primary"):
                # Yeni məlumat yükləməzdən öncə ehtiyat nüsxə götürək
                create_backup()

                # Mağazaları əlavə et
                if store_col:
                    for s in df_excel[store_col].dropna().unique():
                        if s not in stores_df["store_name"].values:
                            stores_df = pd.concat([stores_df, pd.DataFrame([{"id": len(stores_df)+1, "store_name": s, "phone": "", "note": "Excel-dən"}])], ignore_index=True)
                    save_data(stores_df, STORES_FILE)
                
                # Məhsulları əlavə et
                if prod_col:
                    for _, row in df_excel.iterrows():
                        p_name = row.get(prod_col)
                        if pd.isna(p_name): continue
                        code_1c = str(row.get(code_col, "")) if code_col else ""
                        price_val = row.get(price_col, 0.0) if price_col else 0.0
                        price = float(price_val) if pd.notna(price_val) else 0.0
                        
                        if p_name not in products_df["product_name"].values:
                            products_df = pd.concat([products_df, pd.DataFrame([{
                                "id": len(products_df)+1, "code_1c": code_1c, "product_name": p_name, "unit_price": price, "our_stock_qty": 0
                            }])], ignore_index=True)
                    save_data(products_df, PRODUCTS_FILE)

                # Əməliyyatları və Obyekt Mal Qalıqlarını əlavə et
                for _, row in df_excel.iterrows():
                    d_val = datetime.now().strftime("%Y-%m-%d")
                    s_name = row.get(store_col) if store_col else None
                    p_name = row.get(prod_col) if prod_col else None
                    
                    qty = float(row.get(qty_col, 0)) if qty_col and pd.notna(row.get(qty_col)) else 0
                    price = float(row.get(price_col, 0)) if price_col and pd.notna(row.get(price_col)) else 0
                    total = float(row.get(total_col, 0)) if total_col and pd.notna(row.get(total_col)) else (qty * price)
                    paid = float(row.get(paid_col, 0)) if paid_col and pd.notna(row.get(paid_col)) else 0
                    
                    store_stock = float(row.get(stock_col_excel, 0)) if stock_col_excel and pd.notna(row.get(stock_col_excel)) else 0
                    
                    if pd.notna(s_name) and pd.notna(p_name):
                        transactions_df = pd.concat([transactions_df, pd.DataFrame([{
                            "id": len(transactions_df)+1, "date": d_val, "store_name": s_name,
                            "product_name": p_name, "qty": qty, "price": price, "total_amount": total,
                            "store_stock_qty": store_stock
                        }])], ignore_index=True)
                    
                    if pd.notna(s_name) and paid > 0:
                        payments_df = pd.concat([payments_df, pd.DataFrame([{
                            "id": len(payments_df)+1, "date": d_val, "store_name": s_name, "amount": paid, "note": "Excel ödənişi"
                        }])], ignore_index=True)
                
                save_data(transactions_df, TRANSACTIONS_FILE)
                save_data(payments_df, PAYMENTS_FILE)
                st.success("✅ Məlumatlar uğurla köçürüldü! (Əvvəlki baza yedəkləndi)")
                st.rerun()
        except Exception as e:
            st.error(f"Xəta baş verdi: {e}")

# ================= 3. MAL ÇIXIŞI =================
with tab3:
    st.subheader("🚚 Obyektə Nisyə Mal Göndərilməsi")
    if stores_df.empty or products_df.empty:
        st.warning("Əvvəlcə Mağaza və Məhsul əlavə edin.")
    else:
        col_a, col_b = st.columns(2)
        with col_a:
            selected_store = st.selectbox("Mağaza / Obyekt", stores_df["store_name"].tolist())
            selected_product = st.selectbox("Məhsul", products_df["product_name"].tolist())
        with col_b:
            qty = st.number_input("Verilən Miqdar (Ədəd)", min_value=1, step=1)
            p_price = products_df[products_df["product_name"] == selected_product]["unit_price"].values[0] if not products_df.empty else 0.0
            price = st.number_input("Qiymət (AZN)", value=float(p_price))

        if st.button("Təhvil Ver (Nisyə Yaz)", type="primary"):
            create_backup()
            total_amt = qty * price
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            prev_store_stock = 0
            if not transactions_df.empty:
                filtered = transactions_df[(transactions_df["store_name"] == selected_store) & (transactions_df["product_name"] == selected_product)]
                if not filtered.empty:
                    prev_store_stock = float(filtered.iloc[-1]["store_stock_qty"]) if pd.notna(filtered.iloc[-1]["store_stock_qty"]) else 0
            
            new_store_stock = prev_store_stock + qty
            
            transactions_df = pd.concat([transactions_df, pd.DataFrame([{
                "id": len(transactions_df)+1, "date": date_str, "store_name": selected_store,
                "product_name": selected_product, "qty": qty, "price": price, "total_amount": total_amt,
                "store_stock_qty": new_store_stock
            }])], ignore_index=True)
            save_data(transactions_df, TRANSACTIONS_FILE)
            
            stock_col = "our_stock_qty" if "our_stock_qty" in products_df.columns else ("stock_qty" if "stock_qty" in products_df.columns else None)
            if stock_col:
                products_df.loc[products_df["product_name"] == selected_product, stock_col] -= qty
                save_data(products_df, PRODUCTS_FILE)
                
            st.success("Təhvil verildi!")
            st.rerun()

# ================= 4. PUL QƏBULU =================
with tab4:
    st.subheader("💰 Ödəniş Qəbulu")
    if stores_df.empty:
        st.warning("Mağaza yoxdur.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            selected_store_pay = st.selectbox("Mağaza Seçin", stores_df["store_name"].tolist(), key="pay_store")
            amount = st.number_input("Ödənilən Məbləğ (AZN)", min_value=0.1, step=1.0)
        with c2:
            note = st.text_input("Qeyd (Məs: Nağd)")
            
        if st.button("Ödənişi Qeyd Et", type="primary"):
            create_backup()
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            payments_df = pd.concat([payments_df, pd.DataFrame([{
                "id": len(payments_df)+1, "date": date_str, "store_name": selected_store_pay, "amount": amount, "note": note
            }])], ignore_index=True)
            save_data(payments_df, PAYMENTS_FILE)
            st.success("Ödəniş saxlanıldı!")
            st.rerun()

# ================= 5. AKT SVERKİ =================
with tab5:
    st.subheader("📜 Mağaza Hərəkət Tarixçəsi (Akt Sverki)")
    if not stores_df.empty:
        s_filter = st.selectbox("Mağazanı Seçin", stores_df["store_name"].tolist(), key="hist_store")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("📦 **Verilən Mallar və Obyektdə Qalan Mədaxil**")
            st.dataframe(transactions_df[transactions_df["store_name"] == s_filter], use_container_width=True)
        with col2:
            st.write("💵 **Edilən Ödənişlər**")
            st.dataframe(payments_df[payments_df["store_name"] == s_filter], use_container_width=True)

# ================= 6. BİZİM ANBAR İDARƏSİ =================
with tab6:
    st.subheader("🏪 Mağaza və Bizim Anbar Məhsulları")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("➕ **Yeni Mağaza Əlavə Et**")
        s_name = st.text_input("Mağaza Adı")
        s_phone = st.text_input("Telefon")
        if st.button("Mağazanı Saxla"):
            if s_name:
                create_backup()
                stores_df = pd.concat([stores_df, pd.DataFrame([{"id": len(stores_df)+1, "store_name": s_name, "phone": s_phone, "note": ""}])], ignore_index=True)
                save_data(stores_df, STORES_FILE)
                st.success("Əlavə olundu!")
                st.rerun()

    with col2:
        st.write("📦 **Bizim Anbara Yeni Mal Mədaxil Et**")
        p_name = st.text_input("Məhsul Adı")
        p_code = st.text_input("1C Kodu")
        p_price = st.number_input("Qiyməti (AZN)", min_value=0.0)
        p_qty = st.number_input("Bizim Anbardakı Sayı (Ədəd)", min_value=0)
        if st.button("Məhsulu Anbara Saxla"):
            if p_name:
                create_backup()
                stock_col = "our_stock_qty" if "our_stock_qty" in products_df.columns else "stock_qty"
                products_df = pd.concat([products_df, pd.DataFrame([{"id": len(products_df)+1, "code_1c": p_code, "product_name": p_name, "unit_price": p_price, stock_col: p_qty}])], ignore_index=True)
                save_data(products_df, PRODUCTS_FILE)
                st.success("Məhsul anbarımıza daxil edildi!")
                st.rerun()

# ================= 7. BAZA İDARƏSİ VƏ BƏRPA =================
with tab7:
    st.subheader("⚙️ Məlumat Bazası İdarəetməsi")
    st.caption("Səhv olduqda bazanı sıfırlaya və ya son ehtiyat nüsxəyə bərpa edə bilərsiniz.")
    
    col_reset, col_restore = st.columns(2)
    
    with col_reset:
        st.error("🚨 Bazanı Sil / Sıfırla")
        st.write("Bu düymə bütün mağaza, məhsul və əməliyyat məlumatlarını sıfırlayacaq. Sıfırlamadan öncə avtomatik ehtiyat nüsxə götürülür.")
        confirm_reset = st.checkbox("Bazanı sıfırlamağa əminəm")
        if st.button("❌ Bazanı Tam Sil", type="primary", disabled=not confirm_reset):
            reset_database()
            st.success("🗑️ Baza uğurla sıfırlandı!")
            st.rerun()
            
    with col_restore:
        st.info("🔄 Əvvəlki Versiyaya Qayıt (Bərpa Et)")
        st.write("Sonuncu dəfə yüklənmiş və ya sıfırlanmış ehtiyat nüsxəyə geri qayıtmaq üçün bu düymədən istifadə edin.")
        if st.button("↩️ Son Versiyaya Bərpa Et"):
            if restore_backup():
                st.success("✅ Məlumatlar son ehtiyat nüsxədən bərpa olundu!")
                st.rerun()
            else:
                st.warning("⚠️ Bərpa etmək üçün heç bir ehtiyat nüsxə tapılmadı.")
