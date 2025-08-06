from flask import Flask, render_template, Response
import subprocess

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

def generate_output():
    """Generator function to stream live command output"""
    process = subprocess.Popen(["python", "C:\\Users\\matti\\Desktop\\Licenta\\START_PROCESS.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    for line in process.stdout:
        yield line + "<br>\n"
    for line in process.stderr:
        yield line + "<br>\n"

@app.route("/start_process", methods=["POST"])
def start_process():
    return Response(generate_output(), mimetype="text/html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
