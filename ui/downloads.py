"""
downloads.py
------------
Handles download functionality for simulation results.

Provides options for CSV (fast) or Excel (multi-sheet) export.
"""
import streamlit as st
import pandas as pd
import zipfile
from io import BytesIO


@st.cache_data
def generate_csv_zip(all_parts_df, wip_test, all_counts, all_ac_df, wip_df):
    """Generate ZIP file with CSVs - cached to avoid regeneration."""
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('parts.csv', all_parts_df.to_csv(index=False))
        zf.writestr('wip_test.csv', wip_test.to_csv(index=False))
        zf.writestr('count_fleet.csv', all_counts['fleet'].to_csv(index=False))
        zf.writestr('count_condition_f.csv', all_counts['condition_f'].to_csv(index=False))
        zf.writestr('count_depot.csv', all_counts['depot'].to_csv(index=False))
        zf.writestr('count_condition_a.csv', all_counts['condition_a'].to_csv(index=False))
        zf.writestr('ac.csv', all_ac_df.to_csv(index=False))
        zf.writestr('wip.csv', wip_df.to_csv(index=False))
    return zip_buffer.getvalue()


@st.cache_data
def generate_excel(all_parts_df, wip_test, all_counts, all_ac_df, wip_df):
    """Generate Excel file - cached to avoid regeneration."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        all_parts_df.to_excel(writer, sheet_name='parts', index=False)
        wip_test.to_excel(writer, sheet_name='wiptest', index=False)
        all_counts['fleet'].to_excel(writer, sheet_name='count_fleet', index=False)
        all_counts['condition_f'].to_excel(writer, sheet_name='count_cdf', index=False)
        all_counts['depot'].to_excel(writer, sheet_name='count_depot', index=False)
        all_counts['condition_a'].to_excel(writer, sheet_name='count_cda', index=False)
        all_ac_df.to_excel(writer, sheet_name='ac', index=False)
        wip_df.to_excel(writer, sheet_name='wip', index=False)
    return output.getvalue()


def render_download_section(datasets):
    """
    Render the download section with format selection.
    
    Parameters
    ----------
    datasets : DataSets
        DataSets object containing all_parts_df, all_ac_df, and wip_df.
    """
    st.markdown("---")
    st.subheader("💾 Download Results")
    
    # Format selection
    download_format = st.radio(
        "Select download format:",
        ["CSV (Fast)", "Excel (Slower, multi-sheet)"],
        horizontal=True,
        help="CSV creates a zip with separate files. Excel creates one file with multiple sheets but takes longer to generate."
    )
    
    if download_format == "CSV (Fast)":
        csv_data = generate_csv_zip(
            datasets.all_parts_df,
            datasets.wip_test,
            datasets.all_counts,
            datasets.all_ac_df,
            datasets.wip_df
        )
        
        st.download_button(
            label="📥 Download CSV Files (ZIP)",
            data=csv_data,
            file_name="simulation_results.zip",
            mime="application/zip"
        )
    
    else:  # Excel format
        st.info("⏳ Excel generation may take a few seconds for large datasets.")
        
        excel_data = generate_excel(
            datasets.all_parts_df,
            datasets.wip_test,
            datasets.all_counts,
            datasets.all_ac_df,
            datasets.wip_df
        )
        
        st.download_button(
            label="📥 Download Excel File",
            data=excel_data,
            file_name="simulation_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
