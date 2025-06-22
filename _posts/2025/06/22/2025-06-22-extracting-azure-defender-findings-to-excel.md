---
header:
    image: /assets/images/hd_azure_defender_excel.jpg
title: Extracting Azure Defender for Cloud Findings to Excel - A Developer's Detective Story
date: 2025-06-22
tags:
    - Azure
    - Security
    - DevOps
    - Excel
permalink: /blogs/tech/en/extracting-azure-defender-findings-to-excel
layout: single
category: tech
---
> The best way to find out if you can trust somebody is to trust them. - Ernest Hemingway

# Extracting Azure Defender for Cloud Findings to Excel: A Developer's Detective Story

*By Tech Detective*

Picture this: It's Monday morning, and your security team needs a comprehensive Excel report of all vulnerability findings from Azure Defender for Cloud. You confidently navigate to the Azure portal, expecting to find a nice "Export to Excel" button. But wait... there isn't one! Sound familiar? Today, I'm sharing the detective work that led me to crack this puzzle using browser developer tools and some API magic.

## The Mystery: Missing Export Functionality

Recently, I encountered a scenario that many cloud security engineers will recognize. Azure Defender for Cloud had identified numerous vulnerabilities in our container registry, including critical CVEs like CVE-2022-23307. The assessment page showed hundreds of findings, but Azure portal offered no way to export this data to Excel for further analysis or reporting.

This is classic Azure behavior - powerful security insights trapped behind a beautiful UI with limited export capabilities. But where there's a will (and browser developer tools), there's a way!

## The Investigation: Browser Developer Tools to the Rescue

The solution turned out to be surprisingly elegant, requiring some digital detective work:

### Step 1: Open the Crime Scene
1. **Navigate to Azure Defender for Cloud**:
   - Go to your Azure portal
   - Find the problematic assessment (e.g., "Container images in Azure registry should have vulnerability findings resolved")
   - Open the detailed findings page

### Step 2: Deploy Your Detective Tools
1. **Open Chrome Developer Tools** (F12 or right-click → Inspect)
2. **Switch to the Network tab**
3. **Clear the network log** to start fresh
4. **Refresh the page** to capture all API calls

### Step 3: Hunt for the API Treasure
1. **Search for your target**: In the Network tab's filter box, search for specific CVE numbers like "CVE-2022-23307"
2. **Locate the API call**: Look for requests to endpoints containing your search terms
3. **Identify the batch API**: You'll discover the magic endpoint:
   ```
   https://management.azure.com/batch?api-version=2020-06-01
   ```

### Step 4: Extract the Evidence
1. **Click on the API request** in the Network tab
2. **Navigate to the "Response" tab**
3. **Copy the JSON response** - this contains all your vulnerability data
4. **Save to a file** (e.g., `azure_defender_findings.json`)

## The Solution: From JSON to Excel Magic

Once you have the JSON data, converting it to Excel becomes straightforward. Here's a Python script to automate the process:

```python
import json
import pandas as pd
from datetime import datetime
import os
import glob
from typing import Dict, List, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AzureVulnerabilityExcelConverter:
    """Azure vulnerability data Excel converter"""
    
    def __init__(self, json_directory: str):
        self.json_directory = json_directory
        self.vulnerabilities = []
        
    def load_json_files(self) -> bool:
        """Load all JSON files from directory"""
        try:
            json_files = glob.glob(os.path.join(self.json_directory, "*.json"))
            if not json_files:
                logger.error(f"No JSON files found in directory: {self.json_directory}")
                return False
            
            logger.info(f"Found {len(json_files)} JSON files to process")
            
            for json_file in json_files:
                logger.info(f"Loading JSON file: {json_file}")
                try:
                    with open(json_file, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                        self.parse_single_file_data(data)
                except Exception as e:
                    logger.error(f"Error loading file {json_file}: {e}")
                    continue
            
            logger.info(f"Successfully loaded {len(self.vulnerabilities)} vulnerability records")
            return True
            
        except Exception as e:
            logger.error(f"Error loading JSON files: {e}")
            return False
    
    def parse_single_file_data(self, data: dict) -> None:
        """Parse vulnerability data from a single JSON file"""
        try:
            # Get response data
            if 'responses' not in data or not data['responses']:
                logger.warning("No responses field found in JSON data")
                return
            
            response = data['responses'][0]
            if 'content' not in response or 'data' not in response['content']:
                logger.warning("Invalid JSON data structure")
                return
            
            data_content = response['content']['data']
            columns = [col['name'] for col in data_content['columns']]
            rows = data_content['rows']
            
            logger.info(f"Found {len(columns)} columns, {len(rows)} rows of data")
            
            # Convert row data to dictionary list
            for row in rows:
                vulnerability = {}
                for i, value in enumerate(row):
                    if i < len(columns):
                        vulnerability[columns[i]] = value
                self.vulnerabilities.append(vulnerability)
            
        except Exception as e:
            logger.error(f"Error parsing vulnerability data: {e}")
    
    def extract_additional_data(self, vuln: Dict) -> Dict:
        """Extract detailed information from additionalData"""
        additional_info = {}
        
        try:
            additional_data = vuln.get('additionalData', {})
            if isinstance(additional_data, dict):
                # Extract vulnerability details
                vuln_details = additional_data.get('vulnerabilityDetails', {})
                if isinstance(vuln_details, dict):
                    additional_info['cveId'] = vuln_details.get('cveId', '')
                    additional_info['publishedDate'] = vuln_details.get('publishedDate', '')
                    
                    # CVSS score
                    cvss = vuln_details.get('cvss', {})
                    if isinstance(cvss, dict) and '3.0' in cvss:
                        cvss_30 = cvss['3.0']
                        additional_info['cvssScore'] = cvss_30.get('base', '')
                        additional_info['cvssVector'] = cvss_30.get('cvssVectorString', '')
                    
                    # CPE information (masked for privacy)
                    cpe = vuln_details.get('cpe', {})
                    if isinstance(cpe, dict):
                        additional_info['vendor'] = cpe.get('vendor', '')
                        additional_info['product'] = cpe.get('product', '')
                        additional_info['version'] = cpe.get('version', '')
                
                # Extract software details
                software_details = additional_data.get('softwareDetails', {})
                if isinstance(software_details, dict):
                    additional_info['packageName'] = software_details.get('packageName', '')
                    additional_info['packageVersion'] = software_details.get('version', '')
                    additional_info['fixStatus'] = software_details.get('fixStatus', '')
                    additional_info['fixedVersion'] = software_details.get('fixedVersion', '')
        
        except Exception as e:
            logger.error(f"Error extracting additional data: {e}")
        
        return additional_info
    
    def generate_excel_report(self, output_file: str) -> bool:
        """Generate comprehensive Excel report"""
        try:
            if not self.vulnerabilities:
                logger.error("No vulnerability data to export")
                return False
            
            # Create enhanced vulnerability records
            enhanced_vulns = []
            for vuln in self.vulnerabilities:
                enhanced_vuln = vuln.copy()
                additional_info = self.extract_additional_data(vuln)
                enhanced_vuln.update(additional_info)
                enhanced_vulns.append(enhanced_vuln)
            
            df = pd.DataFrame(enhanced_vulns)
            
            # Create Excel writer with multiple sheets
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # All findings
                df.to_excel(writer, sheet_name='All_Findings', index=False)
                
                # High/Critical severity findings
                if 'severity' in df.columns:
                    high_critical = df[df['severity'].isin(['High', 'Critical'])]
                    if not high_critical.empty:
                        high_critical.to_excel(writer, sheet_name='High_Critical', index=False)
                
                # Summary statistics
                summary_data = {
                    'Metric': ['Total Vulnerabilities', 'Critical', 'High', 'Medium', 'Low'],
                    'Count': [
                        len(df),
                        len(df[df['severity'] == 'Critical']) if 'severity' in df.columns else 0,
                        len(df[df['severity'] == 'High']) if 'severity' in df.columns else 0,
                        len(df[df['severity'] == 'Medium']) if 'severity' in df.columns else 0,
                        len(df[df['severity'] == 'Low']) if 'severity' in df.columns else 0
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            logger.info(f"Excel report generated: {output_file}")
            logger.info(f"Total vulnerabilities exported: {len(enhanced_vulns)}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating Excel report: {e}")
            return False

# Usage example
if __name__ == "__main__":
    # Initialize converter
    converter = AzureVulnerabilityExcelConverter("./json_files")
    
    # Load and process JSON files
    if converter.load_json_files():
        # Generate Excel report with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"azure_defender_findings_{timestamp}.xlsx"
        
        if converter.generate_excel_report(output_file):
            print(f"\n✅ Conversion completed successfully!")
            print(f"📊 Excel file created: {output_file}")
        else:
            print("❌ Failed to generate Excel report")
    else:
        print("❌ Failed to load JSON files")
```

## Why This Works Like Magic

This approach is effective because:

1. **Direct API Access**: We're using the same API that the Azure portal uses internally
2. **Complete Data**: Unlike screen scraping, this gives us the full dataset with all metadata
3. **Structured Format**: JSON data is easily parseable and convertible to Excel
4. **Automation Ready**: Once you have the process, it can be scripted and automated

## Advanced Tips for Security Engineers

### 1. Batch Processing Multiple Assessments
```python
def process_multiple_assessments(assessment_files):
    all_findings = []
    for file_path in assessment_files:
        findings = extract_findings_from_json(file_path)
        all_findings.extend(findings)
    
    # Create comprehensive report
    create_master_excel_report(all_findings)
```

### 2. Adding Severity Filtering
```python
def filter_by_severity(findings, min_severity='Medium'):
    severity_order = {'Low': 1, 'Medium': 2, 'High': 3, 'Critical': 4}
    min_level = severity_order.get(min_severity, 2)
    
    return [f for f in findings 
            if severity_order.get(f.get('Severity', 'Low'), 1) >= min_level]
```

### 3. Automated Reporting Pipeline
```bash
#!/bin/bash
# automated_security_report.sh

# Extract findings
python extract_azure_findings.py

# Generate Excel report
python convert_to_excel.py

# Email to security team
python send_security_report.py
```

## Lessons for Cloud Security Engineers

This experience highlights several important principles:

1. **Browser DevTools Are Your Friend**: When official export options don't exist, the browser's network tab often reveals the underlying APIs

2. **APIs Are Everywhere**: Modern web applications are API-driven; understanding this can unlock powerful automation opportunities

3. **JSON is Universal**: Most cloud services return data in JSON format, making it easy to process and transform

4. **Automation Saves Time**: What starts as a manual process can quickly become an automated pipeline

## Common Pitfalls and Solutions

### Authentication Issues
The API calls require proper Azure authentication. If you're scripting this:
```python
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient

credential = DefaultAzureCredential()
# Use credential for authenticated API calls
```

### Rate Limiting
Azure APIs have rate limits. Implement proper retry logic:
```python
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
```

## The Grand Finale

What started as a frustrating limitation in the Azure portal turned into a powerful automation opportunity. By understanding how modern web applications work and leveraging browser developer tools, we transformed a manual, time-consuming process into an automated pipeline.

The next time you encounter a "missing export button" in any cloud service, remember: the data is there, the APIs are accessible, and with a little detective work, you can unlock powerful automation capabilities.

Remember: In the world of cloud security, the best defense is not just identifying vulnerabilities, but efficiently managing and reporting on them. Sometimes that means thinking outside the portal! 🔍

Happy hunting! 🚀

---
*This article is based on real-world experiences with Azure security management. Always ensure you have proper authorization before accessing APIs, and follow your organization's security policies.*