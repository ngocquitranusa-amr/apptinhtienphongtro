import calendar
import csv
import io
from datetime import date, timedelta

import streamlit as st


st.set_page_config(
    page_title="Tính tiền phòng trọ",
    page_icon="🏠",
    layout="centered",
)


def vnd(amount):
    return f"{amount:,.0f} đ".replace(",", ".")


def split_amount(total, weights):
    """Chia một khoản tiền theo trọng số; phần cuối nhận sai số làm tròn."""
    weight_sum = sum(weights)
    if weight_sum <= 0:
        return [0.0] * len(weights)

    shares = [round(total * weight / weight_sum) for weight in weights]
    if shares:
        shares[-1] += round(total) - sum(shares)
    return shares


st.title("🏠 TÍNH TIỀN PHÒNG TRỌ")
st.write(
    "Tính tiền phòng, điện, nước, Wi-Fi và chia chi phí cho từng người "
    "theo số ngày ở thực tế."
)

st.info(
    "Nhập tổng hóa đơn của kỳ này. Tiền điện và nước được tính từ chỉ số "
    "đồng hồ; Wi-Fi và chi phí chung được chia theo số ngày ở."
)

# Chọn kỳ tính tiền
now = date.today()
first_day = date(now.year, now.month, 1)
last_day = date(now.year, now.month, calendar.monthrange(now.year, now.month)[1])

st.subheader("1. Kỳ tính tiền")
date_col1, date_col2 = st.columns(2)
with date_col1:
    period_start = st.date_input("Từ ngày", value=first_day)
with date_col2:
    period_end = st.date_input("Đến ngày", value=last_day)

if period_end < period_start:
    st.error("Ngày kết thúc phải từ ngày bắt đầu trở đi.")
    st.stop()

period_days = (period_end - period_start).days + 1
st.caption(f"Kỳ này có {period_days} ngày.")

# Nhập hóa đơn
st.subheader("2. Hóa đơn của cả nhà")
rent_col, wifi_col = st.columns(2)
with rent_col:
    rent_total = st.number_input(
        "Tổng tiền phòng kỳ này (đ)", min_value=0, value=6000000, step=100000
    )
with wifi_col:
    wifi_total = st.number_input(
        "Tiền Wi-Fi kỳ này (đ)", min_value=0, value=200000, step=10000
    )

electric_col1, electric_col2, electric_col3 = st.columns(3)
with electric_col1:
    electric_old = st.number_input(
        "Điện: chỉ số cũ (kWh)", min_value=0.0, value=1000.0, step=1.0
    )
with electric_col2:
    electric_new = st.number_input(
        "Điện: chỉ số mới (kWh)", min_value=0.0, value=1100.0, step=1.0
    )
with electric_col3:
    electric_rate = st.number_input(
        "Giá điện mỗi kWh (đ)", min_value=0, value=3500, step=100
    )

water_col1, water_col2, water_col3 = st.columns(3)
with water_col1:
    water_old = st.number_input(
        "Nước: chỉ số cũ (m³)", min_value=0.0, value=100.0, step=1.0
    )
with water_col2:
    water_new = st.number_input(
        "Nước: chỉ số mới (m³)", min_value=0.0, value=110.0, step=1.0
    )
with water_col3:
    water_rate = st.number_input(
        "Giá nước mỗi m³ (đ)", min_value=0, value=15000, step=500
    )

extra_total = st.number_input(
    "Khoản chung khác (rác, gửi xe...; nếu không có nhập 0)",
    min_value=0,
    value=0,
    step=10000,
)

electric_valid = electric_new >= electric_old
water_valid = water_new >= water_old
if not electric_valid:
    st.error("Chỉ số điện mới đang nhỏ hơn chỉ số cũ. Hãy kiểm tra lại.")
if not water_valid:
    st.error("Chỉ số nước mới đang nhỏ hơn chỉ số cũ. Hãy kiểm tra lại.")

electric_used = electric_new - electric_old if electric_valid else 0
water_used = water_new - water_old if water_valid else 0
electric_total = electric_used * electric_rate
water_total = water_used * water_rate
shared_total = wifi_total + electric_total + water_total + extra_total

with st.expander("Xem cách tính tiền điện và nước"):
    st.write(f"Điện: {electric_new:g} − {electric_old:g} = {electric_used:g} kWh")
    st.write(
        f"Tiền điện: {electric_used:g} × {vnd(electric_rate)} "
        f"= {vnd(electric_total)}"
    )
    st.write(f"Nước: {water_new:g} − {water_old:g} = {water_used:g} m³")
    st.write(
        f"Tiền nước: {water_used:g} × {vnd(water_rate)} "
        f"= {vnd(water_total)}"
    )

# Hạn đóng tiền
st.subheader("3. Hạn thanh toán")
due_col1, due_col2 = st.columns([1, 2])
with due_col1:
    due_date = st.date_input("Ngày đến hạn", value=period_end + timedelta(days=5))
with due_col2:
    is_paid = st.checkbox("Đã thanh toán hóa đơn kỳ này")

if is_paid:
    st.success("Đã đánh dấu hóa đơn kỳ này là đã thanh toán.")
else:
    days_until_due = (due_date - date.today()).days
    if days_until_due < 0:
        st.warning(f"Hóa đơn đã quá hạn {abs(days_until_due)} ngày.")
    elif days_until_due == 0:
        st.warning("Hóa đơn đến hạn hôm nay.")
    else:
        st.info(f"Còn {days_until_due} ngày đến hạn thanh toán.")

# Thông tin người ở
st.subheader("4. Người ở và cách chia tiền")
resident_count = st.number_input(
    "Có bao nhiêu người cần chia tiền?", min_value=1, max_value=12, value=3, step=1
)
st.caption(
    "Số ngày ở dùng để chia điện, nước, Wi-Fi và khoản chung. "
    "Hệ số tiền phòng mặc định là 1 cho mỗi người; tăng hệ số nếu phòng đó "
    "thỏa thuận trả phần tiền phòng lớn hơn."
)

residents = []
for i in range(int(resident_count)):
    st.markdown(f"**Người {i + 1}**")
    name_col, days_col, weight_col = st.columns([2, 1, 1])
    with name_col:
        name = st.text_input(
            "Tên",
            value=f"Người {i + 1}",
            key=f"resident_name_{i}",
            label_visibility="collapsed",
            placeholder="Tên người ở",
        )
    with days_col:
        days_stayed = st.number_input(
            "Số ngày ở",
            min_value=0,
            max_value=366,
            value=period_days,
            step=1,
            key=f"resident_days_{i}",
        )
    with weight_col:
        rent_weight = st.number_input(
            "Hệ số phòng",
            min_value=0.1,
            max_value=10.0,
            value=1.0,
            step=0.1,
            key=f"rent_weight_{i}",
        )
    residents.append(
        {
            "name": name.strip() or f"Người {i + 1}",
            "days": int(days_stayed),
            "rent_weight": float(rent_weight),
        }
    )

if any(person["days"] > period_days for person in residents):
    st.error(f"Số ngày ở của mỗi người không thể vượt quá {period_days} ngày của kỳ tính tiền.")
    st.stop()

occupied_person_days = sum(person["days"] for person in residents)
rent_weights = [person["days"] * person["rent_weight"] for person in residents]
if occupied_person_days == 0 or sum(rent_weights) == 0:
    st.error("Cần có ít nhất một người ở ít nhất 1 ngày để chia hóa đơn.")
    st.stop()

rent_shares = split_amount(rent_total, rent_weights)
shared_shares = split_amount(
    shared_total, [person["days"] for person in residents]
)
electric_shares = split_amount(
    electric_total, [person["days"] for person in residents]
)
water_shares = split_amount(water_total, [person["days"] for person in residents])
wifi_shares = split_amount(wifi_total, [person["days"] for person in residents])
extra_shares = split_amount(extra_total, [person["days"] for person in residents])

results = []
for i, person in enumerate(residents):
    results.append(
        {
            "Tên": person["name"],
            "Ngày ở": person["days"],
            "Tiền phòng": round(rent_shares[i]),
            "Tiền điện": round(electric_shares[i]),
            "Tiền nước": round(water_shares[i]),
            "Wi-Fi": round(wifi_shares[i]),
            "Khoản chung khác": round(extra_shares[i]),
            "Tổng cần đóng": round(rent_shares[i] + shared_shares[i]),
        }
    )

st.divider()
st.subheader("5. Kết quả chia tiền")
summary_col1, summary_col2, summary_col3 = st.columns(3)
summary_col1.metric("Tiền phòng", vnd(rent_total))
summary_col2.metric("Tiền điện", vnd(electric_total))
summary_col3.metric("Tiền nước", vnd(water_total))
st.caption(
    f"Wi-Fi: {vnd(wifi_total)} · Khoản chung khác: {vnd(extra_total)} · "
    f"Tổng cả nhà: {vnd(rent_total + shared_total)}"
)

for result in results:
    with st.container(border=True):
        st.markdown(f"### 👤 {result['Tên']} — **{vnd(result['Tổng cần đóng'])}**")
        st.write(
            f"Phòng: {vnd(result['Tiền phòng'])} · "
            f"Điện: {vnd(result['Tiền điện'])} · "
            f"Nước: {vnd(result['Tiền nước'])} · "
            f"Wi-Fi: {vnd(result['Wi-Fi'])} · "
            f"Khoản chung: {vnd(result['Khoản chung khác'])}"
        )

# Tải bảng chia tiền để gửi cho người ở cùng
csv_buffer = io.StringIO()
writer = csv.DictWriter(csv_buffer, fieldnames=list(results[0].keys()))
writer.writeheader()
writer.writerows(results)
csv_bytes = ("\ufeff" + csv_buffer.getvalue()).encode("utf-8")

st.download_button(
    "⬇️ Tải bảng chia tiền (CSV)",
    data=csv_bytes,
    file_name=f"chia_tien_phong_{period_start:%Y%m%d}_{period_end:%Y%m%d}.csv",
    mime="text/csv",
    use_container_width=True,
)

st.caption(
    "Lưu ý: app chỉ tính và chia chi phí. Giá điện/nước nhập theo hóa đơn hoặc "
    "thỏa thuận thực tế; dữ liệu không được lưu lại khi tải lại trang."
)
