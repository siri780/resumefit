from app.latex_io import RESUME, get_bullets, read_braced


def test_read_braced_handles_nested_braces():
    text = "{\\textbf{Hi} there}"
    content, end = read_braced(text, 0)
    assert content == "\\textbf{Hi} there"
    assert end == len(text)


def test_finds_all_11_bullets():
    tex = RESUME.read_text(encoding="utf-8")
    assert len(get_bullets(tex)) == 11


def test_positions_point_to_the_bullet_text():
    tex = RESUME.read_text(encoding="utf-8")
    for b in get_bullets(tex):
        assert tex[b["start"] + 1:b["end"] - 1] == b["text"]