from app.latex_io import RESUME, apply_edits, get_bullets, read_braced, replace_bullet


def test_read_braced_handles_nested_braces():
    text = "{\\textbf{Hi} there}"
    content, end = read_braced(text, 0)
    assert content == "\\textbf{Hi} there"
    assert end == len(text)


def test_finds_all_14_bullets():
    tex = RESUME.read_text(encoding="utf-8")
    assert len(get_bullets(tex)) == 14


def test_positions_point_to_the_bullet_text():
    tex = RESUME.read_text(encoding="utf-8")
    for b in get_bullets(tex):
        assert tex[b["start"] + 1:b["end"] - 1] == b["text"]


def test_replace_bullet_changes_only_that_bullet():
    tex = RESUME.read_text(encoding="utf-8")
    bullets = get_bullets(tex)

    new_tex = replace_bullet(tex, bullets[6], "NEW TEXT")
    new_bullets = get_bullets(new_tex)

    assert new_bullets[6]["text"] == "NEW TEXT"
    assert len(new_bullets) == 14

    for i in range(12):
        if i != 6:
            assert new_bullets[i]["text"] == bullets[i]["text"]


def test_apply_edits_replaces_several_bullets():
    tex = RESUME.read_text(encoding="utf-8")

    updated = apply_edits(tex, {2: "FIRST", 8: "SECOND"})
    bullets = get_bullets(updated)

    assert bullets[2]["text"] == "FIRST"
    assert bullets[8]["text"] == "SECOND"
    assert len(bullets) == 14