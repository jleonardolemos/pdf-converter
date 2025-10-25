from flask import Flask, render_template_string, request, Response
from pdfminer.high_level import extract_text
import tempfile
import re

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>PDF to Markdown Converter</title>
<style>
    body {
        background-color: #1e1e1e;
        color: #dcdcdc;
        font-family: 'Segoe UI', sans-serif;
        margin: 40px;
    }
    h2, h3 { color: #ffffff; }
    input[type=file], button, label {
        margin: 8px 0;
    }
    input[type=file] {
        background-color: #2a2a2a;
        color: #ccc;
        border: 1px solid #444;
        padding: 6px;
        border-radius: 4px;
    }
    textarea {
        width: 100%;
        height: 400px;
        background-color: #252526;
        color: #dcdcdc;
        border: 1px solid #444;
        border-radius: 6px;
        padding: 10px;
        resize: vertical;
    }
    button {
        background-color: #0a84ff;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        margin-right: 6px;
        cursor: pointer;
        font-weight: bold;
    }
    button:hover {
        background-color: #0077e6;
    }
    .clean-btn {
        background-color: #e81123;
    }
    .clean-btn:hover {
        background-color: #c50f1f;
    }
    .options {
        margin: 10px 0;
    }
    .checkbox {
        margin-right: 12px;
    }
</style>
</head>
<body>
    <h2>PDF → Markdown Converter</h2>
    <form method="POST" enctype="multipart/form-data">
        <label>Select PDF file:</label><br>
        <input type="file" name="pdf_file" accept=".pdf" required><br>

        <div class="options">
            <label class="checkbox">
                <input type="checkbox" name="remove_breaks" {% if remove_breaks %}checked{% endif %}>
                Remove line breaks
            </label>
            <label class="checkbox">
                <input type="checkbox" name="remove_page_ctrl" {% if remove_page_ctrl %}checked{% endif %}>
                Remove page control characters
            </label>
        </div>

        <button type="submit">Convert</button>
        <button type="button" class="clean-btn" onclick="cleanOutput()">Clean</button>
    </form>

    <h3>Result:</h3>
    <textarea id="output" readonly>{{ result }}</textarea>

<script>
function cleanOutput() {
    document.getElementById("output").value = "";
    document.querySelector('input[type="file"]').value = "";
    document.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
}
</script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    result = ""
    remove_breaks = False
    remove_page_ctrl = False

    if request.method == "POST":
        file = request.files.get("pdf_file")
        remove_breaks = "remove_breaks" in request.form
        remove_page_ctrl = "remove_page_ctrl" in request.form

        if file and file.filename.endswith(".pdf"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                file.save(tmp.name)
                result = extract_text(tmp.name)

            if remove_page_ctrl:
                # Remove form feed characters (\f) and related control codes
                result = re.sub(r"\f+", "", result)

            if remove_breaks:
                # Collapse multiple line breaks and join lines neatly
                result = re.sub(r"\n+", " ", result)
                result = re.sub(r"\s{2,}", " ", result)

    return render_template_string(HTML_PAGE, result=result,
                                  remove_breaks=remove_breaks,
                                  remove_page_ctrl=remove_page_ctrl)

@app.route("/api/convert", methods=["POST"])
def api_convert():
    file = request.files.get("pdf_file")
    if not file or not file.filename.endswith(".pdf"):
        return Response("Missing or invalid PDF file.", status=400)

    remove_breaks = request.form.get("remove_breaks", "false").lower() in ["1", "true", "yes", "on"]
    remove_page_ctrl = request.form.get("remove_page_ctrl", "false").lower() in ["1", "true", "yes", "on"]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        file.save(tmp.name)
        result = extract_text(tmp.name)

    if remove_page_ctrl:
        result = re.sub(r"\f+", "", result)

    if remove_breaks:
        result = re.sub(r"\n+", " ", result)
        result = re.sub(r"\s{2,}", " ", result)

    return Response(result, mimetype="text/plain")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
