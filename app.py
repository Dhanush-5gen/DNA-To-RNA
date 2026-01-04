from flask import Flask, render_template, request, Response

app = Flask(__name__)

def wrap_sequence(seq, line_length=60):
    lines = []
    current = ""
    visible_count = 0
    i = 0

    while i < len(seq):
        if seq[i] == "<":  # HTML tag
            tag = ""
            while seq[i] != ">":
                tag += seq[i]
                i += 1
            tag += ">"
            current += tag
        else:
            current += seq[i]
            visible_count += 1

        if visible_count == line_length:
            lines.append(current)
            current = ""
            visible_count = 0
        i += 1

    if current:
        lines.append(current)

    return "\n".join(lines)


def analyze_and_convert(sequence, strict=False):
    rna_raw = ""
    gc = 0
    length = 0
    invalid = 0

    for line in sequence.splitlines():
        if line.startswith(">"):
            rna_raw += line + "\n"
            continue

        for base in line.upper():
            if base in ["A", "T", "G", "C"]:
                length += 1
                if base in ["G", "C"]:
                    gc += 1
                rna_raw += "U" if base == "T" else base
            elif base in [" ", "\t"]:
                continue
            else:
                invalid += 1
                if strict:
                    continue
                rna_raw += f"<span class='error'>{base}</span>"

        rna_raw += "\n"

    wrapped_rna = wrap_sequence(rna_raw.strip())
    gc_percent = round((gc / length) * 100, 2) if length else 0

    return wrapped_rna, length, gc_percent, invalid


@app.route("/", methods=["GET", "POST"])
def index():
    rna_sequence = ""
    input_sequence = ""
    stats = {}

    if request.method == "POST":
        input_sequence = request.form.get("sequence", "")
        strict = request.form.get("strict") == "on"

        rna_sequence, length, gc, invalid = analyze_and_convert(input_sequence, strict)

        stats = {
            "length": length,
            "gc": gc,
            "invalid": invalid
        }

    return render_template(
        "index.html",
        rna_sequence=rna_sequence,
        input_sequence=input_sequence,
        stats=stats
    )


@app.route("/download", methods=["POST"])
def download():
    rna = request.form.get("rna", "")
    clean_rna = rna.replace("<span class='error'>", "").replace("</span>", "")
    fasta = ">RNA_sequence\n" + clean_rna

    return Response(
        fasta,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment; filename=rna_sequence.fasta"}
    )


if __name__ == "__main__":
    app.run(debug=True)
