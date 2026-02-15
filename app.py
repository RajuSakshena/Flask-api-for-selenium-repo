from flask import Flask, render_template_string, send_file
import requests
import pandas as pd
import io
import os

app = Flask(__name__)

# 🔵 GitHub RAW Excel URL
GITHUB_RAW_URL = "https://raw.githubusercontent.com/RajuSakshena/jobs-scraping-pipeline/main/output/Combined.xlsx"


@app.route("/")
def home():
    return "Flask App Running"


@app.route("/download")
def download_excel():
    try:
        response = requests.get(GITHUB_RAW_URL)

        if response.status_code != 200:
            return "Could not fetch file from GitHub", 404

        return send_file(
            io.BytesIO(response.content),
            download_name="Combined.xlsx",
            as_attachment=True,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        return f"Download Error: {str(e)}", 500


@app.route("/jobs")
def jobs_dashboard():
    try:
        response = requests.get(GITHUB_RAW_URL)

        if response.status_code != 200:
            return "Could not fetch file from GitHub", 404

        # Read Excel
        df = pd.read_excel(io.BytesIO(response.content))

        # Clean display
        df = df.fillna("")

        # Convert to HTML table
        table_html = df.to_html(index=False)

        html = f"""
        <html>
        <head>
            <title>Jobs Dashboard</title>
            <style>
                body {{
                    font-family: Arial;
                    padding: 20px;
                    background-color: #f4f6f9;
                }}
                h2 {{
                    margin-bottom: 15px;
                }}
                .download-btn {{
                    background: #58a648;
                    color: white;
                    padding: 10px 18px;
                    border-radius: 6px;
                    text-decoration: none;
                    font-weight: bold;
                }}
                .download-btn:hover {{
                    background: #0b3c5d;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                    font-size: 14px;
                    background: white;
                }}
                th {{
                    background: #0b3c5d;
                    color: white;
                    padding: 8px;
                    text-align: left;
                }}
                td {{
                    padding: 6px;
                    border-bottom: 1px solid #ddd;
                }}
                tr:hover {{
                    background: #f2f2f2;
                }}
            </style>
        </head>
        <body>
            <h2>Latest Job Listings</h2>

            <a class="download-btn" href="/download">
                Download Full Excel File
            </a>

            {table_html}
        </body>
        </html>
        """

        return render_template_string(html)

    except Exception as e:
        return f"Dashboard Error: {str(e)}", 500


if __name__ == "__main__":
    # For local development only
    app.run()
