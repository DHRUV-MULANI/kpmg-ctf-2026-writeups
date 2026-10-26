from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

ALLOWED_COMMANDS = ["ping", "traceroute", "nslookup"]

def is_allowed(cmd):
    return any(cmd.startswith(c) for c in ALLOWED_COMMANDS)

def sanitize(user_input):
    blacklist = [";", "&", "|", "`", "$(","<"]
    for b in blacklist:
        user_input = user_input.replace(b, "")
    return user_input

@app.route("/run", methods=["POST"])
def run():
    cmd = request.form.get("cmd", "")

    if not is_allowed(cmd):
        return "<div class='output'>Command not allowed</div><br><a href='/'>Back</a>", 403

    cmd = sanitize(cmd)

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=10
        )
        output = result.stdout.decode(errors="replace")

    except subprocess.TimeoutExpired:
        output = "Command timed out."
    except Exception as e:
        output = str(e)

    return f"""
    <html>
    <body style="background:#f4f6f8; font-family:Arial; text-align:center;">
        <div style="width:600px;margin:auto;background:white;padding:20px;border-radius:10px;">
            <h3>Command Output</h3>
            <div style="background:#111;color:#0f0;padding:10px;border-radius:6px;
                        text-align:left;font-family:monospace;white-space:pre-wrap;">
{output}
            </div>
            <br>
            <a href="/">&#8592; Back</a>
        </div>
    </body>
    </html>
    """

@app.route("/")
def home():
    return """
    <html>
    <head>
        <title>Safe Command Runner</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f4f6f8; text-align: center; padding: 40px; }
            .container { background: white; padding: 25px; border-radius: 10px; width: 500px; margin: auto; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
            h2 { margin-bottom: 10px; }
            textarea { width: 100%; height: 80px; padding: 10px; margin-top: 10px; border-radius: 6px; border: 1px solid #ccc; font-family: monospace; }
            .btn { margin-top: 10px; padding: 10px 15px; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }
            .run-btn { background-color: #007bff; color: white; }
            .clear-btn { background-color: #6c757d; color: white; }
            .hint { margin-top: 15px; color: #666; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Safe Command Runner</h2>
            <p>Only network debugging commands are allowed.</p>
            <form method="POST" action="/run">
                <textarea name="cmd" placeholder="Enter command here."></textarea><br>
                <button class="btn run-btn" type="submit">Run</button>
                <button class="btn clear-btn" type="reset">Clear</button>
            </form>
            <div class="hint">Hint: Only certain commands are allowed &#128521;</div>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)