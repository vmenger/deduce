"""
Creates streets_long.txt from streets_manual.txt by applying combinations of
replacements.

As a separate script to improve startup time, needs to be rerun when changes in this
script or in any of the street source lists are made.
"""

from deduce.utils import str_variations

prefix_mapping = {
    r"\bAbraham\b": ["Abraham", "Abr.", "abr."],
    r"\bAdmiraal\b": ["Admiraal", "Adm.", "adm."],
    r"\bAlbert\b": ["Albert", "Alb.", "alb."],
    r"\bBurgemeester\b": ["Burgemeester", "Burg.", "burg."],
    r"\bChris\b": ["Chris", "Chr.", "chr."],
    r"\bCommissaris\b": ["Commissaris", "Comm.", "comm."],
    r"\bDominee\b": ["Dominee", "Ds.", "ds."],
    r"\bDoctor\b": ["Doctor", "Dr.", "dr."],
    r"\bDokter\b": ["Dokter", "Dr.", "dr."],
    r"\bDoctorandus\b": ["Doctorandus", "Drs.", "drs."],
    r"\bFamilie\b": ["Familie", "Fam.", "fam."],
    r"\bGebroeders\b": ["Gebroeders", "Gebr.", "gebr.", "Gebrs.", "gebrs."],
    r"\bGeneraal\b": ["Generaal", "Gen.", "gen."],
    r"\bHertog\b": ["Hertog", "Hert.", "hert."],
    r"\bIngenieur\b": ["Ingenieur", "Ir.", "ir.", "Ing.", "ing."],
    r"\bJacobus\b": ["Jacobus", "Jac.", "jac."],
    r"\bJacob\b": ["Jacobus", "Jac.", "jac."],
    r"\bJacqueline\b": ["Jacqueline", "Jacq.", "jacq."],
    r"\bJonkhkeer\b": ["Jonkhkeer", "Jhr.", "jhr."],
    r"\bJonkvrouw\b": ["Jonkvrouw", "Jkvr.", "jkvr."],
    r"\bJohan\b": ["Johan", "Joh.", "joh."],
    r"\bKardinaal\b": ["Kardinaal", "Kard.", "kard."],
    r"\bKolonel\b": ["Kolonel", "Kol.", "kol."],
    r"\bKoningin\b": ["Koningin", "Kon.", "kon."],
    r"\bKoning\b": ["Koning", "Kon.", "kon."],
    r"\bMajoor\b": ["Majoor", "Maj.", "maj."],
    r"\bMevrouw\b": ["Mevrouw", "Mevr.", "mevr."],
    r"\bMinister\b": ["Minister", "Min.", "min."],
    r"\bMeester\b": ["Meester", "Mr.", "mr."],
    r"\bMonseigneur\b": ["Monseigneur", "Mgr.", "mgr."],
    r"\bPrinses\b": ["Prinses", "Pr.", "pr."],
    r"\bProfessor\b": ["Professor", "Prof.", "prof."],
    r"\bRector\b": ["Rector", "Rect.", "rect."],
    r"\bSecretaris\b": ["Secretaris", "Secr.", "secr."],
    r"\bSenior\b": ["Senior", "Sr.", "sr."],
    r"\bSint\b": ["Sint", "sint", "St.", "st."],
    r"\bTheo\b": ["Theo", "Th.", "th."],
    r"\bVeldmaarschalk\b": ["Veldmaarschalk", "Veldm.", "Veldm"],
    r"\bVicaris\b": ["Vicaris", "Vic.", "vic."],
    r"\bZuster\b": ["Zuster", "Zr.", "zr."],
}

prop_mapping = {
    r"\baan\b": ["Aan", "aan"],
    r"\bachter\b": ["Achter", "achter"],
    r"\band\b": ["And", "and"],
    r"\bbie\b": ["Bie", "bie"],
    r"\bbij\b": ["Bij", "bij"],
    r"\bbinnenzijde\b": ["Binnenzijde", "binnenzijde", "BZ", "Bz", "bz"],
    r"\bbuitenzijde\b": ["Buitenzijde", "buitenzijde", "BZ", "Bz", "bz"],
    r"\bda\b": ["Da", "da"],
    r"\bde\b": ["De", "de"],
    r"\bdel\b": ["Del", "del"],
    r"\bden\b": ["Den", "den"],
    r"\bder\b": ["Der", "der"],
    r"\bdes\b": ["Des", "des"],
    r"\bdi\b": ["Di", "di"],
    r"\bdie\b": ["Die", "die"],
    r"\bdoor\b": ["Door", "door"],
    r"\bdu\b": ["Du", "du"],
    r"\bein\b": ["Ein", "ein"],
    r"\ben\b": ["En", "en"],
    r"\bfan\b": ["Fan", "fan"],
    r"\bge\b": ["Ge", "ge"],
    r"\bgen\b": ["Gen", "gen"],
    r"\bhet\b": ["Het", "het", "'T", "'t", "`T", "`t", "T", "t"],
    r"\bin\b": ["In", "in"],
    r"\bis\b": ["Is", "is"],
    r"\bit\b": ["It", "it", "Het", "het", "'T", "'t", "`T", "`t", "T", "t"],
    r"\bla\b": ["La", "la"],
    r"\blangs\b": ["Langs", "langs"],
    r"\ble\b": ["Le", "le"],
    r"\bnaar\b": ["Naar", "naar"],
    r"\bnabij\b": ["Nabij", "nabij"],
    r"\boan\b": ["Oan", "oan"],
    r"\bof\b": ["Of", "of"],
    r"\bom\b": ["Om", "om"],
    r"\bonder\b": ["Onder", "onder"],
    r"\bop\b": ["Op", "op"],
    r"\bover\b": ["Over", "over"],
    r"\bsur\b": ["Sur", "sur"],
    r"\bte\b": ["Te", "te"],
    r"\bten\b": ["Ten", "ten"],
    r"\bter\b": ["Ter", "ter"],
    r"\btot\b": ["Tot", "tot"],
    r"\btusschen\b": ["Tusschen", "tusschen"],
    r"\btussen\b": ["Tussen", "tussen"],
    r"\but\b": ["Ut", "ut"],
    r"\buten\b": ["Uten", "uten"],
    r"\bvan\b": ["Van", "van", "v.", "V."],
    r"\bvon\b": ["Von", "von"],
    r"\bvoor\b": ["Voor", "voor"],
}

windrichting_mapping = {
    r"\bNoord$": ["Noord", "noord", "N"],
    r"\bOost$": ["Oost", "oost", "O"],
    r"\bZuid$": ["Zuid", "zuid", "Z"],
    r"\bWest$": ["West", "west", "W"],
    r"NZ$": ["N.Z.", "N.z.", "n.z.", "Noordzijde", "noordzijde", ""],
    r"OZ$": ["O.Z.", "O.z.", "o.z.", "Oostzijde", "oostzijde", ""],
    r"ZZ$": ["Z.Z.", "Z.z.", "z.z.", "Zuidzijde", "zuidzijde", ""],
    r"WZ$": ["W.Z.", "W.z.", "w.z.", "Westzijde", "westzijde", ""],
    r"NO$": ["N.O.", "N.o.", "n.o.", ""],
    r"NW$": ["N.W.", "N.w.", "n.w.", ""],
    r"ZO$": ["Z.O.", "Z.o.", "z.o.", ""],
    r"ZW$": ["Z.W.", "Z.w.", "z.w.", ""],
}

suffix_mapping = {
    r"dreef$": ["dreef", "drf"],
    r"gracht$": ["gracht", "gr"],
    r"hof$": ["hof", "hf"],
    r"laan$": ["laan", "ln"],
    r"markt$": ["markt", "mrkt"],
    r"pad$": ["pad", "pd"],
    r"park$": ["park", "prk"],
    r"plantsoen$": ["plantsoen", "plnts", "pltsn"],
    r"plein$": ["plein", "pln"],
    r"singel$": ["singel", "sngl"],
    r"steeg$": ["steeg", "stg", "st"],
    r"straat$": ["straat", "str"],
    r"weg$": ["weg", "wg"],
}

loc_mapping = {
    r"\bAcker\b": ["Acker", "acker"],
    r"\bAkker\b": ["Akker", "akker"],
    r"\bBoulevard\b": ["Boulevard", "boulevard"],
    r"\bDijk\b": ["Dijk", "dijk"],
    r"\bDreef\b": ["Dreef", "dreef"],
    r"\bDwarsweg\b": ["Dwarsweg", "dwarsweg"],
    r"\bDyk\b": ["Dyk", "dyk"],
    r"\bErf\b": ["Erf", "erf"],
    r"\bHeide\b": ["Heide", "heide"],
    r"\bHof\b": ["Hof", "hof"],
    r"\bKade\b": ["Kade", "kade"],
    r"\bKanaal\b": ["Kanaal", "kanaal"],
    r"\bLaan\b": ["Laan", "laan"],
    r"\bPad\b": ["Pad", "pad"],
    r"\bPark\b": ["Park", "park"],
    r"\bPlantsoen\b": ["Plantsoen", "plantsoen"],
    r"\bPlein\b": ["Plein", "plein"],
    r"\bReed\b": ["Reed", "reed"],
    r"\bRotonde\b": ["Rotonde", "rotonde"],
    r"\bSloot\b": ["Sloot", "sloot"],
    r"\bSluis\b": ["Sluis", "sluis"],
    r"\bSteeg\b": ["Steeg", "steeg"],
    r"\bStraat\b": ["Straat", "straat"],
    r"\bTunnel\b": ["Tunnel", "tunnel"],
    r"\bWal\b": ["Wal", "wal"],
    r"\bWeg\b": ["Weg", "weg"],
    r"\bWei\b": ["Wei", "wei"],
    r"\bWijk\b": ["Wijk", "wijk"],
    r"\bVen\b": ["Ven", "ven"],
}

punct_mapping = {r"\.": [".", ""], "-": ["-", "", " "]}

spell_mapping = {
    "y": ["y", "ij"],
    "Y": ["Y", "IJ"],
    "ij": ["ij", "y"],
    "IJ": ["IJ", "Y"],
}

mappings = [
    prefix_mapping,
    prop_mapping,
    windrichting_mapping,
    suffix_mapping,
    loc_mapping,
    punct_mapping,
    spell_mapping,
]


if __name__ == "__main__":

    with open("streets_manual.txt", "r") as file:
        streets = set(file.read().split("\n"))

    with open("street_exceptions.txt", "r") as file:
        streets_exceptions = set(file.read().split("\n"))

    streets.difference_update(streets_exceptions)

    for mapping in mappings:

        to_add = []

        for street in streets:
            to_add += str_variations(street, mapping)

        streets.update(to_add)

    streets = {s.strip() for s in streets}

    with open("streets_long.txt", "w") as file:
        file.write("\n".join(sorted(list(streets))))
