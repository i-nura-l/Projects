import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re
from io import BytesIO
import base64

# Page config
st.set_page_config(
    page_title="Student Data Manager",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for calm, modern design
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stApp {
        max-width: 100%;
    }
    h1, h2, h3 {
        color: #2c3e50;
        font-weight: 600;
    }
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    .stButton>button {
        background-color: #5dade2;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #3498db;
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        color: #2c3e50;
    }
</style>
""", unsafe_allow_html=True)

# Translation dictionary
TRANSLATIONS = {
    "en": {
        "title": "🎓 Student Data Manager",
        "subtitle": "Clean, Analyze & Manage Student Records",
        "language": "Language",
        "upload_clean": "📤 Upload & Clean Data",
        "analysis": "📊 Analysis Dashboard",
        "merge": "🔄 Update & Merge Data",
        "upload_files": "Upload Excel Files (.xls, .xlsx)",
        "drag_drop": "Drag and drop files here or click to browse",
        "processing": "Processing data...",
        "success": "✅ Processing complete!",
        "total_students": "Total Students",
        "with_contacts": "With Contacts",
        "without_contacts": "Without Contacts",
        "download_cleaned": "📥 Download Cleaned Data",
        "year_filter": "Filter by Year",
        "faculty_filter": "Filter by Faculty",
        "edu_level_filter": "Filter by Education Level",
        "all": "All",
        "search_placeholder": "Search by name...",
        "students_by_year": "Students by Year",
        "students_by_faculty": "Students by Faculty",
        "graduation_trend": "Graduation Trend Over Years",
        "contact_completeness": "Contact Information Completeness",
        "upload_old": "Upload Old Dataset",
        "upload_new": "Upload New Dataset",
        "merge_data": "🔄 Merge Data",
        "updated_records": "Updated Records",
        "added_records": "Added Records",
        "download_merged": "📥 Download Merged Data",
        "no_data": "No data available. Please upload files first.",
        "error": "Error processing files. Please check format.",
    },
    "ru": {
        "title": "🎓 Управление данными студентов",
        "subtitle": "Очистка, анализ и управление записями студентов",
        "language": "Язык",
        "upload_clean": "📤 Загрузка и очистка данных",
        "analysis": "📊 Панель анализа",
        "merge": "🔄 Обновление и объединение данных",
        "upload_files": "Загрузите Excel файлы (.xls, .xlsx)",
        "drag_drop": "Перетащите файлы сюда или нажмите для выбора",
        "processing": "Обработка данных...",
        "success": "✅ Обработка завершена!",
        "total_students": "Всего студентов",
        "with_contacts": "С контактами",
        "without_contacts": "Без контактов",
        "download_cleaned": "📥 Скачать очищенные данные",
        "year_filter": "Фильтр по году",
        "faculty_filter": "Фильтр по факультету",
        "edu_level_filter": "Фильтр по уровню образования",
        "all": "Все",
        "search_placeholder": "Поиск по имени...",
        "students_by_year": "Студенты по годам",
        "students_by_faculty": "Студенты по факультетам",
        "graduation_trend": "Динамика выпусков по годам",
        "contact_completeness": "Полнота контактной информации",
        "upload_old": "Загрузите старый набор данных",
        "upload_new": "Загрузите новый набор данных",
        "merge_data": "🔄 Объединить данные",
        "updated_records": "Обновлено записей",
        "added_records": "Добавлено записей",
        "download_merged": "📥 Скачать объединенные данные",
        "no_data": "Нет данных. Пожалуйста, загрузите файлы.",
        "error": "Ошибка обработки файлов. Проверьте формат.",
    }
}

# Initialize session state
if 'lang' not in st.session_state:
    st.session_state.lang = 'en'
if 'cleaned_data' not in st.session_state:
    st.session_state.cleaned_data = None
if 'merged_data' not in st.session_state:
    st.session_state.merged_data = None


def t(key):
    """Translation helper"""
    return TRANSLATIONS[st.session_state.lang].get(key, key)


def clean_phone_number(phone):
    """Clean and standardize phone numbers to +996XXXXXXXXX format"""
    if pd.isna(phone):
        return None

    phone = str(phone).strip()
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)

    # Handle different formats
    if len(digits) == 9:  # 558640927
        return f"+996{digits}"
    elif len(digits) == 10 and digits.startswith('0'):  # 0558640927
        return f"+996{digits[1:]}"
    elif len(digits) == 12 and digits.startswith('996'):  # 996558640927
        return f"+{digits}"
    elif len(digits) == 13 and digits.startswith('996'):  # Already correct
        return f"+{digits}"

    return phone  # Return original if format unclear


def extract_year_from_filename(filename):
    """Extract all years from filename (e.g., 2023_2024)"""
    matches = re.findall(r'20\d{2}', filename)
    if matches:
        # Return the first year found
        return int(matches[0])
    return datetime.now().year


def process_uploaded_files(uploaded_files):
    """Process and combine multiple Excel files"""
    all_data = []

    for file in uploaded_files:
        try:
            # Read Excel file (handles both .xls and .xlsx)
            df = pd.read_excel(file, engine=None)

            # Priority 1: Check if YEAR column exists in the data
            if 'YEAR' not in df.columns:
                # Priority 2: Extract year from filename
                year = extract_year_from_filename(file.name)
                df['YEAR'] = year
            else:
                # YEAR column exists, but fill missing values from filename
                filename_year = extract_year_from_filename(file.name)
                df['YEAR'] = df['YEAR'].fillna(filename_year)

            # Convert YEAR to integer
            df['YEAR'] = df['YEAR'].astype(int)

            all_data.append(df)
        except Exception as e:
            st.error(f"Error processing {file.name}: {str(e)}")

    if not all_data:
        return None

    # Combine all dataframes
    combined_df = pd.concat(all_data, ignore_index=True)

    # Clean phone numbers
    if 'CONTACT_PHONES' in combined_df.columns:
        combined_df['CONTACT_PHONES_CLEANED'] = combined_df['CONTACT_PHONES'].apply(clean_phone_number)

    # Clean email
    if 'EMAIL' in combined_df.columns:
        combined_df['EMAIL'] = combined_df['EMAIL'].str.strip().str.lower()

    return combined_df


def split_by_contact(df):
    """Split dataset into with/without contacts"""
    if 'CONTACT_PHONES_CLEANED' not in df.columns:
        return df, pd.DataFrame()

    with_contacts = df[df['CONTACT_PHONES_CLEANED'].notna()].copy()
    without_contacts = df[df['CONTACT_PHONES_CLEANED'].isna()].copy()

    return with_contacts, without_contacts


def create_excel_download(df_with, df_without):
    """Create Excel file with two sheets"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_with.to_excel(writer, sheet_name='With Contacts', index=False)
        df_without.to_excel(writer, sheet_name='Without Contacts', index=False)

    output.seek(0)
    return output


# Sidebar
with st.sidebar:
    st.markdown("### " + t("language"))
    lang_choice = st.radio("", ["English", "Русский"],
                           index=0 if st.session_state.lang == 'en' else 1,
                           label_visibility="collapsed")
    st.session_state.lang = 'en' if lang_choice == "English" else 'ru'

    st.markdown("---")
    st.markdown("### Navigation")
    page = st.radio("", [t("upload_clean"), t("analysis"), t("merge")],
                    label_visibility="collapsed")

# Main title
st.title(t("title"))
st.markdown(f"*{t('subtitle')}*")
st.markdown("---")

# PAGE 1: Upload & Clean
if page == t("upload_clean"):
    st.header(t("upload_clean"))

    uploaded_files = st.file_uploader(
        t("upload_files"),
        type=['xls', 'xlsx'],
        accept_multiple_files=True,
        help=t("drag_drop")
    )

    if uploaded_files:
        with st.spinner(t("processing")):
            df = process_uploaded_files(uploaded_files)

            if df is not None:
                st.session_state.cleaned_data = df
                st.success(t("success"))

                # Split data
                df_with, df_without = split_by_contact(df)

                # KPI Metrics
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(t("total_students"), len(df))

                with col2:
                    st.metric(t("with_contacts"), len(df_with))

                with col3:
                    st.metric(t("without_contacts"), len(df_without))

                # Preview data
                st.subheader("Data Preview")
                tab1, tab2 = st.tabs([t("with_contacts"), t("without_contacts")])

                with tab1:
                    st.dataframe(df_with.head(50), use_container_width=True)

                with tab2:
                    st.dataframe(df_without.head(50), use_container_width=True)

                # Download button
                excel_file = create_excel_download(df_with, df_without)
                st.download_button(
                    label=t("download_cleaned"),
                    data=excel_file,
                    file_name=f"cleaned_students_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

# PAGE 2: Analysis Dashboard
elif page == t("analysis"):
    st.header(t("analysis"))

    # Option to add more files
    with st.expander("➕ Add More Files to Existing Data"):
        additional_files = st.file_uploader(
            "Upload additional Excel files",
            type=['xls', 'xlsx'],
            accept_multiple_files=True,
            key="additional_files"
        )

        if additional_files and st.button("Add to Dataset"):
            with st.spinner(t("processing")):
                new_df = process_uploaded_files(additional_files)
                if new_df is not None:
                    if st.session_state.cleaned_data is not None:
                        # Combine with existing data
                        st.session_state.cleaned_data = pd.concat(
                            [st.session_state.cleaned_data, new_df],
                            ignore_index=True
                        )
                        st.success(f"✅ Added {len(new_df)} records to dataset!")
                    else:
                        st.session_state.cleaned_data = new_df
                        st.success(f"✅ Loaded {len(new_df)} records!")

    if st.session_state.cleaned_data is None:
        st.warning(t("no_data"))
    else:
        df = st.session_state.cleaned_data

        # Filters
        col1, col2, col3 = st.columns(3)

        with col1:
            years = [t("all")] + sorted(df['YEAR'].unique().tolist())
            selected_year = st.selectbox(t("year_filter"), years)

        with col2:
            if 'SPEC_RU' in df.columns:
                faculties = [t("all")] + sorted([str(x) for x in df['SPEC_RU'].dropna().unique()])
            else:
                faculties = [t("all")]
            selected_faculty = st.selectbox(t("faculty_filter"), faculties)

        with col3:
            if 'EDU_LEVEL' in df.columns:
                edu_levels = [t("all")] + sorted([str(x) for x in df['EDU_LEVEL'].dropna().unique()])
            else:
                edu_levels = [t("all")]
            selected_level = st.selectbox(t("edu_level_filter"), edu_levels)

        # Apply filters
        filtered_df = df.copy()
        if selected_year != t("all"):
            filtered_df = filtered_df[filtered_df['YEAR'] == selected_year]
        if selected_faculty != t("all") and 'SPEC_RU' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['SPEC_RU'].astype(str) == selected_faculty]
        if selected_level != t("all") and 'EDU_LEVEL' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['EDU_LEVEL'].astype(str) == selected_level]

        # Search
        search_term = st.text_input(t("search_placeholder"))
        if search_term:
            mask = filtered_df.apply(lambda row: search_term.lower() in str(row).lower(), axis=1)
            filtered_df = filtered_df[mask]

        # Charts
        col1, col2 = st.columns(2)

        with col1:
            # Students by Year
            if len(filtered_df) > 0:
                year_counts = filtered_df['YEAR'].value_counts().sort_index()
                fig1 = px.bar(
                    x=year_counts.index.tolist(),
                    y=year_counts.values.tolist(),
                    labels={'x': 'Year', 'y': 'Students'},
                    title=t("students_by_year"),
                    color_discrete_sequence=['#5dade2']
                )
                fig1.update_layout(showlegend=False)
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("No data available for the selected filters")

        with col2:
            # Contact Completeness
            if len(filtered_df) > 0:
                has_contact = filtered_df['CONTACT_PHONES_CLEANED'].notna().sum()
                no_contact = filtered_df['CONTACT_PHONES_CLEANED'].isna().sum()

                fig2 = go.Figure(data=[go.Pie(
                    labels=[t("with_contacts"), t("without_contacts")],
                    values=[has_contact, no_contact],
                    marker_colors=['#52be80', '#ec7063']
                )])
                fig2.update_layout(title=t("contact_completeness"))
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No data available for the selected filters")

        # Students by Faculty
        if 'SPEC_RU' in filtered_df.columns and len(filtered_df) > 0:
            faculty_counts = filtered_df['SPEC_RU'].value_counts().head(10)
            if len(faculty_counts) > 0:
                fig3 = px.bar(
                    y=faculty_counts.index.tolist(),
                    x=faculty_counts.values.tolist(),
                    orientation='h',
                    labels={'x': 'Students', 'y': 'Faculty'},
                    title=t("students_by_faculty"),
                    color_discrete_sequence=['#f39c12']
                )
                st.plotly_chart(fig3, use_container_width=True)

        # Graduation Trend
        if len(df) > 0:
            trend_data = df.groupby('YEAR').size().reset_index(name='count')
            fig4 = px.line(
                trend_data,
                x='YEAR',
                y='count',
                markers=True,
                title=t("graduation_trend"),
                labels={'YEAR': 'Year', 'count': 'Students'}
            )
            st.plotly_chart(fig4, use_container_width=True)

        # Filtered data preview
        st.subheader("Filtered Data")
        st.dataframe(filtered_df, use_container_width=True)

        # Download filtered data
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Filtered Data",
            data=csv,
            file_name=f"filtered_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

# PAGE 3: Update & Merge
elif page == t("merge"):
    st.header(t("merge"))

    col1, col2 = st.columns(2)

    with col1:
        old_file = st.file_uploader(t("upload_old"), type=['xls', 'xlsx'], key="old")

    with col2:
        new_file = st.file_uploader(t("upload_new"), type=['xls', 'xlsx'], key="new")

    if old_file and new_file:
        if st.button(t("merge_data"), use_container_width=True):
            with st.spinner(t("processing")):
                try:
                    # Read files
                    df_old = pd.read_excel(old_file, engine=None)
                    df_new = pd.read_excel(new_file, engine=None)

                    # Check for required columns
                    required_cols = ['NAME_NATIVE', 'SURNAME_NATIVE']
                    missing_old = [col for col in required_cols if col not in df_old.columns]
                    missing_new = [col for col in required_cols if col not in df_new.columns]

                    if missing_old or missing_new:
                        error_msg = ""
                        if st.session_state.lang == 'en':
                            error_msg = "❌ **Error: Missing required columns**\n\n"
                            if missing_old:
                                error_msg += f"Old file is missing: {', '.join(missing_old)}\n"
                            if missing_new:
                                error_msg += f"New file is missing: {', '.join(missing_new)}\n"
                            error_msg += "\n**Required columns:** NAME_NATIVE, SURNAME_NATIVE\n\nPlease check your files and try again."
                        else:
                            error_msg = "❌ **Ошибка: Отсутствуют обязательные столбцы**\n\n"
                            if missing_old:
                                error_msg += f"Старый файл не содержит: {', '.join(missing_old)}\n"
                            if missing_new:
                                error_msg += f"Новый файл не содержит: {', '.join(missing_new)}\n"
                            error_msg += "\n**Обязательные столбцы:** NAME_NATIVE, SURNAME_NATIVE\n\nПожалуйста, проверьте файлы и попробуйте снова."

                        st.error(error_msg)
                        st.stop()

                    # Create matching key
                    df_old['match_key'] = (df_old['NAME_NATIVE'].astype(str) + '_' +
                                           df_old['SURNAME_NATIVE'].astype(str)).str.lower().str.strip()
                    df_new['match_key'] = (df_new['NAME_NATIVE'].astype(str) + '_' +
                                           df_new['SURNAME_NATIVE'].astype(str)).str.lower().str.strip()

                    # Merge data
                    merged = df_old.set_index('match_key')
                    updated_count = 0
                    added_count = 0

                    for idx, row in df_new.iterrows():
                        key = row['match_key']

                        if key in merged.index:
                            # Update existing record
                            for col in ['EMAIL', 'CONTACT_PHONES']:
                                if col in df_new.columns and pd.notna(row[col]):
                                    merged.at[key, col] = row[col]
                            updated_count += 1
                        else:
                            # Add new record
                            merged = pd.concat([merged, pd.DataFrame([row]).set_index('match_key')])
                            added_count += 1

                    merged = merged.reset_index(drop=True)
                    merged = merged.drop('match_key', axis=1, errors='ignore')

                    st.session_state.merged_data = merged

                    # Show metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(t("total_students"), len(merged))
                    with col2:
                        st.metric(t("updated_records"), updated_count)
                    with col3:
                        st.metric(t("added_records"), added_count)

                    st.success(t("success"))

                    # Preview
                    st.dataframe(merged.head(50), use_container_width=True)

                    # Download
                    output = BytesIO()
                    merged.to_excel(output, index=False, engine='openpyxl')
                    output.seek(0)

                    st.download_button(
                        label=t("download_merged"),
                        data=output,
                        file_name=f"merged_data_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                except Exception as e:
                    if st.session_state.lang == 'en':
                        st.error(
                            f"❌ **Error processing files**\n\n{str(e)}\n\nPlease check that:\n- Files are in correct Excel format (.xls or .xlsx)\n- Files contain NAME_NATIVE and SURNAME_NATIVE columns\n- Data is properly formatted")
                    else:
                        st.error(
                            f"❌ **Ошибка обработки файлов**\n\n{str(e)}\n\nПожалуйста, проверьте что:\n- Файлы в правильном формате Excel (.xls или .xlsx)\n- Файлы содержат столбцы NAME_NATIVE и SURNAME_NATIVE\n- Данные правильно отформатированы")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #7f8c8d;'>Made with ❤️ for Student Data Management</div>",
    unsafe_allow_html=True
)