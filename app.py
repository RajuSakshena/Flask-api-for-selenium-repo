from flask import Flask, render_template_string, send_file
import requests
import pandas as pd
import io

app = Flask(__name__)

GITHUB_RAW_URL = "https://raw.githubusercontent.com/RajuSakshena/jobs-scraping-pipeline/main/output/Combined.xlsx"

# 🔥 Global cache
cached_excel_bytes = None
cached_table_html = None


def load_excel_once():
    global cached_excel_bytes, cached_table_html

    try:
        response = requests.get(GITHUB_RAW_URL, timeout=20)

        if response.status_code == 200:
            cached_excel_bytes = response.content

            df = pd.read_excel(io.BytesIO(cached_excel_bytes), engine="openpyxl")
            df = df.fillna("")
            df = df.head(500)   # safety limit (avoid huge render)

            cached_table_html = df.to_html(index=False)

            print("✅ Excel Loaded & Cached Successfully")

        else:
            print("❌ Failed to fetch Excel")

    except Exception as e:
        print("❌ Load Error:", e)


# 🔥 Load once when server starts
load_excel_once()


@app.route("/")
def home():
    return "Flask App Running"


@app.route("/download")
def download_excel():
    if cached_excel_bytes:
        return send_file(
            io.BytesIO(cached_excel_bytes),
            download_name="Combined.xlsx",
            as_attachment=True,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    return "File not available", 404


@app.route("/jobs")
def jobs_dashboard():

    if not cached_table_html:
        return "Data not loaded yet. Please refresh.", 500

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

        {cached_table_html}
    </body>
    </html>
    """

    return render_template_string(html)


if __name__ == "__main__":
    app.run()
