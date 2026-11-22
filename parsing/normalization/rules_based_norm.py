import re

# Define vowels and consonants (for historical Swedish)
vowel = "aouåeiyäöAEIOUYÄÖ"
cons = "bcdfghjklmnpqrstvwxzBCDFGHJKLMNPQRSTVWXZ"

def normalize_historical_swedish(line):
    # 1) qvarnar -> kvarnar
    line = re.sub(r"qv", "kv", line, flags=re.IGNORECASE)

    # 2) hvar, hvad, wore -> var, vad, vore
    line = re.sub(r"^(hv|w)", "v", line, flags=re.IGNORECASE)

    # 3) hafuer, gifuess, lefuer, haffuer, hafva -> haver, givess, lever, haver, hava
    line = re.sub(rf"([{vowel}])ff?[uv]([{vowel}])", r"\1v\2", line, flags=re.IGNORECASE)

    # 4) fördärfvat, blijfva -> fördärvat, bliva
    line = re.sub(r"j?fv", "v", line, flags=re.IGNORECASE)

    # 5) een, saaken, söökia -> en, saken, sökia
    line = re.sub(rf"([{vowel}])\1", r"\1", line, flags=re.IGNORECASE)

    # 6) äh, ahntaga -> är, antaga
    line = re.sub(rf"([{vowel}])h([nr])", r"\1\2", line, flags=re.IGNORECASE)

    # 7) uthskickadhe, uthfhöra, sägher -> utskickade, utföra, säger
    if not 'het' in line:
        line = re.sub(rf"([d|t|f|g|k|])h", r"\1", line, flags=re.IGNORECASE)

    # 8) elliest, bevilliat -> eljest, beviljat
    line = re.sub(r"lli([ae])", r"lj\1", line, flags=re.IGNORECASE)

    # 9) varidt -> varit, födt -> fött, dt -> t
    line = re.sub(r"födt", "fött", line)
    line = re.sub(r"dt", "t", line)

    # 10) dömbt, dömbdes, benämbdh -> dömt, dömdes, benämnd
    line = re.sub(r"m[bp]t", "mt", line)
    line = re.sub(r"m[bp]d", "mnd", line)

    # 11) slogz, skötz -> slogs, sköts
    line = re.sub(r"z", "s", line)

    # 12) försöria(s) -> försörja(s)
    line = re.sub(r"([^a])ria([^t])", r"\1rja\2", line)

    # 13) vijka, bevijsa, blijva -> vika, bevisa, bliva
    line = re.sub(r"iji", "j", line)
    line = re.sub(r"ij", "i", line)

    # 14) häfdar -> hävdar
    line = re.sub(rf"([{vowel}])fd", r"\1vd", line)

    # 15) föregaf -> föregav
    line = re.sub(r"gaff?($|\s)", r"gav\1", line)

    # 16) blef -> blev
    line = re.sub(r"eff?($|\s)", r"ev\1", line)

    # 17) affsagt -> avsagt
    line = re.sub(r"^([Aa])ff", r"\1v", line)

    # 18) schall -> skall
    line = re.sub(r"sch", "sk", line)

    # 19) kiöpt -> köpt
    line = re.sub(r"kiö", "kö", line)

    # 20) prætenderat -> pretenderat
    line = re.sub(r"(æ|ae)", "e", line)

    # 21) ehrläggia, sökia -> erlägga, söka
    line = re.sub(r"(gg|k)ia", r"\1a", line)

    # 22) huilken -> vilken
    line = re.sub(r"hui", "vi", line)

    # 23) avsachnat -> avsaknat (restricted to succeeding consonants)
    line = re.sub(rf"ch([{cons}])", r"k\1", line)

    # 24) giort -> gjort
    line = re.sub(r"^giort($|\s)", r"gjort\1", line)

    # 25) voro -> vore
    line = re.sub(r"^voro($|\s)", r"vore\1", line)

    # 26) effter, offta -> efter, ofta
    line = re.sub(r"fft", "ft", line)

    # 27) givess, avdömass, prövass -> gives, avdömas, prövas
    line = re.sub(r"(ea)ss($|\s)", r"\1s\1", line)

    # 28) af -> av
    line = re.sub(r"([Aa])f([^ft])", r"\1v\2", line)

    # 29) iemte, sielf -> jämte, själf
    line = re.sub(r"ie(l|r|mt)", r"jä\1", line)
    line = re.sub(r"Ie(l|r|mt)", r"Jä\1", line)
    line = re.sub(r"(T|t)ien", r"\1jän", line)

    #30)  "af"-> "av"
    line = re.sub(r"^af($|\s)", r"av\1", line, flags=re.IGNORECASE)

    #31)  fw  -> v  "blifwa": "bliva",
    line = re.sub(r"(fw)", "v", line, flags=re.IGNORECASE)

    return line

if __name__=="__main__":
    line = "de"
    print(normalize_historical_swedish(line))