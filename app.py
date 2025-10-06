from flask import Flask, render_template, request, send_file, redirect
import yt_dlp
import os
import uuid
import threading

app = Flask(__name__)


DOWNLOAD_DIR = "/tmp/download" 
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def delete_file_later(filepath, delay=120):
    def remove():
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"Deleted file: {filepath}")
        except Exception as e:
            print(f"Error deleting file: {e}")
    threading.Timer(delay, remove).start()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        if not url:
            return "<h3>Please provide a URL.</h3>"
        return redirect(f"/info?url={url}")
    return render_template("index.html")

@app.route("/info")
def info():
    url = request.args.get("url")
    if not url:
        return redirect("/")

    ydl_opts = {'quiet': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        formats = []
        for f in info.get('formats', []):
            if f.get('url'):
                formats.append({
                    "format_id": f.get("format_id"),
                    "resolution": f.get("format_note") or f.get("height") or "Unknown",
                    "filesize": f.get("filesize", 0) or 0
                })

        if not formats:
            return "<h3>No downloadable formats found for this URL.</h3>"

        return render_template(
            "info.html",
            title=info.get("title", "Unknown Title"),
            thumbnail=info.get("thumbnail"),
            formats=formats,
            url=url
        )

    except Exception as e:
        return f"<h3>Error fetching video info: {str(e)}</h3>"

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url")
    format_id = request.form.get("format_id")

    if not url or not format_id:
        return "<h3>Missing URL or format ID.</h3>"

    
    filename = f"{uuid.uuid4()}.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    ydl_opts = {
        'format': format_id,
        'outtmpl': filepath,
        'quiet': True,
        'no_warnings': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

       
        delete_file_later(filepath, delay=120)

        return send_file(filepath, as_attachment=True)

    except Exception as e:
        return f"<h3>Error downloading video: {str(e)}</h3>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
