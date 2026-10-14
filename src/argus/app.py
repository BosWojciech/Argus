"""CustomTkinter desktop UI: one tab per generator, click a value to copy it."""

import re

import customtkinter as ctk

from argus import data, records

GENDER_LABELS = {"obojętnie": "any", "kobieta": "female", "mężczyzna": "male"}
CARD_LABELS = {"obojętnie": "any", "Visa": "Visa", "MasterCard": "MasterCard"}
REGON_LABELS = {"9 cyfr": 9, "14 cyfr": 14}


class GeneratorTab:
    """Options panel (optional, collapsible), a Generate button and the result list."""

    def __init__(self, app: "App", parent, make_record, build_options=None):
        self.app = app
        self.make_record = make_record
        self.record: dict = {}

        self.bar = bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.pack(fill="x", pady=(4, 8))
        ctk.CTkButton(bar, text="Generuj", command=self.generate).pack(side="left")

        self.options = None
        if build_options:
            self.options = ctk.CTkFrame(parent)
            build_options(self.options)
            ctk.CTkButton(bar, text="Konfiguruj", fg_color="transparent", border_width=1,
                          text_color=("gray10", "gray90"), command=self.toggle_options).pack(side="left", padx=8)

        self.results = ctk.CTkScrollableFrame(parent)
        self.results.pack(fill="both", expand=True)
        self.results.grid_columnconfigure(1, weight=1)

    def toggle_options(self):
        """Show or hide the options panel above the results."""
        if self.options.winfo_manager():
            self.options.pack_forget()
        else:
            self.options.pack(fill="x", pady=(0, 8), after=self.bar)

    def generate(self):
        """Build a new record; on bad input keep the old one and report the error."""
        try:
            self.record = self.make_record()
        except ValueError as exc:
            self.app.set_status(str(exc), error=True)
            return
        for child in self.results.winfo_children():
            child.destroy()
        for row, (label, value) in enumerate(self.record.items()):
            ctk.CTkLabel(self.results, text=label, anchor="w").grid(row=row, column=0, sticky="w", padx=(4, 12), pady=3)
            ctk.CTkButton(self.results, text=value, anchor="w", fg_color=("gray85", "gray20"),
                          text_color=("gray10", "gray90"), hover_color=("gray75", "gray30"),
                          command=lambda v=value: self.app.copy(v)).grid(row=row, column=1, sticky="ew", pady=3)
        self.app.set_status("Kliknij wartość, by ją skopiować.")


def _option_row(parent, row: int, label: str, widget):
    """Place a label and its control on one row of an options grid."""
    ctk.CTkLabel(parent, text=label, anchor="w").grid(row=row, column=0, sticky="w", padx=8, pady=6)
    widget.grid(row=row, column=1, sticky="w", padx=8, pady=6)


class App(ctk.CTk):
    """Main window."""

    def __init__(self):
        super().__init__()
        self.title("Argus - generator danych testowych")
        self.geometry("680x780")
        self.minsize(520, 480)

        ctk.CTkLabel(self, text="Argus", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(14, 0))
        ctk.CTkLabel(self, text="Poprawne formalnie dane testowe: PESEL, NIP, REGON, IBAN, karty, VIN",
                     text_color=("gray40", "gray60")).pack()
        ctk.CTkLabel(self, text=data.source_note(), font=ctk.CTkFont(size=11),
                     text_color=("gray50", "gray50")).pack()

        tabview = ctk.CTkTabview(self)
        tabview.pack(fill="both", expand=True, padx=14, pady=8)
        self.status = ctk.CTkLabel(self, text="", anchor="w")
        self.status.pack(fill="x", padx=18, pady=(0, 10))

        # Option state, read by the record lambdas below.
        self.age_range = ctk.StringVar(value="0-99")
        self.gender = ctk.StringVar(value="obojętnie")
        self.regon = ctk.StringVar(value="9 cyfr")
        self.card = ctk.StringVar(value="obojętnie")
        self.age_entry: ctk.CTkEntry | None = None

        specs = [
            ("Zbiorcze", records.combined, None),
            ("Osobowe", lambda: records.person(GENDER_LABELS[self.gender.get()], self.age_range.get(),
                                               self.age_entry.get()), self._personal_options),
            ("Firmowe", lambda: records.company(REGON_LABELS[self.regon.get()]), self._company_options),
            ("Bankowe", lambda: records.bank(CARD_LABELS[self.card.get()]), self._bank_options),
            ("Auto", records.vehicle, None),
        ]
        self.tabs: dict[str, GeneratorTab] = {}
        for name, make_record, build_options in specs:
            self.tabs[name] = GeneratorTab(self, tabview.add(name), make_record, build_options)
            self.tabs[name].generate()

    def _personal_options(self, frame):
        """Age range, gender and the free-text age/date field."""
        # Picking a range clears the typed age, since a typed age wins.
        _option_row(frame, 0, "Wiek", ctk.CTkSegmentedButton(
            frame, values=list(records.AGE_RANGES), variable=self.age_range,
            command=lambda _: self.age_entry.delete(0, "end")))
        _option_row(frame, 1, "Płeć", ctk.CTkSegmentedButton(frame, values=list(GENDER_LABELS), variable=self.gender))
        allowed = (frame.register(lambda s: re.fullmatch(r"[\d-]{0,10}", s) is not None), "%P")
        self.age_entry = ctk.CTkEntry(frame, placeholder_text="1984-01", width=160,
                                      validate="key", validatecommand=allowed)
        _option_row(frame, 2, "Wiek lub data", self.age_entry)
        ctk.CTkLabel(frame, text=records.AGE_HINT, text_color=("gray40", "gray60")).grid(
            row=3, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 6))

    def _company_options(self, frame):
        """REGON length switch."""
        _option_row(frame, 0, "REGON", ctk.CTkSegmentedButton(frame, values=list(REGON_LABELS), variable=self.regon))

    def _bank_options(self, frame):
        """Card brand switch."""
        _option_row(frame, 0, "Karta", ctk.CTkSegmentedButton(frame, values=list(CARD_LABELS), variable=self.card))

    def copy(self, value: str):
        """Put ``value`` on the system clipboard."""
        self.clipboard_clear()
        self.clipboard_append(value)
        self.set_status(f"Skopiowano: {value}")

    def set_status(self, text: str, error: bool = False):
        """Show ``text`` in the status line, in red when ``error`` is set."""
        self.status.configure(text=text, text_color="#d64545" if error else ("gray30", "gray70"))


def main():
    """Entry point for ``argus`` / ``make run``."""
    ctk.set_appearance_mode("system")
    App().mainloop()


if __name__ == "__main__":
    main()
