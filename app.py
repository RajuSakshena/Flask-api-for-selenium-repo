from flask import Flask, render_template_string, send_file, jsonify
from flask_cors import CORS
import requests
import pandas as pd
import io
import time

app = Flask(__name__)
CORS(app)

# GitHub RAW Excel URL
GITHUB_RAW_URL = "https://raw.githubusercontent.com/RajuSakshena/jobs-scraping-pipeline/main/output/Combined.xlsx"


@app.route("/")
def home():
    return "Flask App Running"


# =========================
# FETCH LATEST EXCEL FROM GITHUB
# =========================
def fetch_latest_excel():

    try:
        # cache busting parameter
        url = f"{GITHUB_RAW_URL}?t={int(time.time())}"

        response = requests.get(url, timeout=30)

        if response.status_code != 200:
            raise Exception("Could not fetch Excel from GitHub")

        df = pd.read_excel(io.BytesIO(response.content))
        df = df.fillna("")

        return df

    except Exception as e:
        raise Exception(f"Excel Fetch Error: {str(e)}")


# =========================
# DOWNLOAD EXCEL
# =========================
@app.route("/download")
def download_excel():
    try:

        url = f"{GITHUB_RAW_URL}?t={int(time.time())}"

        response = requests.get(url, timeout=30)

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


# =========================
# JSON API FOR FRONTEND
# =========================
@app.route("/jobs-json")
def jobs_json():

    try:

        df = fetch_latest_excel()

        jobs = df.to_dict(orient="records")

        return jsonify(jobs)

    except Exception as e:

        return jsonify({"error": str(e)}), 500


# =========================
# HTML DASHBOARD
# =========================
@app.route("/jobs")
def jobs_dashboard():

    try:

        df = fetch_latest_excel()

        if "Description" in df.columns:

            df["Description"] = df["Description"].apply(
                lambda x: f"""
                <div class="clamp-4">{x}</div>
                <span class="more-btn">More</span>
                """ if len(str(x)) > 200 else x
            )

        table_html = df.to_html(index=False, escape=False)

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
        vertical-align: top;
        }}

        tr:hover {{
        background: #f2f2f2;
        }}

        .clamp-4 {{
        display: -webkit-box;
        -webkit-line-clamp: 4;
        -webkit-box-orient: vertical;
        overflow: hidden;
        }}

        .more-btn {{
        display: inline-block;
        margin-top: 5px;
        color: #58a648;
        cursor: pointer;
        font-weight: bold;
        }}

        </style>

        </head>

        <body>

        <h2>Latest Job Listings</h2>

        <a class="download-btn" href="/download">
        Download Full Excel File
        </a>

        {table_html}

        <script>

        document.addEventListener("click", function(e) {{

        if (e.target.classList.contains("more-btn")) {{

        let textDiv = e.target.previousElementSibling;

        if (textDiv.classList.contains("clamp-4")) {{

        textDiv.classList.remove("clamp-4");
        e.target.innerText = "Less";

        }} else {{

        textDiv.classList.add("clamp-4");
        e.target.innerText = "More";

        }}

        }}

        }});

        </script>

        </body>
        </html>
        """

        return render_template_string(html)

    except Exception as e:

        return f"Dashboard Error: {str(e)}", 500


if __name__ == "__main__":
    app.run(debug=True)
