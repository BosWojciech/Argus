"""Small hand-picked lists used when the generated database is not available.

Run ``make data`` to build the full database from open data instead.
"""

FIRST_NAMES_FEMALE = [
    "Anna", "Maria", "Katarzyna", "Małgorzata", "Agnieszka", "Barbara", "Ewa",
    "Krystyna", "Elżbieta", "Zofia", "Joanna", "Magdalena", "Monika", "Aleksandra",
    "Natalia", "Julia", "Zuzanna", "Hanna", "Maja", "Lena", "Alicja", "Oliwia",
    "Wiktoria", "Amelia", "Iga", "Blanka", "Eliza", "Malwina", "Aniela", "Inga",
]

FIRST_NAMES_MALE = [
    "Piotr", "Krzysztof", "Andrzej", "Tomasz", "Paweł", "Jan", "Michał", "Marcin",
    "Jakub", "Adam", "Łukasz", "Mateusz", "Wojciech", "Marek", "Grzegorz", "Kamil",
    "Szymon", "Filip", "Antoni", "Franciszek", "Stanisław", "Józef", "Bartosz",
    "Dawid", "Konrad", "Igor", "Oskar", "Wiktor", "Leon", "Aleksander",
]

# Surnames in masculine form; feminine form is derived by ``feminine_surname``.
SURNAMES = [
    "Nowak", "Kowalski", "Wiśniewski", "Wójcik", "Kowalczyk", "Kamiński",
    "Lewandowski", "Zieliński", "Szymański", "Woźniak", "Dąbrowski", "Kozłowski",
    "Jankowski", "Mazur", "Kwiatkowski", "Krawczyk", "Piotrowski", "Grabowski",
    "Nowakowski", "Pawłowski", "Michalski", "Nowicki", "Adamczyk", "Dudek",
    "Zając", "Wieczorek", "Jabłoński", "Król", "Majewski", "Olszewski",
    "Jaworski", "Wróbel", "Malinowski", "Pawlak", "Witkowski", "Walczak",
    "Stępień", "Górski", "Rutkowski", "Michalak", "Sikora", "Ostrowski",
    "Baran", "Duda", "Szewczyk", "Tomaszewski", "Pietrzak", "Marciniak",
    "Wróblewski", "Zalewski", "Jakubowski", "Jasiński", "Zawadzki", "Sadowski",
]


def feminine_surname(surname: str) -> str:
    """Turn ``-ski/-cki/-dzki`` into ``-ska/-cka/-dzka``; other surnames are unisex."""
    return surname[:-1] + "a" if surname.endswith("ki") else surname


CITIES = [
    "Warszawa", "Kraków", "Łódź", "Wrocław", "Poznań", "Gdańsk", "Szczecin",
    "Bydgoszcz", "Lublin", "Białystok", "Katowice", "Gdynia", "Częstochowa",
    "Radom", "Rzeszów", "Toruń", "Sosnowiec", "Kielce", "Gliwice", "Olsztyn",
    "Zabrze", "Bielsko-Biała", "Bytom", "Zielona Góra", "Rybnik", "Ruda Śląska",
    "Opole", "Tychy", "Gorzów Wielkopolski", "Dąbrowa Górnicza", "Elbląg",
    "Płock", "Wałbrzych", "Włocławek", "Tarnów", "Chorzów", "Koszalin",
    "Kalisz", "Legnica", "Grudziądz", "Słupsk", "Jaworzno", "Jastrzębie-Zdrój",
    "Nowy Sącz", "Jelenia Góra", "Siedlce", "Mysłowice", "Konin", "Piła",
    "Wola Kiedrzyńska", "Zakopane", "Sopot", "Leszno", "Przemyśl",
]

STREETS = [
    "Polna", "Leśna", "Słoneczna", "Krótka", "Szkolna", "Ogrodowa", "Lipowa",
    "Brzozowa", "Łąkowa", "Kwiatowa", "Sosnowa", "Kościelna", "Akacjowa",
    "Parkowa", "Zielona", "Kolejowa", "Sportowa", "Długa", "Krakowska",
    "Warszawska", "Mickiewicza", "Słowackiego", "Kościuszki", "Sienkiewicza",
    "Piłsudskiego", "Kopernika", "Chopina", "Prusa", "Reymonta", "Konopnickiej",
    "Żeromskiego", "Jana Pawła II", "3 Maja", "11 Listopada", "Wolności",
    "Częstochowska", "Wrocławska", "Poznańska", "Gdańska", "Grunwaldzka",
    "Wiejska", "Wspólna", "Spacerowa", "Klonowa", "Jesionowa",
]

# Bank code (first three digits of the settlement number) -> bank name.
BANKS = {
    "102": "PKO BP",
    "105": "ING Bank Śląski",
    "109": "Santander Bank Polska",
    "114": "mBank",
    "116": "Bank Millennium",
    "124": "Bank Pekao",
    "132": "Bank Pocztowy",
    "154": "BOŚ Bank",
    "160": "BNP Paribas Bank Polska",
    "187": "Nest Bank",
    "193": "Bank Polskiej Spółdzielczości",
    "249": "Alior Bank",
    "291": "Aion Bank",
}
