# app.py
import streamlit as st
import pandas as pd
import re
from io import BytesIO
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="Student Data Manager", layout="wide", initial_sidebar_state="expanded")

# ---------- Styles (modern calm) ----------
st.markdown(
    """
    <style>
    /* Calm modern card */
    .stApp {
        background: linear-gradient(180deg, #F7FAFC 0%, #FFFFFF 100%);
    }
    .title {
        font-size:28px;
        font-weight:700;
    }
    .subtitle {
        color: #6B7280;
        font-size:14px;
    }
    .kpi {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 14px;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Language dictionary ----------
LANG = {
    "en": {
        "app_title": "Student Data Manager",
        "upload_instructions": "Upload multiple .xls/.xlsx files (different years). Columns expected: EDU_LEVEL, CIPHER, SPEC_RU, RU, STUD_ID, NAME_NATIVE, SURNAME_NATIVE, PATRONYMIC, BIRTH_DATE, CONTACT_PHONES, EMAIL",
        "upload_button": "Upload files",
        "process": "Process files",
        "download_cleaned": "Download cleaned Excel",
        "with_contacts": "Students with contacts",
        "without_contacts": "Students without contacts",
        "total_students": "Total students",
        "students_with": "With contact",
        "students_without": "Without contact",
        "analysis": "Analysis Dashboard",
        "filters": "Filters",
        "year": "Year",
        "faculty": "Faculty (SPEC_RU)",
        "edu_level": "Education Level",
        "chart_students_year": "Students by Year",
        "chart_by_faculty": "Students by Faculty",
        "chart_trend": "Graduation Trend (by Year)",
        "contact_completeness": "Contact completeness",
        "search_name": "Search name",
        "download_filtered": "Download filtered data",
        "update_merge": "Update / Merge Data",
        "upload_master": "(Optional) Upload master file to update (or use 'Processed master' above)",
        "upload_updates": "Upload updates file",
        "merge_button": "Merge & Update",
        "merge_summary": "Merge summary",
        "updated": "Records updated",
        "added": "New records added",
        "download_merged": "Download merged file",
        "no_data": "No data loaded yet. Upload files first.",
        "invalid_phone_example": "Phone converted; unrecognized left blank.",
        "processing_complete": "Processing complete.",
    },
    "ru": {
        "app_title": "Управление Данными Студентов",
        "upload_instructions": "Загрузите несколько .xls/.xlsx файлов (разных лет). Ожидаемые столбцы: EDU_LEVEL, CIPHER, SPEC_RU, RU, STUD_ID, NAME_NATIVE, SURNAME_NATIVE, PATRONYMIC, BIRTH_DATE, CONTACT_PHONES, EMAIL",
        "upload_button": "Загрузить файлы",
        "process": "Обработать файлы",
        "download_cleaned": "Скачать очищенный Excel",
        "with_contacts": "Студенты с контактами",
        "without_contacts": "Студенты без контактов",
        "total_students": "Всего студентов",
        "students_with": "С контактами",
        "students_without": "Без контактов",
        "analysis": "Панель Анализа",
        "filters": "Фильтры",
        "year": "Год",
        "faculty": "Факультет (SPEC_RU)",
        "edu_level": "Уровень образования",
        "chart_students_year": "Студенты по годам",
        "chart_by_faculty": "Студенты по факультетам",
        "chart_trend": "Динамика выпусков (по годам)",
        "contact_completeness": "Наличие контактов",
        "search_name": "Поиск по имени",
        "download_filtered": "Скачать отфильтрованные данные",
        "update_merge": "Обновить / Слить данные",
        "upload_master": "(Опционально) Загрузите мастер-файл для обновления (или используйте 'Обработанный мастер' выше)",
        "upload_updates": "Загрузить файл с обновлениями",
        "merge_button": "Слить и обновить",
        "merge_summary": "Итог слияния",
        "updated": "Записей обновлено",
        "added": "Новых записей добавлено",
        "download_merged": "Скачать слитый файл",
        "no_data": "Данные не загружены. Сначала загрузите файлы.",
        "invalid_phone_example": "Телефон стандартизирован; нераспознаваемые оставлены пустыми.",
        "processing_complete": "Обработка завершена.",
    },
}

# ---------- Helpers ----------
def detect_year_from_filename(fname: str):
    # try to find a 4-digit year like 2021,2022 etc
    m = re.search(r"(20\d{2})", fname)
    if m:
        return int(m.group(1))
    return None

def normalize_phone(phone_raw: str):
    """
    Normalize phone numbers to +996XXXXXXXXX (Kyrgyzstan mobile expected 9 digits after code).
    Handles inputs like:
      0558640927 -> +996558640927
      558640927  -> +996558640927
      996558640927 -> +996558640927
      +996558640927 -> +996558640927
    If cannot parse cleanly, returns empty string.
    """
    if pd.isna(phone_raw):
        return ""
    s = str(phone_raw)
    # remove spaces, parentheses, hyphens, plus signs except leading
    digits = re.sub(r"[^\d+]", "", s)
    # Remove leading plus for processing
    digits = digits.lstrip('+')
    # If it contains country code 996 at start
    if digits.startswith("996") and len(digits) >= 12:
        # digits after 996 should be 9
        rest = digits[3:]
        if len(rest) == 9:
            return "+996" + rest
        # if rest is 10 and starts with 0, drop leading 0
        if len(rest) == 10 and rest.startswith("0"):
            return "+996" + rest[1:]
    # If length 9 -> assume national without leading zero
    if len(digits) == 9:
        return "+996" + digits
    # If length 10 and starts with 0 -> drop 0
    if len(digits) == 10 and digits.startswith("0"):
        return "+996" + digits[1:]
    # If length 12 and starts with 996
    if len(digits) == 12 and digits.startswith("996"):
        return "+" + digits
    # If already formatted as +996... (rare here after strip)
    if s.startswith("+996") and len(s) >= 13:
        return s
    # fallback: try to extract last 9 digits
    last9 = re.sub(r"\D", "", s)[-9:]
    if len(last9) == 9:
        return "+996" + last9
    return ""


def combine_uploaded_files(uploaded_files):
    frames = []
    years = []
    for uploaded_file in uploaded_files:
        try:
            df = pd.read_excel(uploaded_file)
        except Exception:
            # try engine fallback
            df = pd.read_excel(uploaded_file, engine="xlrd")
        fname = getattr(uploaded_file, "name", "")
        year = detect_year_from_filename(fname) or None
        if year is not None:
            df["YEAR_SOURCE"] = year
            years.append(year)
        else:
            df["YEAR_SOURCE"] = None
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True, sort=False)
    # Ensure columns exist
    expected_cols = ["EDU_LEVEL","CIPHER","SPEC_RU","RU","STUD_ID","NAME_NATIVE","SURNAME_NATIVE","PATRONYMIC","BIRTH_DATE","CONTACT_PHONES","EMAIL","YEAR_SOURCE"]
    for c in expected_cols:
        if c not in combined.columns:
            combined[c] = pd.NA
    # Standardize phone
    combined["CONTACT_PHONES_STD"] = combined["CONTACT_PHONES"].apply(normalize_phone)
    # Create boolean
    combined["HAS_CONTACT"] = combined["CONTACT_PHONES_STD"].apply(lambda x: bool(str(x).strip()))
    # Create a helper normalized name key
    def key_name(r):
        n = str(r.get("NAME_NATIVE","") or "").strip().lower()
        s = str(r.get("SURNAME_NATIVE","") or "").strip().lower()
        return (n + " " + s).strip()
    combined["__NAME_KEY__"] = combined.apply(key_name, axis=1)
    return combined

def to_excel_bytes(df_with: pd.DataFrame, df_without: pd.DataFrame):
    output = BytesIO()
    now = datetime.now().strftime("%Y%m%d_%H%M")
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_with.to_excel(writer, sheet_name="with_contacts", index=False)
        df_without.to_excel(writer, sheet_name="without_contacts", index=False)
        writer.save()
    output.seek(0)
    return output

def df_to_excel_bytes(df, sheet_name="sheet"):
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        writer.save()
    out.seek(0)
    return out

# ---------- Sidebar: language & navigation ----------
if "lang" not in st.session_state:
    st.session_state.lang = "en"
lang_choice = st.sidebar.selectbox("Language / Язык", options=["English", "Русский"])
st.session_state.lang = "en" if lang_choice == "English" else "ru"
T = LANG[st.session_state.lang]

st.sidebar.title(T["app_title"])

page = st.sidebar.radio("", options=[T["upload_button"], T["analysis"], T["update_merge"]])

# ---------- Main Title ----------
st.markdown(f"<div class='title'>{T['app_title']}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='subtitle'>{T['upload_instructions']}</div>", unsafe_allow_html=True)
st.write("---")

# ---------- Page: Upload & Clean ----------
if page == T["upload_button"]:
    uploaded = st.file_uploader(T["upload_instructions"], accept_multiple_files=True, type=["xls", "xlsx"])
    if uploaded:
        with st.spinner(T["process"] + "..."):
            combined = combine_uploaded_files(uploaded)
            # store master in session state for other pages
            st.session_state.master = combined.copy()
        st.success(T["processing_complete"])
        # KPIs
        total = len(combined)
        with_cnt = combined["HAS_CONTACT"].sum()
        without_cnt = total - with_cnt
        col1, col2, col3 = st.columns([1,1,1])
        col1.markdown(f"<div class='kpi'><h3>{T['total_students']}</h3><h2 style='margin:0'>{total}</h2></div>", unsafe_allow_html=True)
        col2.markdown(f"<div class='kpi'><h3>{T['students_with']}</h3><h2 style='margin:0'>{with_cnt}</h2></div>", unsafe_allow_html=True)
        col3.markdown(f"<div class='kpi'><h3>{T['students_without']}</h3><h2 style='margin:0'>{without_cnt}</h2></div>", unsafe_allow_html=True)

        # Show samples
        st.write("Preview (first 15 rows):")
        st.dataframe(combined.head(15))

        # Split and download
        df_with = combined[combined["HAS_CONTACT"]].copy()
        df_without = combined[~combined["HAS_CONTACT"]].copy()

        excel_bytes = to_excel_bytes(df_with, df_without)
        nowtag = datetime.now().strftime("%Y%m%d")
        st.download_button(label=T["download_cleaned"], data=excel_bytes, file_name=f"cleaned_students_{nowtag}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # show note about phone normalization
        st.info(T["invalid_phone_example"])

    else:
        st.info(T["no_data"])

# ---------- Page: Analysis ----------
elif page == T["analysis"]:
    if "master" not in st.session_state or st.session_state.master is None or st.session_state.master.empty:
        st.info(T["no_data"])
    else:
        df = st.session_state.master.copy()
        # Sidebar filters
        st.sidebar.header(T["filters"])
        years = sorted(df["YEAR_SOURCE"].dropna().unique().tolist())
        years = [int(y) for y in years if pd.notna(y)]
        year_sel = st.sidebar.multiselect(T["year"], options=years, default=years if years else [])
        faculties = sorted(df["SPEC_RU"].dropna().unique().tolist())
        fac_sel = st.sidebar.multiselect(T["faculty"], options=faculties, default=faculties if faculties else [])
        edu_levels = sorted(df["EDU_LEVEL"].dropna().unique().tolist())
        edu_sel = st.sidebar.multiselect(T["edu_level"], options=edu_levels, default=edu_levels if edu_levels else [])

        # apply filters
        if year_sel:
            df = df[df["YEAR_SOURCE"].isin(year_sel)]
        if fac_sel:
            df = df[df["SPEC_RU"].isin(fac_sel)]
        if edu_sel:
            df = df[df["EDU_LEVEL"].isin(edu_sel)]

        # search
        search = st.sidebar.text_input(T["search_name"])
        if search:
            search_l = search.strip().lower()
            df = df[df["__NAME_KEY__"].str.contains(search_l, na=False)]

        # Charts
        col1, col2 = st.columns((2,1))
        # Students by Year
        if not df.empty:
            by_year = df.groupby("YEAR_SOURCE").size().reset_index(name="count").sort_values("YEAR_SOURCE")
            fig1 = px.bar(by_year, x="YEAR_SOURCE", y="count", title=T["chart_students_year"], labels={"YEAR_SOURCE": T["year"], "count":"Count"})
            col1.plotly_chart(fig1, use_container_width=True)

            # Students by Faculty (horizontal)
            by_fac = df.groupby("SPEC_RU").size().reset_index(name="count").sort_values("count", ascending=True)
            fig2 = px.bar(by_fac, x="count", y="SPEC_RU", orientation="h", title=T["chart_by_faculty"], labels={"count":"Count", "SPEC_RU":T["faculty"]})
            col1.plotly_chart(fig2, use_container_width=True)

            # Trend line
            trend = df.groupby("YEAR_SOURCE").size().reset_index(name="count").sort_values("YEAR_SOURCE")
            fig3 = px.line(trend, x="YEAR_SOURCE", y="count", markers=True, title=T["chart_trend"], labels={"YEAR_SOURCE":T["year"], "count":"Count"})
            col2.plotly_chart(fig3, use_container_width=True)

            # Contact completeness
            comp = pd.DataFrame({
                "has_contact": ["Has contact", "No contact"],
                "count": [int(df["HAS_CONTACT"].sum()), int((~df["HAS_CONTACT"]).sum())]
            })
            fig4 = px.pie(comp, values="count", names="has_contact", title=T["contact_completeness"])
            col2.plotly_chart(fig4, use_container_width=True)

        else:
            st.write("No rows after filters.")

        # Data table and download filtered
        st.write("Filtered data preview:")
        st.dataframe(df.head(100))
        xlsx = df_to_excel_bytes(df, sheet_name="filtered")
        st.download_button(label=T["download_filtered"], data=xlsx, file_name=f"filtered_students_{datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ---------- Page: Update / Merge ----------
elif page == T["update_merge"]:
    st.write("### " + T["update_merge"])
    st.write(T["upload_master"])
    master_file = st.file_uploader("Master file (optional)", type=["xls","xlsx"], key="master_update")
    st.write(T["upload_updates"])
    updates_file = st.file_uploader("", type=["xls","xlsx"], key="updates_file")

    use_session_master = st.checkbox("Use processed master from this session (if exists)", value=True)

    if st.button(T["merge_button"]):
        # determine base master
        if use_session_master and "master" in st.session_state and st.session_state.master is not None and not st.session_state.master.empty:
            base = st.session_state.master.copy()
        elif master_file:
            base = pd.read_excel(master_file)
            # add standard columns if missing
            if "__NAME_KEY__" not in base.columns:
                base["__NAME_KEY__"] = (base.get("NAME_NATIVE","").fillna("").astype(str).str.strip().str.lower() + " " + base.get("SURNAME_NATIVE","").fillna("").astype(str).str.strip().str.lower()).str.strip()
            if "CONTACT_PHONES_STD" not in base.columns and "CONTACT_PHONES" in base.columns:
                base["CONTACT_PHONES_STD"] = base["CONTACT_PHONES"].apply(normalize_phone)
                base["HAS_CONTACT"] = base["CONTACT_PHONES_STD"].apply(lambda x: bool(str(x).strip()))
        else:
            st.warning(T["no_data"])
            st.stop()

        if not updates_file:
            st.warning(T["upload_updates"])
            st.stop()
        updates = pd.read_excel(updates_file)
        # prepare keys
        updates["__NAME_KEY__"] = (updates.get("NAME_NATIVE","").fillna("").astype(str).str.strip().str.lower() + " " + updates.get("SURNAME_NATIVE","").fillna("").astype(str).str.strip().str.lower()).str.strip()

        # We'll do an inner update on columns present in updates (excluding name keys)
        merge_cols = [c for c in updates.columns if c not in ["__NAME_KEY__"]]
        updated_count = 0
        added_count = 0

        # create index on base by name key for quick lookup
        base_index = {k: i for i, k in enumerate(base["__NAME_KEY__"].fillna("").astype(str))}
        base_records = base.copy()

        for idx, row in updates.iterrows():
            key = row["__NAME_KEY__"]
            if key in base_index and key != "":
                i = base_index[key]
                # update non-null values from updates into base
                updated = False
                for c in merge_cols:
                    val = row.get(c, pd.NA)
                    if pd.notna(val) and str(val).strip() != "":
                        base_records.at[i, c] = val
                        updated = True
                if updated:
                    updated_count += 1
            else:
                # add as new record
                added_count += 1
                base_records = pd.concat([base_records, pd.DataFrame([row.to_dict()])], ignore_index=True)

        # Recompute normalized phone for safety
        if "CONTACT_PHONES" in base_records.columns:
            base_records["CONTACT_PHONES_STD"] = base_records["CONTACT_PHONES"].apply(normalize_phone)
            base_records["HAS_CONTACT"] = base_records["CONTACT_PHONES_STD"].apply(lambda x: bool(str(x).strip()))
        # ensure name key present
        if "__NAME_KEY__" not in base_records.columns:
            base_records["__NAME_KEY__"] = (base_records.get("NAME_NATIVE","").fillna("").astype(str).str.strip().str.lower() + " " + base_records.get("SURNAME_NATIVE","").fillna("").astype(str).str.strip().str.lower()).str.strip()

        st.success(T["processing_complete"])
        st.write("### " + T["merge_summary"])
        st.write(f"- {T['updated']}: {updated_count}")
        st.write(f"- {T['added']}: {added_count}")

        # show few rows
        st.write("Preview of merged dataset (first 50 rows):")
        st.dataframe(base_records.head(50))

        # store as new master optionally
        st.session_state.master = base_records.copy()

        # download merged
        merged_bytes = df_to_excel_bytes(base_records, sheet_name="merged")
        st.download_button(label=T["download_merged"], data=merged_bytes, file_name=f"merged_students_{datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ---------- Footer ----------
st.write("---")
st.caption("Built for data cleaning, standardization, analysis, and merging. Designed with a calm modern theme.")
