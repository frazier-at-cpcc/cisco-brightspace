# Brightspace-Cisco Grade Updater

A Streamlit application that updates Brightspace gradebook exports with grades from Cisco Networking Academy CSV files.

## Features

- Upload Brightspace Gradebook Export CSV files
- Upload Cisco Networking Academy CSV files
- Automatically match students by email address
- Update checkpoint exam grades from Cisco to Brightspace
- Download updated Brightspace CSV file
- Robust error handling and data validation
- Support for multiple CSV encodings

## Usage

1. Export your gradebook from Brightspace as a CSV file
2. Export your course data from Cisco Networking Academy as a CSV file
3. Upload both files to the application
4. Click "Update Grades" to process the data
5. Download the updated Brightspace CSV file

## Supported Grade Types

The application maps the following Cisco checkpoint exams to Brightspace:

- Build a Small Network
- Network Access
- Internet Protocol
- Communication Between Networks
- Protocols for Specific Tasks
- Characteristics of Network Design
- Network Addressing
- ARP, DNS, DHCP and the Transport Layer
- Configure Cisco Devices
- Physical, Data Link, and Network Layers
- IP Addressing
- Cisco Devices and Troubleshooting

## Requirements

- Python 3.7+
- Streamlit
- Pandas

## Installation

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deployment

This application is designed to work with Streamlit Community Cloud. Simply connect your GitHub repository and deploy.

## File Format Requirements

### Brightspace CSV
- Must contain columns: Email, Last Name, First Name
- Should contain checkpoint exam grade columns

### Cisco CSV
- Must contain columns: NAME, EMAIL
- Should contain checkpoint exam score columns
- The first data row should not be "Point Possible"

## Error Handling

The application handles various common issues:
- Different CSV encodings (UTF-8, UTF-8-BOM, ISO-8859-1, CP1252)
- Missing or malformed data
- Column name variations
- Email address formatting differences

## Support

If you encounter issues, check that your CSV files match the required format and contain the necessary columns.