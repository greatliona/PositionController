import streamlit as st
import math

# --- 核心邏輯函數 ---
def calculate_money_management(entry_price, initial_stop, total_shares, current_price, 
                               target_stop_price=None, 
                               profit_amount_goal=0,
                               enable_add_on=False, 
                               add_on_stop=None):
    
    one_r_unit = abs(entry_price - initial_stop)
    current_profit_per_share = current_price - entry_price
    total_current_profit = current_profit_per_share * total_shares
    profit_pct = (current_profit_per_share / entry_price) * 100 if entry_price != 0 else 0
    profit_r_multiple = current_profit_per_share / one_r_unit if one_r_unit != 0 else 0

    # --- 1. 獨立減碼計算 ---
    sell_basic = 0
    if current_profit_per_share > 0:
        sell_basic = math.ceil((total_shares * one_r_unit) / (current_profit_per_share + one_r_unit))
    
    sell_by_amount = 0
    if profit_amount_goal > 0 and current_profit_per_share > 0:
        sell_by_amount = math.ceil((profit_amount_goal + (total_shares * one_r_unit)) / (current_profit_per_share + one_r_unit))

    final_sell = max(sell_basic, sell_by_amount)
    final_sell = min(final_sell, total_shares)
    remaining_shares = total_shares - final_sell

    # --- 2. 獨立加碼計算 ---
    add_on_shares = 0
    theo_add_on = 0
    add_on_cost = 0
    final_p_if_add_stop = 0 
    
    if enable_add_on and add_on_stop is not None and add_on_stop > entry_price:
        available_buffer = (total_shares * (add_on_stop - entry_price)) - profit_amount_goal
        risk_per_add_on = current_price - add_on_stop
        
        if risk_per_add_on > 0 and available_buffer > 0:
            theo_add_on = math.floor(available_buffer / risk_per_add_on)
            add_on_shares = min(theo_add_on, total_shares)
            add_on_cost = add_on_shares * current_price 
            
            loss_on_add_shares = add_on_shares * (current_price - add_on_stop)
            final_p_if_add_stop = (total_shares * (add_on_stop - entry_price)) - loss_on_add_shares

    # --- 3. 鎖利分析與獲利明細 ---
    already_earned = final_sell * (current_price - entry_price) 
    potential_locked = remaining_shares * (target_stop_price - entry_price) if target_stop_price else 0
    locked_total = already_earned + potential_locked

    no_sell_init = total_shares * (initial_stop - entry_price) 
    no_sell_target = total_shares * (target_stop_price - entry_price) if target_stop_price else 0

    crash_price = current_price * 0.8
    risk_now = (current_price - crash_price) * total_shares
    risk_after_sell = (current_price - crash_price) * remaining_shares
    risk_after_add = (current_price - crash_price) * (total_shares + add_on_shares)
    
    return {
        "one_r": one_r_unit, "sell": final_sell, "remain": remaining_shares,
        "add_on": add_on_shares, "theo_add": theo_add_on, "add_cost": add_on_cost,
        "total_p": total_current_profit, "p_pct": profit_pct, "profit_r": profit_r_multiple,
        "l_total": locked_total, "l_earned": already_earned, "l_potential": potential_locked,
        "no_sell_init": no_sell_init, "no_sell_target": no_sell_target,
        "final_p_if_add_stop": final_p_if_add_stop,
        "risk_now": risk_now, "risk_sell": risk_after_sell, "risk_add": risk_after_add
    }

# --- Streamlit 介面 ---
st.set_page_config(page_title="三階段防彈交易計算器", layout="centered")
st.title("🛡️ 三階段交易策略計算器 C1.1.1")

# 側邊欄輸入
st.sidebar.header("📥 基礎參數")
entry = st.sidebar.number_input("進場價格", value=680.0)
stop = st.sidebar.number_input("原始停損", value=650.0)
shares = st.sidebar.number_input("原始張數", value=350, step=1)
current = st.sidebar.number_input("目前市價", value=1350.0)

st.sidebar.divider()
st.sidebar.subheader("🎯 策略開關")
en_amount = st.sidebar.checkbox("我要保留特定獲利金額")
p_goal = st.sidebar.number_input("保留金額 ($)", value=0.0) if en_amount else 0.0

en_target = st.sidebar.checkbox("我要設定移動停損價位")
t_stop = st.sidebar.number_input("移動停損價", value=entry) if en_target else None

en_add = st.sidebar.checkbox("我要計算保本加碼")
a_stop = st.sidebar.number_input("加碼單停損價", value=entry) if en_add else None

if st.sidebar.button("立即計算"):
    res = calculate_money_management(entry, stop, shares, current, t_stop, p_goal, en_add, a_stop)
    
    st.subheader("💰 目前帳面獲利概況")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("目前獲利金額", f"${res['total_p']:,.0f}")
    c2.metric("獲利百分比", f"{res['p_pct']:.2f}%")
    c3.metric("1R 距離", f"{res['one_r']:.2f}")
    c4.metric("獲利倍數", f"{res['profit_r']:.2f} R")

    st.divider()

    st.subheader("📋 獨立交易指令")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.write("### ❶ 減碼鎖利指令")
        st.metric("建議減碼", f"{res['sell']} 張")
        st.write(f"執行後剩餘：**{res['remain']} 張**")
        if en_amount and p_goal > 0:
            st.write(f"💡 目的：確保跌回原始停損時仍有 :green[**${p_goal:,.0f}**] 獲利。")
        else:
            st.write(f"💡 目的：確保跌回原始停損 {stop} 時能 :green[**完全保本**]。")

    with col_b:
        st.write("### ❷ 原倉加碼指令")
        if en_add:
            st.metric("建議實戰加碼", f"{res['add_on']} 張")
            st.write(f"理論最大加碼： **{res['theo_add']} 張**")
            st.caption(f"（實戰上限限制為原始部位 1:1，即最高 {shares} 張）")
            st.write(f"預估投入金額： :green[**${res['add_cost']:,.0f}**]")
            
            # --- 強化防禦提示：寫清楚保留多少、多賺多少 ---
            final_p = res['final_p_if_add_stop']
            if en_amount:
                surplus = final_p - p_goal
                if final_p >= p_goal:
                    st.write(f"🛡️ **防禦提示**：若加碼單跌破停損 {a_stop}，帳戶仍能保住保留金額 :green[**${p_goal:,.0f}**]，且多賺 :green[**${surplus:,.0f}**]。")
                else:
                    st.write(f"🚨 **風險提示**：若加碼單跌破停損 {a_stop}，將無法保住全額保留獲利，會缺損 :red[**${abs(surplus):,.0f}**]。")
            else:
                if final_p >= 0:
                    st.write(f"🛡️ **防禦提示**：若加碼單跌破停損 {a_stop}，帳戶最終仍能穩賺 :green[**${final_p:,.0f}**]。")
                else:
                    st.write(f"🚨 **風險提示**：若加碼單跌破停損 {a_stop}，帳戶最終將轉為虧損 :red[**${abs(final_p):,.0f}**]。")
        else:
            st.info("加碼功能未開啟")

    st.divider()
    
    st.subheader("📊 價位鎖利與對照明細")
    detail_l, detail_r = st.columns(2)
    with detail_l:
        st.write("📝 **減碼後 (鎖利狀態)**")
        st.write(f"* 現價減碼 {res['sell']} 張已實現： :green[**${res['l_earned']:,.0f}**]")
        if en_target:
            st.write(f"* 剩餘 {res['remain']} 張守在 {t_stop} 預期： :green[**${res['l_potential']:,.0f}**]")
            st.write(f"**最終保底穩賺總額： :green[**${res['l_total']:,.0f}**]**")
    with detail_r:
        st.write("❌ **若不減碼 (原始倉位硬扛)**")
        st.write(f"* 回到原始停損 {stop} 盈虧： :red[**${res['no_sell_init']:,.0f}**]")
        if en_target:
            st.write(f"* 回到移動停損 {t_stop} 盈虧： :orange[**${res['no_sell_target']:,.0f}**]")

    st.divider()

    st.subheader("⚠️ 黑天鵝風險預警 (-20% 跌停)")
    r1, r2, r3 = st.columns(3)
    r1.write("**目前全倉**")
    r1.write(f":red[$-{res['risk_now']:,.0f}]")
    r2.write("**若僅減碼後**")
    r2.write(f":orange[$-{res['risk_sell']:,.0f}]")
    r3.write("**若僅加碼後**")
    r3.write(f":red[$-{res['risk_add']:,.0f}]")
