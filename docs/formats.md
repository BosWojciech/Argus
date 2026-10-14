# Value formats and checksums

All rules live in `src/argus/identifiers.py`. Each generator has a matching
`is_valid_*` validator, and the tests check every generated value with it.

## PESEL (11 digits)

`YYMMDD` + 3-digit serial + sex digit + check digit.

- Century is encoded in the month: 1800s +80, 1900s +0, 2000s +20, 2100s +40, 2200s +60.
- Sex digit (10th): even for women, odd for men.
- Check: weights `1,3,7,9,1,3,7,9,1,3`; `check = (10 - sum mod 10) mod 10`.

## Identity card (Dowód osobisty)

Three random uppercase letters, a check digit, five digits, e.g. `ABA300000`.
Letters count as `A=10 ... Z=35`; weights `7,3,1,9,7,3,1,7,3` over all nine
characters must give a sum divisible by 10.

## NIP (10 digits)

Weights `6,5,7,2,3,4,5,6,7`; `check = sum mod 11`. A remainder of 10 is not a
legal NIP, so such bodies are redrawn.

## REGON (9 or 14 digits)

- 9: weights `8,9,2,3,4,5,6,7`, `sum mod 11`, 10 becomes 0.
- 14: a valid 9-digit REGON + 4 digits (local unit) + check with weights
  `2,4,8,5,0,9,7,3,6,1,2,4,8`, same mod-11 rule.

## Bank account (IBAN)

`PL` + 2 check digits + 8-digit settlement number + 16 account digits (28 chars).

- Settlement number = 3-digit bank code + 4-digit branch + check digit
  (weights `3,9,7,1,3,9,7`, `(10 - sum mod 10) mod 10`).
- IBAN check digits: `98 - (BBAN + "PL00" as base-36 digits) mod 97`; the
  result passes the standard `mod 97 == 1` test.
- The settlement number is a real bank branch from the central bank's list,
  so the IBAN points at an existing bank and branch; the 16 account digits are
  random. The Bankowe tab shows the bank name; Zbiorcze shows only the IBAN.

## Payment card

16 digits passing Luhn. Prefix by brand: Visa `4`, MasterCard `51`-`55`,
any = Visa, MasterCard or `56`-`58`. CVC is 3 digits. Expiry is `MM/YY`,
1 to 96 months after the current month. The card and the bank account are
independent draws.

## VIN (17 characters)

WMI (real manufacturer prefix) + 5 descriptor chars + check character +
model-year char + plant char + 6-digit serial. Letters `I`, `O`, `Q` never
appear. The check character (position 9) follows ISO 3779: transliterate,
weights `8,7,6,5,4,3,2,10,0,9,8,7,6,5,4,3,2`, `sum mod 11`, 10 written as `X`.

## Registration plate

Two-letter district prefix, a space, five digits, e.g. `PO 12345`.

## Address

With the database: a real street in a real place with its real postal code,
drawn in proportion to the number of address points on it (so big cities come
up more often). The house number is random, from 1 to the highest number found
on that street. The street keeps its type prefix: `ul.`, `al.`, `pl.`, `os.`,
or none for names like `Rynek`.

With the fallback lists: postal code `NN-NNN`, a city and `ul. {street} {1-199}`
are drawn independently, so they do not form a real address.

## Names

With the database: given name and surname drawn from the PESEL registry lists
for the person's sex, weighted by how many people carry them (`Anna` is about
5% of women, rare names well under 0.01%). Surnames come from the separate
female and male lists, so the form always matches.

With the fallback lists: a short hand-picked list per sex; surnames are stored
in masculine form and `-ski/-cki/-dzki` becomes `-ska/-cka/-dzka` for women.
`Imię i nazwisko` is `"{Imię} {Nazwisko}"`.
