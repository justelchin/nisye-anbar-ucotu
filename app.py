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
products_df = load_data(PRODUCTS_FILE, ["id", "product_name", "unit_price", "stock_qty"])
transactions_df = load_data(TRANSACTIONS_FILE, ["id", "date", "store_name", "product_name", "qty", "price", "total_amount"])
payments_df = load_data(PAYMENTS_FILE, ["id", "date", "store_name", "amount", "note"])

st.title("📦 Qeyri-rəsmi Nisyə və Anbar Uçotu Sistemi")

# Yan menyu
menu = st.sidebar.radio("Bölmələr", [
    "📊 Əsas Hesabatlar (Dashboard)",
    "🏪 Mağazalar (Müştərilər)",
    "📦 Anbar / Məhsullar",
    "🚚 Nisyə Mal Çıxışı",
    "💰 Borc Ödənişi Qəbulu",
    "📜 Hərəkət Tarixçəsi (Akt Sverki)"
])

# --- 1. ƏSAS HESABATLAR ---
if menu == "📊 Əsas Hesabatlar (Dashboard)":
    st.header("📊 Ümumi Vəziyyət")
    
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
    
    col1.metric("Ümumi Alacaq Borc", f"{total_debt:.2f} AZN")
    col2.metric("Anbardakı Mal Dəyəri", f"{total_stock_val:.2f} AZN")
    col3.metric("Aktiv Mağaza Sayı", len(stores_df))
    
    st.subheader("🏪 Mağazalar üzrə Borc Siyahısı")
    st.dataframe(stores_summary, use_container_width=True)

# --- 2. MAĞAZALAR ---
elif menu == "🏪 Mağazalar (Müştərilər)":
    st.header("🏪 Mağazaların Qeydiyyatı")
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

    st.subheader("Mövcud Mağazalar")
    st.dataframe(stores_df, use_container_width=True)

# --- 3. ANBAR VƏ MƏHSULLAR ---
elif menu == "📦 Anbar / Məhsullar":
    st.header("📦 Məhsul Və Anbar Qalıqları")
    with st.form("add_product"):
        product_name = st.text_input("Məhsulun Adı")
        unit_price = st.number_input("Satış Qiyməti (AZN)", min_value=0.0, step=0.1)
        stock_qty = st.number_input("Anbardakı İlkin Miqdar", min_value=0, step=1)
        submit = st.form_submit_button("Məhsul Əlavə Et")
        
        if submit and product_name:
            new_id = len(products_df) + 1
            new_row = {"id": new_id, "product_name": product_name, "unit_price": unit_price, "stock_qty": stock_qty}
            products_df = pd.concat([products_df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(products_df, PRODUCTS_FILE)
            st.success(f"'{product_name}' bazaya əlavə olundu!")
            st.rerun()

    st.subheader("Anbardakı Qalıqlar")
    st.dataframe(products_df, use_container_width=True)

# --- 4. NISYƏ MAL ÇIXIŞI ---
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

# --- 5. BORC ÖDƏNİŞİ QƏBULU ---
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

# --- 6. AKT SVERKİ ---
elif menu == "📜 Hərəkət Tarixçəsi (Akt Sverki)":
    st.header("📜 Mağaza üzrə Hərəkət Tarixçəsi")
    if not stores_df.empty:
        selected_store = st.selectbox("Mağaza Seçin", stores_df["store_name"].tolist())
        
        st.subheader("📦 Verilən Mallar")
        st.dataframe(transactions_df[transactions_df["store_name"] == selected_store], use_container_width=True)
        
        st.subheader("💵 Edilən Ödənişlər")
        st.dataframe(payments_df[payments_df["store_name"] == selected_store], use_container_width=True)
