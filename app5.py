import streamlit as st
import math

# --- 核心邏輯函數 ---
def calculate_money_management(entry_price, initial_stop, total_shares, current_price, new_stop=None):
    one_r_unit = abs(entry_price - initial_stop)
    
    # 2R 減碼計算
    current_profit_per_share = current_price - entry_price
    sell_shares = 0
    if current_profit_per_share > 0:
        sell_shares = math.floor((total_shares * one_r_unit) / (current_profit_per_share + one_r_unit))
    
    remaining_shares = total_shares - sell_shares

    # 加碼計算
    add_on_shares = 0
    # 修正點：必須勾選且新停損價高於進場價才計算
    if new_stop is not None and new_stop > entry_price:
        profit_buffer = remaining_shares * (new_stop - entry_price)
        risk_per_add_on = current_price - new_stop
        if risk_per_add_on > 0:
            add_on_shares = math.floor(profit_buffer / risk_per_add_on)
            # 安全機制：限制加碼上限為初始部位的 2 倍
            add_on_shares = min(add_on_shares, total_shares * 2 - remaining_shares)

    # 壓力測試
    crash_price = current_price * 0.8
    crash_loss = (current_price - crash_price) * (remaining_shares + add_on_shares)
    
    return one_r_unit, sell_shares, remaining_shares, add_on_shares, crash_loss

# --- Streamlit 網頁介面設計 ---
st.set_page_config(page_title="三階段防彈交易計算器", layout="centered")

st.title("🛡️ 三階段交易策略計算器")
st.markdown("根據進場位、停損位自動計算**減碼**與**保本加碼**數據。")

# 側邊欄輸入
st.sidebar.header("📥 輸入參數")
entry = st.sidebar.number_input("進場價格 (Entry)", value=100.0)
stop = st.sidebar.number_input("原始停損 (Initial Stop)", value=90.0)
shares = st.sidebar.number_input("原始張數 (Total Shares)", value=10, step=1)
current = st.sidebar.number_input("目前市價 (Current Price)", value=115.0)

# --- 修改處：勾選式加碼輸入 ---
enable_add_on = st.sidebar.checkbox("我要計算保本加碼")
new_stop_input = None
if enable_add_on:
    new_stop_input = st.sidebar.number_input("新的移動停損 (New Stop)", value=entry)
    if new_stop_input <= entry:
        st.sidebar.warning("⚠️ 新停損需大於進場價方可保本加碼")
# ----------------------------

if st.sidebar.button("立即計算"):
    one_r, sell, remain, add_on, crash = calculate_money_management(entry, stop, shares, current, new_stop_input)
    
    # 顯示結果
    col1, col2 = st.columns(2)
    with col1:
        st.metric("1R 風險距離", f"{one_r:.2f}")
        st.metric("建議減碼張數", f"{sell} 張")
    with col2:
        st.metric("剩餘部位", f"{remain} 張")
        if enable_add_on:
            st.metric("建議加碼張數", f"{add_on} 張")

    st.divider()
    
    st.subheader("📊 風險診斷報告")
    st.info(f"💡 **減碼邏輯**：在現價減碼 {sell} 張後，即便剩下的 {remain} 張跌回原停損 {stop}，這筆交易結算仍為 $0 (保本)。")
    
    if enable_add_on and add_on > 0:
        st.success(f"🔥 **加碼邏輯**：利用移動停損至 {new_stop_input} 產生的獲利，可額外加碼 {add_on} 張。若跌破新停損，整筆單不傷本金。")
    elif enable_add_on and add_on == 0:
        st.warning("ℹ️ 目前獲利空間不足以支撐保本加碼。")
    
    st.warning(f"⚠️ **黑天鵝預警**：若不幸遭遇連續跌停 (-20%)，預計損失金額為：${crash:,.0f}")