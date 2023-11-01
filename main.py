import streamlit as st
import tempfile
from mathpix import MathpixConverter
from dotenv import load_dotenv
import os

load_dotenv()

__author__ = 'Mike Rustell'
__email__ = 'mike@inframatic.ai'
__github__ = 'CivilEngineerUK'


def main():
    st.title('PDF to Mathpix Markdown Converter')

    st.write("See here for more explanation of the options: https://docs.mathpix.com/#request-parameters-6")

    tabs = st.tabs(["Send to Mathpix", "Markdown Viewer and Download"])
    send_tab, view_tab = tabs

    with send_tab:
        st.write("You must provide MATHPIX_APP_ID and MATHPIX_APP_KEY in a .env file or manually enter them below.")

        auth_method = st.radio("Choose an authentication method",
                               ["Provide credentials via .env file", "Enter credentials manually"])

        if auth_method == "Provide credentials via .env file":
            env_file = st.file_uploader("Upload your .env file", type="env")

            if env_file is not None:
                with open(".env", "wb") as f:
                    f.write(env_file.getvalue())
                load_dotenv()

        elif auth_method == "Enter credentials manually":
            st.write("Please enter your Mathpix credentials:")
            app_id = st.text_input("App ID")
            app_key = st.text_input("App Key", type="password")

            if app_id and app_key:
                os.environ["MATHPIX_APP_ID"] = app_id
                os.environ["MATHPIX_APP_KEY"] = app_key

        st.divider()

        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

        if uploaded_file is not None:
            st.write('File successfully uploaded.')

        st.divider()

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

        st.divider()
        advanced = st.checkbox("Advanced Options", value=False, key="advanced_options")
        if advanced:
            st.write("Select advanced options")
            # Provide input fields for all the options
            rm_spaces = st.checkbox('Remove extra white spaces from equations', value=True)
            rm_fonts = st.checkbox('Remove font commands from equations')
            idiomatic_eqn_arrays = st.checkbox(
                'Use aligned, gathered, or cases instead of an array environment for a list of equations')
            numbers_default_to_math = st.checkbox('Specify whether numbers are always math')
            math_inline_delimiters = st.text_input('Inline math delimiters', value='\\(,\\)')
            math_display_delimiters = st.text_input('Display math delimiters', value='\\[,\\]')
            page_ranges = st.text_input('Page ranges', value='')
            enable_spell_check = st.checkbox('Enable predictive mode for English handwriting')
        else:
            # Provide input fields for all the options
            rm_spaces = True
            rm_fonts = False
            idiomatic_eqn_arrays = False
            numbers_default_to_math = False
            math_inline_delimiters ='\\(,\\)'
            math_display_delimiters = '\\[,\\]'
            page_ranges = ''
            enable_spell_check = False

        st.divider()

        conversion_formats = st.multiselect(
            'Choose conversion formats',
            ['md', 'docx', 'tex.zip', 'html'],
            default=['md']
        )

        if st.button('Send to Mathpix'):
            pdf_id = st.session_state.get("pdf_id", None)
            if pdf_id is None:
                with st.spinner('Processing...'):
                    # Create the MathpixConverter object
                    converter = MathpixConverter()

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
                        'conversion_formats': {format: True for format in conversion_formats}
                    }
                    if page_ranges:
                        options['page_ranges'] = page_ranges

                        # Get the file path of the uploaded file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                        temp_file.write(uploaded_file.getvalue())
                        temp_file_path = temp_file.name

                        # Convert the file
                        pdf_id = converter.send_pdf_to_mathpix(temp_file_path, options=options)
                        st.session_state["pdf_id"] = pdf_id

                        # Use a different key for the spinner to avoid infinite spinning
                        with st.spinner('Waiting for processing to complete...'):
                            processing_status = converter.wait_for_processing(st.session_state["pdf_id"])
                            if processing_status == 'completed':
                                st.success('Processing complete')
                            elif processing_status == 'error':
                                st.error('Error: Unable to process PDF')
                            else:
                                st.experimental_rerun()  # Rerun the script to check the processing status again


                        # Now you can safely access st.session_state["pdf_id"] without getting a KeyError
                        processing_status = converter.wait_for_processing(st.session_state["pdf_id"])
                        st.session_state[
                            "processing_status"] = processing_status  # Store the processing status in st.session_state

                        processing_status = converter.wait_for_processing(st.session_state["pdf_id"])
                        st.session_state[
                            "processing_status"] = processing_status  # Store the processing status in st.session_state

                        if processing_status == 'completed':
                            with view_tab:
                                if st.session_state.get("pdf_id"):
                                    # Providing download buttons for different formats
                                    for format in conversion_formats:
                                        btn_label = f"Download {format}"
                                        file_name = f"output.{format.lower()}"
                                        mime_type = "text/plain" if format.lower() == 'md' else "application/octet-stream"

                                        response = converter.download_processed_file(st.session_state["pdf_id"], format)
                                        file_content = response.content

                                        download_btn = st.download_button(
                                            label=btn_label,
                                            data=file_content,
                                            file_name=file_name,
                                            mime=mime_type
                                        )

                                    # Displaying Markdown viewer
                                    if st.session_state.get("markdown_content"):
                                        st.markdown('### Converted Markdown Content')
                                        st.markdown(st.session_state["markdown_content"], unsafe_allow_html=True)
                                else:
                                    st.warning('Please convert a file first in the "Send to Mathpix" tab.')


if __name__ == "__main__":
    main()