import streamlit as st
import tempfile
from mathpix import MathpixConverter
from dotenv import load_dotenv
import os

load_dotenv()

__author__ = 'Mike Rustell'
__email__ = 'mike@inframatic.ai'
__github__ = 'CivilEngineerUK'


if not st.session_state.get("pdf_id"):
    st.session_state["pdf_id"] = None
    st.session_state["markdown_content"] = None

def main():
    st.title('PDF to Mathpix Markdown Converter')

    st.divider()
    st.write("This app uses the Mathpix API to convert PDFs and download to various formats."
             "It also allows you to view the converted document by clicking the 'Show Markdown' checkbox.")
    st.write("You must have a MATHPIX_APP_ID and MATHPIX_APP_KEY stored in a .env file. You can find these on your Mathpix dashboard: https://accounts.mathpix.com/dashboard")
    st.divider()

    # Create the MathpixConverter object
    converter = MathpixConverter()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("API KEY")
        env_file = st.file_uploader("Upload your .env file", type="env")

        if env_file is not None:
            with open(".env", "wb") as f:
                f.write(env_file.getvalue())
            load_dotenv()

    with col2:
        st.subheader("PDF to Convert")
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    st.divider()

    st.subheader("Options")
    st.write("For information about the options go here: https://docs.mathpix.com/#request-parameters-6")

    section_numbering_option = st.radio(
        'Section Numbering Option',
        ['Preserve section numbering', 'Automatically number sections and subsections',
         'Remove existing numbering for sections and subsections']
    )

    if section_numbering_option == 'Preserve section numbering':
        preserve_section_numbering = True
        auto_number_sections = False
        remove_section_numbering = False
    elif section_numbering_option == 'Automatically number sections and subsections':
        preserve_section_numbering = False
        auto_number_sections = True
        remove_section_numbering = False
    else:  # section_numbering_option == 'Remove existing numbering for sections and subsections'
        preserve_section_numbering = False
        auto_number_sections = False
        remove_section_numbering = True

    enable_tables_fallback = st.checkbox('Enable advanced table processing algorithm', value=True)

    selected_format = st.selectbox(
        'Choose conversion format',
        ('md', 'docx', 'tex.zip', 'html')
    )
    conversion_formats = {selected_format: True}

    st.divider()
    if st.toggle('Show advanced options'):
        # Provide input fields for all the options
        rm_spaces = st.checkbox('Remove extra white spaces from equations', value=True)
        rm_fonts = st.checkbox('Remove font commands from equations')
        idiomatic_eqn_arrays = st.checkbox(
            'Use aligned, gathered, or cases instead of an array environment for a list of equations')
        numbers_default_to_math = st.checkbox('Specify whether numbers are always math')
        math_inline_delimiters = st.text_input('Inline math delimiters', value='\\(,\\)')
        math_display_delimiters = st.text_input('Display math delimiters', value='\\[,\\]')
        enable_spell_check = st.checkbox('Enable predictive mode for English handwriting')
        page_ranges = st.text_input('Page ranges', value='')
    else:
        # Provide input fields for only the most commonly used options
        rm_spaces = True
        rm_fonts = False
        idiomatic_eqn_arrays = False
        numbers_default_to_math = False
        math_inline_delimiters = '\\(,\\)'
        math_display_delimiters = '\\[,\\]'
        enable_spell_check = False
        page_ranges = ''

    st.divider()


    if st.button('Convert'):


        # Create a dictionary for the options
        options = {
            'rm_spaces': rm_spaces,
            'rm_fonts': rm_fonts,
            'idiomatic_eqn_arrays': idiomatic_eqn_arrays,
            'numbers_default_to_math': numbers_default_to_math,
            'math_inline_delimiters': math_inline_delimiters.split(','),
            'math_display_delimiters': math_display_delimiters.split(','),
            'enable_spell_check': enable_spell_check,
            'auto_number_sections': auto_number_sections,
            'remove_section_numbering': remove_section_numbering,
            'preserve_section_numbering': preserve_section_numbering,
            'enable_tables_fallback': enable_tables_fallback,
            'conversion_formats': conversion_formats
        }
        if page_ranges:
            options['page_ranges'] = page_ranges

        # Get the file path of the uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_file_path = temp_file.name

            # Convert the file
            st.session_state["pdf_id"] = converter.send_pdf_to_mathpix(temp_file_path, options=options)
            if st.session_state["pdf_id"]:
                processing_status = converter.wait_for_processing(st.session_state["pdf_id"])

                if processing_status:
                    # Getting Markdown content for viewing
                    response = converter.download_processed_file(st.session_state["pdf_id"], 'md')
                    st.session_state["markdown_content"] = response.content.decode('utf-8')

    if st.session_state["pdf_id"]:
        # Providing download buttons for different formats
        for format in conversion_formats:
            btn_label = f"Download {format}"
            file_name = f"output.{format.lower()}"
            mime_type = "text/plain" if format.lower() == 'md' else "application/octet-stream"

            response = converter.download_processed_file(st.session_state["pdf_id"], format)
            file_content = response.content

            st.divider()


        # Displaying Markdown viewer
        show_markdown = st.checkbox('Show Markdown', value=True)
        if st.session_state["markdown_content"] and show_markdown:
            st.markdown('### Converted Markdown Content')
            download_btn = st.download_button(
                label=btn_label,
                data=file_content,
                file_name=file_name,
                mime=mime_type
            )
            st.divider()
            st.markdown(st.session_state["markdown_content"], unsafe_allow_html=True)

if __name__ == "__main__":
    main()