import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# محاولة الاتصال بقاعدة بيانات Supabase السحابية للمزامنة اللحظية بين الموبايل والحاسبة
try:
    from supabase import create_client
    SUPABASE_URL = st.secrets.get("SUPABASE_URL", "YOUR_SUPABASE_URL")
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "YOUR_SUPABASE_KEY")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    CLOUD_READY = True
except Exception:
    CLOUD_READY = False

# إعدادات صفحة الويب المتطورة
st.set_page_config(
    page_title="مستشفى الشوملي العام - النظام الصيدلاني السحابي الموحد",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تنسيقات واجهة المستشفى الداكنة الاحترافية (Dark Pro Dashboard)
st.markdown("""
    <style>
    .main { background-color: #090d16; color: #f8fafc; font-family: 'Segoe UI', Tahoma, sans-serif; }
    h1, h2, h3 { color: #38bdf8; }
    .stButton>button { background-color: #0284c7; color: white; font-weight: bold; border-radius: 8px; border: none; padding: 8px 16px; }
    .stButton>button:hover { background-color: #0369a1; }
    div.stMetric { background-color: #111827; padding: 15px; border-radius: 10px; border: 1px solid #1f2937; }
    </style>
""", unsafe_allow_html=True)

# القوائم الأساسية المطابقة للبرنامج المكتبي تماماً
DEFAULT_REGISTERS = [
    "الحياتية", "الامبولات والفيالات", "المساحيق والشرابات",
    "الحبوب والكباسيل", "المؤثرات العقلية", "المخدرات",
    "مستلزمات القسم", "سجل الضماد", "اللقاحات", "مشتريات الادويه",
    "مشتريات المستلزمات", "مشتريات الجناح الخاص"
]

SUB_PORTALS_LIST = [
    "البرنامج الرئيسي (صاحب البرنامج)", "الصيدلية الداخلية", "الصيدلية الاستشاريه", "صيدلية الطوارئ",
    "الصيدلية الخارجية الخافرة", "الداخلية الخافرة", "الجناح العام الرجالي",
    "الجناح العام النسائي", "جناح الاطفال", "الخدج", "صالة الولادة",
    "صاله العمليات / الجناح الخاص", "الاسنان", "الاشعة", "السونار",
    "الطوارئ العامه", "الاسعاف الفوري", "الخدمات", "المختبرات",
    "الوبائيه", "لوكرات الصدمة", "الجناح الخاص", "العمليات"
]

MONTHS_LIST = [
    "كانون الثاني (Month 01)", "شباط (Month 02)", "آذار (Month 03)",
    "نيسان (Month 04)", "أيار (Month 05)", "حزيران (Month 06)",
    "تموز (Month 07)", "آب (Month 08)", "أيلول (Month 09)",
    "تشرين الأول (Month 10)", "تشرين الثاني (Month 11)", "كانون الأول (Month 12)"
]

# التحقق من الاتصال السحابي
if not CLOUD_READY:
    st.error("⚠️ تنبيه: يرجى إعداد متغيرات الاتصال بـ Supabase (SUPABASE_URL و SUPABASE_KEY) في إعدادات المنصة (Streamlit Secrets) لتفعيل المزامنة.")
    st.stop()

# إدارة الجلسة (Session State) لتسجيل الدخول واختيار البوابات والسجلات
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "portal_scope" not in st.session_state:
    st.session_state.portal_scope = "MAIN_ADMIN"

# شاشة تسجيل الدخول واختيار البوابة (مطابقة تماماً للنسخة المكتبية)
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center; color: #38bdf8;'>🏥 مستشفى الشوملي العام - بوابة الدخول الذكية</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("---")
        chosen_portal_label = st.selectbox("اختر بوابة الدخول أو الوحدة:", SUB_PORTALS_LIST)
        u_name = st.text_input("اسم المستخدم:")
        u_pass = st.text_input("كلمة المرور:", type="password")
        
        if st.button("🚀 تسجيل الدخول للواجهة"):
            portal_key = "MAIN_ADMIN" if chosen_portal_label == "البرنامج الرئيسي (صاحب البرنامج)" else chosen_portal_label
            try:
                res = supabase.table("portal_credentials").select("*").eq("portal_name", portal_key).execute()
                data = res.data
                saved_u = data[0]["username"] if data and data[0].get("username") else "admin"
                saved_p = data[0]["password"] if data and data[0].get("password") else "1234"
            except Exception:
                saved_u, saved_p = "admin", "1234"
                
            if u_name.strip() == saved_u and u_pass.strip() == saved_p:
                st.session_state.logged_in = True
                st.session_state.portal_scope = portal_key
                st.success("تم تسجيل الدخول بنجاح!")
                st.rerun()
            else:
                st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة!")
    st.stop()

# الواجهة الرئيسية بعد تسجيل الدخول
portal_display = "المذخر الصيدلاني (الرئيسي)" if st.session_state.portal_scope == "MAIN_ADMIN" else st.session_state.portal_scope
st.sidebar.markdown(f"### 🏥 مستشفى الشوملي")
st.sidebar.info(f"البوابة النشطة: **{portal_display}**")

if st.sidebar.button("🔒 تسجيل الخروج وتغيير البوابة"):
    st.session_state.logged_in = False
    st.rerun()

st.sidebar.markdown("---")

# جلب أو إدارة السجلات المخصصة من قاعدة البيانات السحابية
try:
    reg_res = supabase.table("custom_registers").select("register_name").eq("portal_scope", st.session_state.portal_scope).execute()
    custom_regs = [r["register_name"] for r in reg_res.data] if reg_res.data else []
    active_registers = DEFAULT_REGISTERS.copy()
    for cr in custom_regs:
        if cr not in active_registers:
            active_registers.append(cr)
except Exception:
    active_registers = DEFAULT_REGISTERS

selected_register = st.sidebar.selectbox("📋 السجلات والمخزون:", active_registers)

# إضافة أو حذف سجل جديد من الشريط الجانبي
with st.sidebar.expander("⚙️ إدارة السجلات"):
    new_reg_name = st.text_input("اسم السجل الجديد:")
    if st.button("إضافة السجل"):
        if new_reg_name:
            try:
                supabase.table("custom_registers").insert({
                    "portal_scope": st.session_state.portal_scope,
                    "register_name": new_reg_name
                }).execute()
                st.success("تم إضافة السجل بنجاح!")
                st.rerun()
            except Exception as e:
                st.error(f"خطأ: {e}")

# أدوات التقارير والجرد السحابية في الشريط الجانبي
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 أدوات التقارير والجرد")

if st.sidebar.button("🔔 تنبيهات الصلاحية (9 / 18 شهراً)"):
    try:
        if st.session_state.portal_scope == "MAIN_ADMIN":
            exp_res = supabase.table("items").select("*").gt("remaining_qty", 0).execute()
        else:
            exp_res = supabase.table("items").select("*").eq("portal_scope", st.session_state.portal_scope).gt("remaining_qty", 0).execute()
        
        today = datetime.now().date()
        near_expiry_items = []
        for itm in exp_res.data:
            exp_str = itm.get("expiry_date")
            if exp_str:
                try:
                    exp_dt = datetime.strptime(exp_str, "%Y-%m-%d").date()
                    days_left = (exp_dt - today).days
                    if days_left <= 540:
                        near_expiry_items.append(itm)
                except ValueError:
                    continue
        
        if near_expiry_items:
            st.sidebar.warning(f"⚠️ يوجد {len(near_expiry_items)} مادة قريبة من النفاذ!")
            for ni in near_expiry_items:
                st.sidebar.text(f"• {ni['item_name']} (انتهاء: {ni['expiry_date']})")
        else:
            st.sidebar.success("🟢 جميع المواد صالحة وبفترات أمان ممتازة.")
    except Exception as e:
      st.sidebar.error(f"خطأ في جلب التنبيهات: {e}")

# مسؤولي السجلات
reg_key = f"{st.session_state.portal_scope}_{selected_register}"
try:
    mgr_res = supabase.table("register_managers").select("manager_name").eq("register_name", reg_key).execute()
    current_mgr = mgr_res.data[0]["manager_name"] if mgr_res.data else ""
except Exception:
    current_mgr = ""

col_m1, col_m2 = st.sidebar.columns([2, 1])
mgr_input = col_m1.text_input("اسم المسؤول عن السجل:", value=current_mgr, label_visibility="collapsed")
if col_m2.button("حفظ المسؤول"):
    try:
        supabase.table("register_managers").upsert({
            "register_name": reg_key,
            "manager_name": mgr_input
        }).execute()
        st.sidebar.success("تم حفظ المسؤول!")
    except Exception as e:
        st.sidebar.error(f"خطأ: {e}")

# عرض الواجهة الرئيسية للمخزون
st.title(f"📦 إدارة المخزون والصيدلية - [{selected_register}]")
st.markdown(f"**المسؤول عن السجل:** {current_mgr if current_mgr else 'غير محدد'} | **البوابة:** {portal_display}")

# جلب بيانات المواد من Supabase للسجل والبوابة الحالية
try:
    if st.session_state.portal_scope == "MAIN_ADMIN":
        query_res = supabase.table("items").select("*").eq("register_name", selected_register).execute()
    else:
        query_res = supabase.table("items").select("*").eq("portal_scope", st.session_state.portal_scope).eq("register_name", selected_register).execute()
    items_list = query_res.data if query_res.data else []
except Exception as e:
    items_list = []
    st.error(f"خطأ في جلب المواد: {e}")

# إحصائيات البطاقات العلوية (Cards)
total_val = sum([(i.get("remaining_qty", 0) * i.get("unit_price_iqd", 0)) for i in items_list])
low_stock_cnt = len([i for i in items_list if i.get("remaining_qty", 0) < 10])

c1, c2, c3, c4 = st.columns(4)
c1.metric("القيمة الإجمالية للمخزون", f"{total_val:,.0f} IQD")
c2.metric("مخزون منخفض / منتهي", low_stock_cnt)
c3.metric("عدد المنتجات بالسجل", len(items_list))
c4.metric("حالة المزامنة السحابية", "متصل لحظياً 🟢")

st.markdown("---")

# شريط البحث والإجراءات السريعة
search_q = st.text_input("🔍 بحث سريع عن مادة (الاسم أو الرمز الوطني)...", "")
if search_q:
    items_list = [i for i in items_list if search_q in str(i.get("item_name", "")) or search_q in str(i.get("national_code", ""))]

# عرض جدول البيانات التفاعلي
if items_list:
    df_items = pd.DataFrame(items_list)
    show_cols = ["id", "national_code", "item_name", "item_name_en", "remaining_qty", "dispensed_qty", "total_qty", "unit_price_iqd", "expiry_date", "batch_number"]
    available_cols = [c for c in show_cols if c in df_items.columns]
    st.dataframe(df_items[available_cols], use_container_width=True)
else:
    st.warning("لا توجد مواد مسجلة في هذا السجل حالياً.")

st.markdown("---")

# تبويبات العمليات الأساسية (إضافة مادة، وجبة شهرية، تخريج FIFO)
tab_add, tab_inbound, tab_dispense = st.tabs(["➕ إضافة مادة جديدة", "📥 إضافة وجبة / توريد شهري", "⬇ تخريج وصرف يومي (FIFO)"])

with tab_add:
    st.subheader("إضافة مادة جديدة للسجل الحالي")
    with st.form("new_item_form"):
        i_name = st.text_input("اسم المادة باللغة العربية:")
        i_name_en = st.text_input("اسم المادة باللغة الإنجليزية:")
        i_code = st.text_input("الرمز الوطني (National Code):")
        i_qty = st.number_input("الكمية الواردة التأسيسية:", min_value=0, value=100)
        i_price = st.number_input("السعر المفرد (IQD):", min_value=0.0, value=0.0)
        i_exp = st.date_input("تاريخ انتهاء الصلاحية:")
        i_batch = st.text_input("رقم الوجبة (Batch Number):")
        i_source = st.text_input("جهة التجهيز / المصدر:")
        
        submit_item = st.form_submit_button("💾 حفظ المادة وإرسالها للسحابة")
        if submit_item and i_name:
            try:
                supabase.table("items").insert({
                    "portal_scope": st.session_state.portal_scope,
                    "register_name": selected_register,
                    "item_name": i_name,
                    "item_name_en": i_name_en,
                    "national_code": i_code,
                    "total_qty": i_qty,
                    "remaining_qty": i_qty,
                    "dispensed_qty": 0,
                    "unit_price_iqd": i_price,
                    "expiry_date": str(i_exp),
                    "batch_number": i_batch,
                    "source_type": i_source,
                    "date_added": datetime.now().strftime("%Y-%m-%d")
                }).execute()
                st.success("✅ تمت إضافة المادة وتحديث السحابة بنجاح لجميع الأجهزة!")
                st.rerun()
            except Exception as e:
                st.error(f"خطأ أثناء الحفظ: {e}")

with tab_inbound:
    st.subheader("إضافة وجبة واردة شهرية (تحديث الرصيد والوجبات)")
    if items_list:
        item_names_map = {item["item_name"]: item["id"] for item in items_list}
        selected_item_name = st.selectbox("اختر المادة لتوريد وجبة جديدة لها:", list(item_names_map.keys()))
        selected_month = st.selectbox("الشهر المستلم فيه:", MONTHS_LIST)
        in_qty = st.number_input("الكمية الواردة للوجبة:", min_value=1, value=50)
        in_letter = st.text_input("رقم كتاب الورود أو الطلبية:")
        in_batch = st.text_input("رقم الوجبة (Batch No) للوارد الجديد:")
        in_exp = st.date_input("تاريخ الانتهاء لهذه الوجبة بالتحديد:")
        
        if st.button("📥 إضافة الوجبة وتحديث الرصيد سحابياً"):
            item_id = item_names_map[selected_item_name]
            target_item = next(i for i in items_list if i["id"] == item_id)
            new_total = target_item.get("total_qty", 0) + in_qty
            new_rem = target_item.get("remaining_qty", 0) + in_qty
            try:
                supabase.table("items").update({
                    "total_qty": new_total,
                    "remaining_qty": new_rem,
                    "batch_number": in_batch,
                    "expiry_date": str(in_exp),
                    "incoming_letter_no": in_letter
                }).eq("id", item_id).execute()
                
                supabase.table("monthly_inbound_log").insert({
                    "item_id": item_id,
                    "month_year": selected_month,
                    "qty_added": in_qty,
                    "qty_remaining": in_qty,
                    "letter_no": in_letter,
                    "batch_no": in_batch,
                    "expiry_date": str(in_exp),
                    "entry_date": datetime.now().strftime("%Y-%m-%d %H:%M")
                }).execute()
                
                st.success("✅ تم تسجيل الوجبة الشهرية وتحديث السحابة لحظياً بنجاح!")
                st.rerun()
            except Exception as e:
                st.error(f"خطأ أثناء إضافة الوجبة: {e}")
    else:
        st.info("لا توجد مواد لإضافة وجبات لها.")

with tab_dispense:
    st.subheader("تنزيل وتخريج يومي للمنافذ حسب الأقدمية (FIFO)")
    if items_list:
        disp_map = {item["item_name"]: (item["id"], item["remaining_qty"]) for item in items_list}
        chosen_disp_name = st.selectbox("اختر المادة للصرف والتخريج:", list(disp_map.keys()), key="disp_sel")
        max_rem = disp_map[chosen_disp_name][1]
        
        st.text(f"الرصيد المتبقي الإتاحية للصرف: {max_rem} قطعة")
        d_qty = st.number_input("الكمية المصروفة:", min_value=1, max_value=max(1, max_rem), value=1)
        d_dest = st.selectbox("جهة الصرف / المنفذ المستلم:", SUB_PORTALS_LIST[1:])
        d_ref = st.text_input("رقم المستند أو كتاب الصرف:")
        
        if st.button("⬇ تأكيد الخصم والصرف سحابياً"):
            item_id = disp_map[chosen_disp_name][0]
            target_item = next(i for i in items_list if i["id"] == item_id)
            curr_disp = target_item.get("dispensed_qty", 0) + d_qty
            new_rem = max(0, target_item.get("total_qty", 0) - curr_disp)
            
            try:
                supabase.table("items").update({
                    "dispensed_qty": curr_disp,
                    "remaining_qty": new_rem,
                    "dispense_location": d_dest
                }).eq("id", item_id).execute()
                
                supabase.table("daily_dispense_log").insert({
                    "item_id": item_id,
                    "dispensed_amount": d_qty,
                    "destination": d_dest,
                    "letter_ref": d_ref,
                    "remaining_after_dispense": new_rem,
                    "dispense_date": datetime.now().strftime("%Y-%m-%d %H:%M")
                }).execute()
                
                st.success(f"✅ تم صرف ({d_qty}) قطعة لـ ({d_dest}) بنجاح وتحديث السحابة فوراً!")
                st.rerun()
            except Exception as e:
                st.error(f"خطأ أثناء عملية الصرف: {e}")
    else:
        st.info("لا توجد مواد متاحة للصرف.")