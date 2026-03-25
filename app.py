from flask import Flask, render_template_string, send_file, jsonify
from flask_cors import CORS
import requests
import pandas as pd
import io
import time

app = Flask(__name__)
CORS(app)

# =========================
# CONFIG
# =========================

# 👉 Prefer CSV (FASTER)
GITHUB_CSV_URL = "https://raw.githubusercontent.com/RajuSakshena/jobs-scraping-pipeline/main/output/Combined.csv"

# 👉 Backup Excel (if CSV not available)
GITHUB_EXCEL_URL = "https://raw.githubusercontent.com/RajuSakshena/jobs-scraping-pipeline/main/output/Combined.xlsx"

CACHE_DURATION = 300  # 5 minutes

cached_df = None
last_fetch_time = 0


# =========================
# HOME
# =========================
@app.route("/")
def home():
    return "Flask App Running 🚀"


# =========================
# FETCH DATA (WITH CACHE)
# =========================
def fetch_latest_data():
    global cached_df, last_fetch_time

    # ✅ Return cached data if valid
    if cached_df is not None and (time.time() - last_fetch_time < CACHE_DURATION):
        print("Using cached data...")
        return cached_df

    print("Fetching fresh data from GitHub...")

    try:
        # =========================
        # TRY CSV FIRST (FAST)
        # =========================
        try:
            response = requests.get(GITHUB_CSV_URL, timeout=10)
            response.raise_for_status()

            df = pd.read_csv(io.StringIO(response.text))
            print("Loaded CSV successfully ✅")

        except Exception as csv_error:
            print("CSV failed, switching to Excel...")

            # =========================
            # FALLBACK TO EXCEL
            # =========================
            response = requests.get(GITHUB_EXCEL_URL, timeout=15)
            response.raise_for_status()

            df = pd.read_excel(io.BytesIO(response.content))
            print("Loaded Excel successfully ✅")

        df = df.fillna("")

        # ✅ LIMIT ROWS (Performance)
        df = df.head(300)

        # ✅ Update cache
        cached_df = df
        last_fetch_time = time.time()

        return df

    except Exception as e:
        raise Exception(f"Data Fetch Error: {str(e)}")


# =========================
# DOWNLOAD FILE
# =========================
@app.route("/download")
def download_file():
    try:
        response = requests.get(GITHUB_EXCEL_URL, timeout=15)
        response.raise_for_status()

        return send_file(
            io.BytesIO(response.content),
            download_name="Jobs_Data.xlsx",
            as_attachment=True,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        return f"Download Error: {str(e)}", 500


# =========================
# JSON API
# =========================
@app.route("/jobs-json")
def jobs_json():
    try:
        df = fetch_latest_data()
        return jsonify(df.to_dict(orient="records"))

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================
# DASHBOARD UI
# =========================
@app.route("/jobs")
def jobs_dashboard():
    try:
        df = fetch_latest_data()

        # =========================
        # Description Clamp
        # =========================
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
            position: sticky;
            top: 0;
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

        <h2>🚀 Latest Job Listings</h2>

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


# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)
