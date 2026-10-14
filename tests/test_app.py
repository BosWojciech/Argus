"""Smoke test of the window. Skipped when no display is available."""

import tkinter

import pytest


@pytest.fixture
def app():
    from argus.app import App
    try:
        window = App()
    except tkinter.TclError as exc:
        pytest.skip(f"no display: {exc}")
    window.withdraw()
    yield window
    window.destroy()


def test_tabs_render_records(app):
    assert list(app.tabs) == ["Zbiorcze", "Osobowe", "Firmowe", "Bankowe", "Auto"]
    for tab in app.tabs.values():
        assert tab.record
        assert len(tab.results.winfo_children()) == 2 * len(tab.record)


def test_options_feed_generators(app):
    app.regon.set("14 cyfr")
    app.tabs["Firmowe"].generate()
    assert len(app.tabs["Firmowe"].record["REGON"]) == 14

    app.card.set("Visa")
    app.tabs["Bankowe"].generate()
    assert app.tabs["Bankowe"].record["Karta płatnicza"].startswith("4")


def test_bad_age_input_keeps_record(app):
    tab = app.tabs["Osobowe"]
    before = tab.record
    app.age_entry.insert(0, "2001-02-29")
    tab.generate()
    assert tab.record is before
    assert "Niepoprawna" in app.status.cget("text")


def test_copy_to_clipboard(app):
    app.copy("12345")
    assert app.clipboard_get() == "12345"


def test_options_panel_toggles(app):
    tab = app.tabs["Osobowe"]
    assert not tab.options.winfo_manager()
    tab.toggle_options()
    assert tab.options.winfo_manager() == "pack"
    tab.toggle_options()
    assert not tab.options.winfo_manager()
    assert app.tabs["Auto"].options is None
