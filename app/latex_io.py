from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESUME = ROOT / "data" / "resume_ds.tex"  # default base resume


def read_braced(text, open_pos):
    """Return the text inside {...} starting at open_pos, and where it ends."""
    depth = 0
    for i in range(open_pos, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[open_pos + 1:i], i + 1
    raise ValueError("Unbalanced braces in the resume")


def get_bullets(tex):
    """Find every \\resumeItem{...} and the section it belongs to."""
    tag = "\\resumeItem{"
    bullets = []
    pos = 0
    while True:
        found = tex.find(tag, pos)
        if found == -1:
            break
        section = None
        sec_pos = tex.rfind("\\section{", 0, found)
        if sec_pos != -1:
            section, _ = read_braced(tex, sec_pos + len("\\section"))
        open_pos = found + len(tag) - 1
        text, end = read_braced(tex, open_pos)
        bullets.append({"section": section, "text": text,
                        "start": open_pos, "end": end})
        pos = end
    return bullets


def replace_bullet(tex, bullet, new_text):
    """Return tex with one bullet's text replaced by new_text."""
    return tex[:bullet["start"] + 1] + new_text + tex[bullet["end"] - 1:]


def apply_edits(tex, edits):
    """Replace multiple resume bullets without shifting later positions."""
    bullets = get_bullets(tex)
    for i in sorted(edits, reverse=True):
        tex = replace_bullet(tex, bullets[i], edits[i])
    return tex


if __name__ == "__main__":
    tex = RESUME.read_text(encoding="utf-8")
    bullets = get_bullets(tex)
    print(f"Found {len(bullets)} bullets\n")
    for i, b in enumerate(bullets, start=1):
        print(f"{i}. [{b['section']}] {b['text'][:80]}")