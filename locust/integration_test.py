"""
Usage:
    export GOOGLE_APPLICATION_CREDENTIALS=<path_to_key.json>
    python scripts/integration_test.py \
        -c <config_path> \
        -t <test_type>
"""
import os
import json
import yaml
import csv
import subprocess
import time
import argparse
import requests
import re
import sys
import matplotlib.pyplot as plt
import pandas as pd

from multiprocessing import Process
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime, timedelta
from tqdm import tqdm
from PyPDF2 import PdfMerger
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

from linkinpark.lib.common.secret_accessor import SecretAccessor
from linkinpark.lib.common.gcs_helper import GcsHelper


# def get_csv_path(config_path):
#     dirname = os.path.join(os.path.dirname(config_path), 'reports')
#     os.makedirs(dirname, exist_ok=True)
#     server_name = os.path.normpath(config_path).split(os.sep)[-2]
#     return f"{dirname}/{server_name}"



def plot_total_requests_per_seconds(data, pdf_pages):
    data['Timestamp'] = pd.to_datetime(data['Timestamp'], unit='s')
    plt.figure(figsize=(12, 6))
    plt.plot(data['Timestamp'], data['Requests/s'], label='RPS', color='blue')
    plt.plot(data['Timestamp'], data['Failures/s'], label='Failures', color='red')
    plt.xlabel('Time Stamp')
    plt.ylabel('Request Counts')
    plt.title('Total Requests per Seconds')
    plt.legend()
    plt.grid(True)
    pdf_pages.savefig()
    plt.close()


def plot_response_times(data, pdf_pages):
    if data['Timestamp'].dtype == 'int64':
        data['Timestamp'] = pd.to_datetime(data['Timestamp'], unit='s')
    plt.figure(figsize=(12, 6))
    plt.plot(data['Timestamp'], data['50%'], label='Median Response Time', color='blue')
    plt.plot(data['Timestamp'], data['95%'], label='95% Percentile', color='red')
    plt.xlabel('Time Stamp')
    plt.ylabel('Response Time (ms)')
    plt.title('Response Times (ms)')
    plt.legend()
    plt.grid(True)
    pdf_pages.savefig()
    plt.close()


def create_charts_pdf(config_path):
    csv_path = get_csv_path(config_path) + "_stats_history.csv"
    data = pd.read_csv(csv_path)
    pdf_path = os.path.join(os.path.dirname(csv_path), 'charts.pdf')

    print("Writing charts to pdf...")
    with PdfPages(pdf_path) as pdf_pages:
        plot_total_requests_per_seconds(data, pdf_pages)
        plot_response_times(data, pdf_pages)

    return pdf_path


def get_secret():
    credentials_file = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not credentials_file:
        raise ValueError(
            "GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.")
    
    accessor = SecretAccessor()
    username = accessor.access_secret('aiServerAuth-integrationTest-email')
    password = accessor.access_secret('aiServerAuth-integrationTest-password')
    return username, password


def compute_rescusage_csv(test_type):
    duration_seconds = config[test_type]['duration']
    interval_seconds = config[test_type]['interval']
    total_requests = duration_seconds / interval_seconds
    csv_path = os.path.join(os.path.dirname(config_path), 'reports/merge_reports.csv')

    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Timestamp', 'CPU_Percent', 'CPU_Count', 'Memory_Percent', 'Memory_Used_Bytes'])

        for _ in tqdm(range(int(total_requests)), desc="Processing", ncols=100, mininterval=1):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            resource_usage = get_request_response('/resc-usage')
            
            writer.writerow([
                timestamp, 
                resource_usage['cpu_percent'], 
                resource_usage['cpu_count'], 
                resource_usage['memory_percent'], 
                resource_usage['memory_used (bytes)']
            ])
            time.sleep(interval_seconds)

    return csv_path


def merge_csv_files(config_path, csv_path, start_time):
    locust_csv = get_csv_path(config_path) + "_stats_history.csv"
    locust_df = pd.read_csv(locust_csv)
    resc_df = pd.read_csv(csv_path)

    # Replace TimeStamp generated by Locust
    num_rows = len(locust_df)
    timestamps = [start_time + timedelta(seconds=i) for i in range(num_rows)]
    locust_df['Timestamp'] = pd.to_datetime([ts.strftime("%Y-%m-%d %H:%M:%S") for ts in timestamps])

    resc_df['Timestamp'] = pd.to_datetime(resc_df['Timestamp'], format="%Y-%m-%d %H:%M:%S")

    merged_df = pd.merge(resc_df, locust_df, on='Timestamp', how='left')
    columns_to_keep = [
        "Timestamp", "CPU_Percent", "CPU_Count", "Memory_Percent", 
        "Memory_Used_Bytes", "User Count", "Requests/s", 
        "Total Average Response Time", "Total Min Response Time", "Total Max Response Time"
    ]
    df_filtered = merged_df[columns_to_keep]
    df_filtered.to_csv(csv_path, index=False)


def get_request_response(endpoint):
    listen_host = "127.0.0.1:80"

    url = listen_host + endpoint

    response = requests.get(url)
    if not response:   
        raise Exception("Request get empty response, maybe due to server not correctly running on k8s.")
    
    return response


def check_app_version():
 
    health_check = get_request_response('/health-check')
    app_version = health_check['app_version']
        
    return app_version


# def upload_pdf(pdf_path, config_path, start_time):
#     server_name = os.path.normpath(config_path).split(os.sep)[-2]
#     bucket_name = 'jubo-ai-serving'
#     format_time = start_time.strftime("%Y-%m-%d_%H:%M:%S")
#     blob_name = f'integration_test_reports/{server_name}/{server_name}_{format_time}.pdf'

#     gcs_helper = GcsHelper()
#     gcs_helper.upload_file_to_bucket(bucket_name, blob_name, pdf_path)

#     return f'gs://{bucket_name}/{blob_name}'


def csv_to_pdf(csv_path):
    df = pd.read_csv(csv_path)

    if df.empty:
        table_data = [df.columns]
        col_widths = [len(col) for col in df.columns]
    else:
        table_data = [df.columns] + df.values.tolist()
        col_widths = [max(df[col].astype(str).apply(len).max(), len(col)) for col in df.columns]

    # Determine the optimal figure width.
    total_width = sum(col_widths)
    col_widths = [width / total_width for width in col_widths]
    fig_width = sum(col_widths) * 15
    fig, ax = plt.subplots(figsize=(fig_width, 4))
    ax.axis('off')

    # Plot the table
    table = ax.table(cellText=table_data, cellLoc='center', loc='center', colWidths=col_widths)
    table.auto_set_font_size(False)
    table.set_fontsize(9)

    reports_path = os.path.dirname(csv_path)
    csv_filename = os.path.basename(csv_path)
    filename = csv_filename[:-len('.csv')]
    csv_to_pdf_path = os.path.join(reports_path, f'{filename}.pdf')
    with PdfPages(csv_to_pdf_path) as pdf:
        pdf.savefig(fig, bbox_inches='tight')

    return csv_to_pdf_path


def create_version_pdf(app_version, reports_path):
    output_path = os.path.join(reports_path, 'app_version.pdf')
    doc = SimpleDocTemplate(output_path, pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    title_text = f"App Version: {app_version}"
    story = [Paragraph(title_text, styles['Title'])]  # Create a title with the app_version
    doc.build(story)
    return output_path


def compute_failure_csv(config_path):
    stats_csv_path = get_csv_path(config_path) + "_stats.csv"
    stats_df = pd.read_csv(stats_csv_path)
    request_count = stats_df['Request Count'].values[0]
    failure_count = stats_df['Failure Count'].values[0]

    failures_csv_path = get_csv_path(config_path) + "_failures.csv"
    failures_df = pd.read_csv(failures_csv_path)

    failures_df['Failure Percentage'] = ((failures_df['Occurrences'] / failure_count) * 100).round(3)
    failures_df['Request Percentage'] = ((failures_df['Occurrences'] / request_count) * 100).round(3)

    reports_path = os.path.dirname(failures_csv_path)
    new_failure_csv_path = os.path.join(reports_path, 'failures.csv')
    failures_df.to_csv(new_failure_csv_path, index=False)
    
    return new_failure_csv_path


def compute_exception_csv(config_path):
    exceptions_csv_path = get_csv_path(config_path) + "_exceptions.csv"
    return exceptions_csv_path


def compute_final_report(csv_paths, app_version, charts_pdf_path):
    pdf_paths = []
    for csv_path in csv_paths:
        pdf_paths.append(csv_to_pdf(csv_path))

    reports_path = os.path.dirname(pdf_paths[0])
    app_version_pdf_path = create_version_pdf(app_version, reports_path)
    merger = PdfMerger()
    merger.append(app_version_pdf_path)

    final_report_pdf = os.path.join(reports_path, 'final_report.pdf')
    for pdf_path in pdf_paths:
        merger.append(pdf_path)

    merger.append(charts_pdf_path)
    merger.write(final_report_pdf)
    merger.close()

    return final_report_pdf



def main(config_path, test_type):

    
    merge_csv_path = compute_rescusage_csv(config_path, token, test_type)


    merge_csv_files(config_path, merge_csv_path, start_time)

    csv_paths = []
    csv_paths.append(merge_csv_path)
    csv_paths.append(compute_failure_csv(config_path))
    csv_paths.append(compute_exception_csv(config_path))
    charts_pdf_path = create_charts_pdf(config_path)

    final_report_pdf = compute_final_report(csv_paths, app_version, charts_pdf_path)
    
    gcs_path = upload_pdf(final_report_pdf, config_path, start_time)
    print(f'PDF report save locally: {final_report_pdf}')
    print(f'PDF report save on GCS: {gcs_path}')

    print('|======== integration test ends =======|')

    return [final_report_pdf, gcs_path]

