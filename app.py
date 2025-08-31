import streamlit as st
import pandas as pd
import io
import re
from typing import Dict, List, Tuple, Optional, Set

def main():
    st.set_page_config(
        page_title="Brightspace-Cisco Grade Updater",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Brightspace-Cisco Grade Updater")
    st.markdown("Upload your Brightspace Gradebook Export CSV and Cisco Networking Academy CSV to update grades automatically.")
    
    # Initialize session state
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    if 'updated_df' not in st.session_state:
        st.session_state.updated_df = None
    if 'update_summary' not in st.session_state:
        st.session_state.update_summary = None
    
    # Create two columns for file uploads
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Brightspace Gradebook CSV")
        brightspace_file = st.file_uploader(
            "Choose Brightspace CSV file",
            type=['csv'],
            key="brightspace",
            help="Upload your Brightspace gradebook export file"
        )
        
    with col2:
        st.subheader("🌐 Cisco Networking Academy CSV")
        cisco_file = st.file_uploader(
            "Choose Cisco CSV file",
            type=['csv'],
            key="cisco",
            help="Upload your Cisco Networking Academy export file"
        )
    
    if brightspace_file and cisco_file:
        try:
            with st.spinner("Loading CSV files..."):
                # Load the CSV files
                brightspace_df = load_brightspace_csv(brightspace_file)
                cisco_df = load_cisco_csv(cisco_file)
            
            # Display file information
            st.success("✅ Files loaded successfully!")
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"Brightspace: {len(brightspace_df)} students")
            with col2:
                st.info(f"Cisco: {len(cisco_df)} students")
            
            # Show preview of data
            show_preview = st.checkbox("Show data preview", key="preview_checkbox")
            if show_preview:
                st.subheader("Brightspace Data Preview")
                preview_cols = ['Email', 'Last Name', 'First Name']
                available_cols = [col for col in preview_cols if col in brightspace_df.columns]
                if available_cols:
                    st.dataframe(brightspace_df[available_cols].head())
                else:
                    st.warning("Preview columns not found in Brightspace data")
                
                st.subheader("Cisco Data Preview")
                cisco_preview_cols = ['EMAIL', 'NAME']
                cisco_available_cols = [col for col in cisco_preview_cols if col in cisco_df.columns]
                if cisco_available_cols:
                    st.dataframe(cisco_df[cisco_available_cols].head())
                else:
                    st.warning("Preview columns not found in Cisco data")
            
            # Assignment Selection and Options
            st.subheader("📝 Assignment Selection")
            
            # Extract available assignments from Cisco data
            available_assignments = extract_available_assignments(cisco_df)
            
            if available_assignments:
                st.markdown("**Select which assignments to transfer from Cisco NetAcad to Brightspace:**")
                
                # Show assignment preview
                show_assignment_preview = st.checkbox("Show assignment details", key="assignment_preview")
                if show_assignment_preview:
                    assignment_preview = get_assignment_data_preview(cisco_df, available_assignments)
                    if not assignment_preview.empty:
                        st.dataframe(assignment_preview, use_container_width=True)
                
                # Create columns for assignment selection
                col1, col2 = st.columns(2)
                
                # Initialize session state for selected assignments if not exists
                if 'selected_assignments' not in st.session_state:
                    st.session_state.selected_assignments = set(available_assignments)
                
                with col1:
                    st.markdown("**Select Assignments:**")
                    
                    # Select All / Deselect All buttons
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("Select All", key="select_all"):
                            st.session_state.selected_assignments = set(available_assignments)
                            st.rerun()
                    with col_b:
                        if st.button("Deselect All", key="deselect_all"):
                            st.session_state.selected_assignments = set()
                            st.rerun()
                    
                    # Assignment checkboxes
                    selected_assignments = set()
                    for assignment in available_assignments:
                        is_selected = st.checkbox(
                            assignment,
                            value=assignment in st.session_state.selected_assignments,
                            key=f"assign_{assignment}"
                        )
                        if is_selected:
                            selected_assignments.add(assignment)
                    
                    # Update session state
                    st.session_state.selected_assignments = selected_assignments
                
                with col2:
                    st.markdown("**Grade Transfer Options:**")
                    
                    # Toggle for setting blanks to zero
                    set_blanks_to_zero = st.checkbox(
                        "Set blank/empty grades to zero",
                        value=False,
                        key="set_blanks_zero",
                        help="When enabled, students with blank grades in Cisco NetAcad will receive a grade of 0 in Brightspace. When disabled, blank grades will remain empty."
                    )
                    
                    # Show selected assignments count
                    st.info(f"**Selected assignments:** {len(st.session_state.selected_assignments)}")
                    
                    if st.session_state.selected_assignments:
                        st.success("✅ Ready to transfer grades")
                    else:
                        st.warning("⚠️ No assignments selected")
                
                # Store options in session state
                if 'set_blanks_to_zero' not in st.session_state:
                    st.session_state.set_blanks_to_zero = set_blanks_to_zero
                else:
                    st.session_state.set_blanks_to_zero = set_blanks_to_zero
                
            else:
                st.warning("No gradeable assignments found in Cisco CSV file.")
                st.session_state.selected_assignments = set()
            
            # Process and update grades
            if st.button("🔄 Update Grades", type="primary", key="update_button", disabled=not bool(st.session_state.selected_assignments)):
                with st.spinner("Processing grades..."):
                    updated_df, update_summary = update_brightspace_grades(
                        brightspace_df,
                        cisco_df,
                        st.session_state.selected_assignments,
                        st.session_state.set_blanks_to_zero
                    )
                    
                    # Store in session state
                    st.session_state.updated_df = updated_df
                    st.session_state.update_summary = update_summary
                    st.session_state.processing_complete = True
            
            # Show results if processing is complete
            if st.session_state.processing_complete and st.session_state.updated_df is not None:
                # Display update summary
                st.subheader("📈 Update Summary")
                
                # First row of metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Students Matched", st.session_state.update_summary.get('Students Matched', 0))
                with col2:
                    st.metric("Grades Updated", st.session_state.update_summary.get('Grades Updated', 0))
                with col3:
                    st.metric("Students Not Found", st.session_state.update_summary.get('Students Not Found', 0))
                
                # Second row of metrics
                col4, col5, col6 = st.columns(3)
                with col4:
                    st.metric("Selected Assignments", st.session_state.update_summary.get('Selected Assignments', 0))
                with col5:
                    st.metric("Mapped Assignments", st.session_state.update_summary.get('Mapped Assignments', 0))
                with col6:
                    blank_grades = st.session_state.update_summary.get('Blank Grades Processed', 0)
                    st.metric("Blank Grades Set to Zero", blank_grades)
                
                # Show updated data preview
                show_updated_preview = st.checkbox("Show updated data preview", key="updated_preview_checkbox")
                if show_updated_preview:
                    st.dataframe(st.session_state.updated_df.head())
                
                # Download button
                csv_buffer = io.StringIO()
                st.session_state.updated_df.to_csv(csv_buffer, index=False)
                csv_data = csv_buffer.getvalue()
                
                st.download_button(
                    label="📥 Download Updated Brightspace CSV",
                    data=csv_data,
                    file_name="updated_brightspace_grades.csv",
                    mime="text/csv",
                    key="download_button"
                )
                
        except Exception as e:
            st.error(f"❌ Error processing files: {str(e)}")
            with st.expander("Show detailed error information"):
                st.exception(e)

def load_brightspace_csv(file) -> pd.DataFrame:
    """Load and clean Brightspace CSV file."""
    try:
        # Try reading with different encodings
        encodings = ['utf-8', 'utf-8-sig', 'iso-8859-1', 'cp1252']
        df = None
        
        for encoding in encodings:
            try:
                file.seek(0)  # Reset file pointer
                df = pd.read_csv(file, encoding=encoding, low_memory=False)
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        if df is None:
            # Final attempt without specifying encoding
            file.seek(0)
            df = pd.read_csv(file, low_memory=False)
        
        # Remove rows that are completely empty or contain only metadata
        df = df.dropna(how='all')
        
        # Clean column names (remove extra whitespace)
        df.columns = df.columns.str.strip()
        
        # Ensure we have the required columns
        required_columns = ['Email', 'Last Name', 'First Name']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            available_columns = list(df.columns[:10])  # Show first 10 columns
            raise ValueError(f"Required columns {missing_columns} not found in Brightspace CSV. "
                           f"Available columns: {available_columns}")
        
        return df
        
    except Exception as e:
        raise ValueError(f"Error loading Brightspace CSV: {str(e)}")

def load_cisco_csv(file) -> pd.DataFrame:
    """Load and clean Cisco CSV file."""
    try:
        # Try reading with different encodings
        encodings = ['utf-8', 'utf-8-sig', 'iso-8859-1', 'cp1252']
        df = None
        
        for encoding in encodings:
            try:
                file.seek(0)  # Reset file pointer
                df = pd.read_csv(file, encoding=encoding, low_memory=False)
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        if df is None:
            # Final attempt without specifying encoding
            file.seek(0)
            df = pd.read_csv(file, low_memory=False)
        
        # Clean column names (remove extra whitespace)
        df.columns = df.columns.str.strip()
        
        # Check for required columns
        required_columns = ['NAME', 'EMAIL']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            available_columns = list(df.columns[:10])  # Show first 10 columns
            raise ValueError(f"Required columns {missing_columns} not found in Cisco CSV. "
                           f"Available columns: {available_columns}")
        
        # Remove the "Point Possible" row and any empty rows
        df = df[df['NAME'].notna()]
        df = df[df['NAME'] != 'Point Possible']
        df = df.dropna(subset=['NAME', 'EMAIL'])
        
        # Clean up email addresses (remove any whitespace)
        df['EMAIL'] = df['EMAIL'].astype(str).str.strip().str.lower()
        
        return df
        
    except Exception as e:
        raise ValueError(f"Error loading Cisco CSV: {str(e)}")

def extract_available_assignments(cisco_df: pd.DataFrame) -> List[str]:
    """Extract available assignment columns from Cisco CSV."""
    try:
        # Define columns that are not assignments (metadata columns)
        non_assignment_columns = {
            'NAME', 'EMAIL', 'Final Exam Submitted', 'Survey Submitted',
            'Completion', 'Final Exam Score', 'Assessment( Average )',
            'Class Grade %', 'Networking Essentials: Course Final Exam'
        }
        
        # Get all columns and filter out non-assignment columns
        all_columns = list(cisco_df.columns)
        assignment_columns = []
        
        for col in all_columns:
            # Skip non-assignment columns
            if col in non_assignment_columns:
                continue
            
            # Look for checkpoint exams and other gradeable assignments
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['checkpoint', 'exam', 'quiz', 'test', 'activity']):
                assignment_columns.append(col)
        
        return assignment_columns
        
    except Exception as e:
        st.error(f"Error extracting assignments: {str(e)}")
        return []

def get_assignment_data_preview(cisco_df: pd.DataFrame, assignment_cols: List[str]) -> pd.DataFrame:
    """Get a preview of assignment data including point values and completion stats."""
    try:
        preview_data = []
        
        # Find the "Point Possible" row to get max points
        point_possible_row = cisco_df[cisco_df['NAME'] == 'Point Possible']
        
        for col in assignment_cols:
            # Get max points if available
            max_points = ""
            if not point_possible_row.empty and col in point_possible_row.columns:
                max_points_val = point_possible_row[col].iloc[0]
                if pd.notna(max_points_val) and str(max_points_val).strip():
                    max_points = f"/{max_points_val}"
            
            # Count students with grades for this assignment
            student_data = cisco_df[cisco_df['NAME'] != 'Point Possible']
            total_students = len(student_data)
            students_with_grades = len(student_data[student_data[col].notna() & (student_data[col] != '') & (student_data[col] != ' ')])
            
            preview_data.append({
                'Assignment': col,
                'Max Points': max_points,
                'Students with Grades': f"{students_with_grades}/{total_students}",
                'Completion %': f"{(students_with_grades/total_students*100):.1f}%" if total_students > 0 else "0%"
            })
        
        return pd.DataFrame(preview_data)
        
    except Exception as e:
        st.error(f"Error creating assignment preview: {str(e)}")
        return pd.DataFrame()

def create_column_mapping() -> Dict[str, str]:
    """Create mapping between Cisco and Brightspace column names."""
    mapping = {
        'Checkpoint Exam: Build a Small Network': 'Checkpoint Exam - Build a Small Network Points Grade',
        'Checkpoint Exam: Network Access': 'Checkpoint Exam - Network Access Points Grade',
        'Checkpoint Exam: The Internet Protocol': 'Checkpoint Exam - Internet Protocol Points Grade',
        'Checkpoint Exam: Communication Between Networks': 'Checkpoint Exam: Communication Between Networks Points Grade',
        'Checkpoint Exam: Protocols for Specific Tasks': 'Checkpoint Exam – Protocols for Specific Tasks(1) Points Grade',
        'Checkpoint Exam: Characteristics of Network Design': 'Checkpoint Exam – Characteristics of Network Design Points Grade',
        'Checkpoint Exam: Network Addressing': 'Checkpoint Exam – Network Addressing Points Grade',
        'Checkpoint Exam: ARP, DNS, DHCP and the Transport Layer': 'Checkpoint Exam – ARP DNS DHCP and the Transport Layer Points Grade',
        'Checkpoint Exam: Configure Cisco Devices': 'Checkpoint Exam – Configure Cisco Devices Points Grade',
        'Checkpoint Exam: Physical, Data Link, and Network Layers': 'Checkpoint Exam – Physical Data Link and Network Layers Points Grade',
        'Checkpoint Exam: IP Addressing': 'Checkpoint Exam – IP Addressing Points Grade',
        'Checkpoint Exam: Cisco Devices and Troubleshooting Network Issues': 'Checkpoint Exam – Cisco Devices Points Grade'
    }
    return mapping

def find_brightspace_column(brightspace_columns: List[str], search_term: str) -> Optional[str]:
    """Find the best matching Brightspace column for a given search term."""
    # First try exact match
    for col in brightspace_columns:
        if search_term in col:
            return col
    
    # Try partial matches with key terms
    key_terms = search_term.lower().split()
    for col in brightspace_columns:
        col_lower = col.lower()
        if any(term in col_lower for term in key_terms):
            return col
    
    return None

def create_dynamic_column_mapping(selected_assignments: Set[str], brightspace_columns: List[str]) -> Dict[str, str]:
    """Create dynamic mapping between selected Cisco assignments and Brightspace column names."""
    mapping = {}
    
    # Static mapping for known assignments
    static_mapping = {
        'Checkpoint Exam: Build a Small Network': 'Checkpoint Exam - Build a Small Network Points Grade',
        'Checkpoint Exam: Network Access': 'Checkpoint Exam - Network Access Points Grade',
        'Checkpoint Exam: The Internet Protocol': 'Checkpoint Exam - Internet Protocol Points Grade',
        'Checkpoint Exam: Communication Between Networks': 'Checkpoint Exam: Communication Between Networks Points Grade',
        'Checkpoint Exam: Protocols for Specific Tasks': 'Checkpoint Exam – Protocols for Specific Tasks(1) Points Grade',
        'Checkpoint Exam: Characteristics of Network Design': 'Checkpoint Exam – Characteristics of Network Design Points Grade',
        'Checkpoint Exam: Network Addressing': 'Checkpoint Exam – Network Addressing Points Grade',
        'Checkpoint Exam: ARP, DNS, DHCP and the Transport Layer': 'Checkpoint Exam – ARP DNS DHCP and the Transport Layer Points Grade',
        'Checkpoint Exam: Configure Cisco Devices': 'Checkpoint Exam – Configure Cisco Devices Points Grade',
        'Checkpoint Exam: Physical, Data Link, and Network Layers': 'Checkpoint Exam – Physical Data Link and Network Layers Points Grade',
        'Checkpoint Exam: IP Addressing': 'Checkpoint Exam – IP Addressing Points Grade',
        'Checkpoint Exam: Cisco Devices and Troubleshooting Network Issues': 'Checkpoint Exam – Cisco Devices Points Grade'
    }
    
    # Only include selected assignments
    for cisco_col in selected_assignments:
        if cisco_col in static_mapping:
            # Use static mapping if available
            brightspace_col = find_brightspace_column(brightspace_columns, static_mapping[cisco_col])
            if brightspace_col:
                mapping[cisco_col] = brightspace_col
        else:
            # Try to find matching column for assignments not in static mapping
            brightspace_col = find_brightspace_column(brightspace_columns, cisco_col)
            if brightspace_col:
                mapping[cisco_col] = brightspace_col
    
    return mapping

def update_brightspace_grades(
    brightspace_df: pd.DataFrame,
    cisco_df: pd.DataFrame,
    selected_assignments: Set[str],
    set_blanks_to_zero: bool
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """Update Brightspace grades with Cisco data based on selected assignments."""
    updated_df = brightspace_df.copy()
    cisco_df_copy = cisco_df.copy()
    
    try:
        # Normalize email addresses for matching
        updated_df['Email_normalized'] = updated_df['Email'].astype(str).str.strip().str.lower()
        cisco_df_copy['EMAIL_normalized'] = cisco_df_copy['EMAIL'].astype(str).str.strip().str.lower()
        
        # Create dynamic column mapping based on selected assignments
        brightspace_columns = list(updated_df.columns)
        column_mapping = create_dynamic_column_mapping(selected_assignments, brightspace_columns)
        
        # Track updates
        update_summary = {
            'Students Matched': 0,
            'Grades Updated': 0,
            'Students Not Found': 0,
            'Selected Assignments': len(selected_assignments),
            'Mapped Assignments': len(column_mapping),
            'Blank Grades Processed': 0
        }
        
        # Process each student in Cisco data
        for idx, cisco_row in cisco_df_copy.iterrows():
            try:
                cisco_email = cisco_row['EMAIL_normalized']
                
                # Skip if email is empty or null
                if pd.isna(cisco_email) or cisco_email == 'nan' or cisco_email.strip() == '':
                    continue
                
                # Find matching student in Brightspace
                brightspace_match = updated_df[updated_df['Email_normalized'] == cisco_email]
                
                if brightspace_match.empty:
                    update_summary['Students Not Found'] += 1
                    continue
                
                update_summary['Students Matched'] += 1
                brightspace_idx = brightspace_match.index[0]
                
                # Update grades for each mapped column
                for cisco_col, brightspace_col in column_mapping.items():
                    try:
                        if cisco_col in cisco_row:
                            cisco_grade = cisco_row[cisco_col]
                            
                            # Check if grade is blank/empty
                            is_blank = (pd.isna(cisco_grade) or
                                       str(cisco_grade).strip() == '' or
                                       str(cisco_grade).strip() == ' ')
                            
                            if not is_blank:
                                # Grade has a value - process normally
                                try:
                                    grade_value = float(cisco_grade)
                                except (ValueError, TypeError):
                                    grade_value = str(cisco_grade).strip()
                                
                                updated_df.at[brightspace_idx, brightspace_col] = grade_value
                                update_summary['Grades Updated'] += 1
                                
                            elif set_blanks_to_zero:
                                # Grade is blank and user wants to set blanks to zero
                                updated_df.at[brightspace_idx, brightspace_col] = 0
                                update_summary['Grades Updated'] += 1
                                update_summary['Blank Grades Processed'] += 1
                            
                            # If grade is blank and user doesn't want to set to zero, leave unchanged
                                
                    except Exception as col_error:
                        # Continue processing other columns if one fails
                        st.warning(f"Error updating column {cisco_col} for student {cisco_email}: {str(col_error)}")
                        continue
                        
            except Exception as row_error:
                # Continue processing other students if one fails
                st.warning(f"Error processing student at row {idx}: {str(row_error)}")
                continue
        
        # Remove the temporary normalized email column
        if 'Email_normalized' in updated_df.columns:
            updated_df = updated_df.drop('Email_normalized', axis=1)
        
        return updated_df, update_summary
        
    except Exception as e:
        st.error(f"Critical error in grade update process: {str(e)}")
        # Return original dataframe if update fails
        return brightspace_df, {
            'Students Matched': 0,
            'Grades Updated': 0,
            'Students Not Found': 0,
            'Selected Assignments': 0,
            'Mapped Assignments': 0,
            'Blank Grades Processed': 0
        }

if __name__ == "__main__":
    main()