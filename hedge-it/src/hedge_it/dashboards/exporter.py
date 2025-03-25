import streamlit as st
from fpdf import FPDF

from hedge_it.commons import get_logger

log = get_logger()


def generate_pdf(dataframe, filename="stock_composition.pdf"):
    log.info(f"Generating PDF: {filename}")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Custom Index Stock Report", ln=True, align="C")

    pdf.set_font("Arial", style="B", size=10)
    for column in dataframe.columns:
        pdf.cell(40, 10, column, border=1, align="C")
    pdf.ln()

    pdf.set_font("Arial", size=10)
    for _, row in dataframe.iterrows():
        for value in row:
            pdf.cell(40, 10, str(value), border=1, align="C")
        pdf.ln()

    pdf.output(filename)
    return filename


def download_pdf_button(selected_date_data):
    pdf_file = generate_pdf(selected_date_data)
    with open(pdf_file, "rb") as f:
        st.download_button(
            label="Download PDF",
            data=f,
            file_name="stock_composition.pdf",
            mime="application/pdf",
        )


def generate_csv(dataframe, filename="stock_composition.csv"):
    log.info(f"Exporting DataFrame to CSV: {filename}")
    dataframe.to_csv(filename, index=False)
    log.info(f"CSV export completed: {filename}")
    return filename


def download_csv_button(selected_date_data):
    csv_file = generate_csv(selected_date_data)
    with open(csv_file, "rb") as f:
        st.download_button(
            label="Download CSV",
            data=f,
            file_name="stock_composition.csv",
            mime="text/csv",
        )
