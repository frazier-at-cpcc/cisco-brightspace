import streamlit as st
import pandas as pd
import io
import re
from typing import Dict, List, Tuple, Optional

def main():
    st.set_page_config(
        page_title="Brightspace-Cisco Grade Updater",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Brightspace-Cisco Grade Updater")
    st.markdown("Upload your Brightspace Gradebook Export CSV and Cisco Networking Academy CSV to update grades automatically.")
    
    # Create two columns for file uploads
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Brightspace Gradebook CSV")
        brightspace_file = st.file_uploader(
            "Choose Brightspace CSV file",
            type=['csv'],
            key="brightspace"
        )
        
    with col2:
        st.subheader("🌐 Cisco Networking Academy CSV")
        cisco_file = st.file_uploader(
            "Choose Cisco CSV file",
            type=['csv'],
            key="cisco"
        )
    
    if brightspace_file and cisco_file:
        try:
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
            if st.checkbox("Show data preview"):
                st.subheader("Brightspace Data Preview")
                st.dataframe(brightspace_df[['Email', 'Last Name', 'First Name']].head())
                
                st.subheader("Cisco Data Preview")
                st.dataframe(cisco_df[['EMAIL', 'NAME']].head())
            
            # Process and update grades
            if st.button("🔄 Update Grades", type="primary"):
                updated_df, update_summary = update_brightspace_grades(brightspace_df, cisco_df)
                
                # Display update summary
                st.subheader("📈 Update Summary")
                for key, value in update_summary.items():
                    st.metric(key, value)
                
                # Show updated data preview
                if st.checkbox("Show updated data preview"):
                    st.dataframe(updated_df.head())
                
                # Download button
                csv_buffer = io.StringIO()
                updated_df.to_csv(csv_buffer, index=False)
                csv_data = csv_buffer.getvalue()
                
                st.download_button(
                    label="📥 Download Updated Brightspace CSV",
                    data=csv_data,
                    file_name="updated_brightspace_grades.csv",
                    mime="text/csv"
                )
                
        except Exception as e:
            st.error(f"❌ Error processing files: {str(e)}")
            st.exception(e)

def load_brightspace_csv(file) -> pd.DataFrame:
    """Load and clean Brightspace CSV file."""
    df = pd.read_csv(file)
    
    # Remove rows that are completely empty or contain only metadata
    df = df.dropna(how='all')
    
    # Ensure we have the required columns
    required_columns = ['Email', 'Last Name', 'First Name']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in Brightspace CSV")
    
    return df

def load_cisco_csv(file) -> pd.DataFrame:
    """Load and clean Cisco CSV file."""
    df = pd.read_csv(file)
    
    # Remove the "Point Possible" row and any empty rows
    df = df[df['NAME'] != 'Point Possible']
    df = df.dropna(subset=['NAME', 'EMAIL'])
    
    # Clean up email addresses (remove any whitespace)
    df['EMAIL'] = df['EMAIL'].str.strip().str.lower()
    
    return df

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

def update_brightspace_grades(brightspace_df: pd.DataFrame, cisco_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """Update Brightspace grades with Cisco data."""
    updated_df = brightspace_df.copy()
    
    # Normalize email addresses for matching
    updated_df['Email_normalized'] = updated_df['Email'].str.strip().str.lower()
    cisco_df['EMAIL_normalized'] = cisco_df['EMAIL'].str.strip().str.lower()
    
    # Create column mapping
    column_mapping = create_column_mapping()
    
    # Track updates
    update_summary = {
        'Students Matched': 0,
        'Grades Updated': 0,
        'Students Not Found': 0
    }
    
    # Get list of Brightspace columns for matching
    brightspace_columns = list(updated_df.columns)
    
    # Process each student in Cisco data
    for _, cisco_row in cisco_df.iterrows():
        cisco_email = cisco_row['EMAIL_normalized']
        
        # Find matching student in Brightspace
        brightspace_match = updated_df[updated_df['Email_normalized'] == cisco_email]
        
        if brightspace_match.empty:
            update_summary['Students Not Found'] += 1
            continue
        
        update_summary['Students Matched'] += 1
        brightspace_idx = brightspace_match.index[0]
        
        # Update grades for each mapped column
        for cisco_col, brightspace_col_pattern in column_mapping.items():
            if cisco_col in cisco_row and pd.notna(cisco_row[cisco_col]):
                # Find the actual Brightspace column
                brightspace_col = find_brightspace_column(brightspace_columns, brightspace_col_pattern)
                
                if brightspace_col:
                    # Update the grade
                    updated_df.at[brightspace_idx, brightspace_col] = cisco_row[cisco_col]
                    update_summary['Grades Updated'] += 1
    
    # Remove the temporary normalized email column
    updated_df = updated_df.drop('Email_normalized', axis=1)
    
    return updated_df, update_summary

if __name__ == "__main__":
    main()