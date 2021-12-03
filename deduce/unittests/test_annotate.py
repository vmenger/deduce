import unittest

from deduce import annotate
from deduce.tokenizer import tokenize_split, tokenize
from deduce.utilcls import Token, TokenGroup, AnnotationError
from deduce.utility import to_text


class TestAnnotateMethods(unittest.TestCase):
    def test_annotate_names(self):
        text = (
            u"Dit is stukje tekst met daarin de naam Jan Jansen. De patient J. Jansen "
            u"(e: j.jnsen@email.com, t: 06-12345678) is 64 jaar oud en woonachtig in Utrecht. Hij werd op 10 "
            u"oktober door arts Peter de Visser ontslagen van de kliniek van het UMCU."
        )
        tokens = tokenize_split(text)
        start_ix = 0
        for i, token in enumerate(tokens):
            end_ix = start_ix + len(token)
            tokens[i] = Token(start_ix, end_ix, token, '')
        annotated_names = annotate.annotate_names(
            tokens,
            patient_first_names="Jan",
            patient_surname="Jansen",
            patient_initial="",
            patient_given_name="",
        )
        expected_text = (
            "Dit is stukje tekst met daarin de naam <VOORNAAMPAT Jan> <ACHTERNAAMPAT Jansen>. De "
            "<PREFIXNAAM patient J>. <ACHTERNAAMPAT Jansen> (e: j.jnsen@email.com, t: 06-12345678) is 64 "
            "jaar oud en woonachtig in Utrecht. Hij werd op 10 oktober door arts <VOORNAAMONBEKEND "
            "Peter> <INTERFIXNAAM de Visser> ontslagen van de kliniek van het UMCU."
        )
        self.assertEqual(expected_text, to_text(annotated_names))

    def test_duplicated_names(self):
        text = (
            "Dank je <VOORNAAMONBEKEND Peter> van Gonzalez. Met vriendelijke groet, "
            "<VOORNAAMONBEKEND Peter> van Gonzalez"
        )
        annotated_names = annotate.annotate_names_context(tokenize(text))
        expected_text = (
            "Dank je <INTERFIXACHTERNAAM <VOORNAAMONBEKEND Peter> van Gonzalez>. "
            "Met vriendelijke groet, <INTERFIXACHTERNAAM <VOORNAAMONBEKEND Peter> van Gonzalez>"
        )
        self.assertEqual(expected_text, to_text(annotated_names))

    def test_duplicated_names_longer(self):
        text = (
            "Dank je <VOORNAAMONBEKEND Peter> van Gonzalez. Met vriendelijke groet, "
            "<VOORNAAMONBEKEND Peter> van Gonzalez. Er is ook een Pieter de Visser hier"
        )
        annotated_names = annotate.annotate_names_context(tokenize(text))
        expected_text = (
            "Dank je <INTERFIXACHTERNAAM <VOORNAAMONBEKEND Peter> van Gonzalez>. "
            "Met vriendelijke groet, <INTERFIXACHTERNAAM <VOORNAAMONBEKEND Peter> van Gonzalez>. "
            "Er is ook een Pieter de Visser hier"
        )
        self.assertEqual(expected_text, to_text(annotated_names))

    def test_duplicated_names_triple(self):
        text = (
            "Dank je <VOORNAAMONBEKEND Peter> van Gonzalez. Met vriendelijke groet, "
            "<VOORNAAMONBEKEND Peter> van Gonzalez. Er is ook een andere <VOORNAAMONBEKEND Peter> van Gonzalez hier"
        )
        annotated_names = annotate.annotate_names_context(tokenize(text))
        expected_text = (
            "Dank je <INTERFIXACHTERNAAM <VOORNAAMONBEKEND Peter> van Gonzalez>. "
            "Met vriendelijke groet, <INTERFIXACHTERNAAM <VOORNAAMONBEKEND Peter> van Gonzalez>. "
            "Er is ook een andere <INTERFIXACHTERNAAM <VOORNAAMONBEKEND Peter> van Gonzalez> hier"
        )
        self.assertEqual(expected_text, to_text(annotated_names))

    def test_simple_context(self):
        text = "V. <ACHTERNAAMONBEKEND Menger>"
        annotated_names = annotate.annotate_names_context(tokenize(text))
        expected_text = "<INITIAAL V. <ACHTERNAAMONBEKEND Menger>>"
        self.assertEqual(expected_text, to_text(annotated_names))

    def test_coordinating_nexus(self):
        text = """We hebben o.a. gesproken om een verwijsbrief te verzorgen naar Ajax, <PREFIXNAAM PJ> en Pieter"""
        tokens = tokenize(text)
        annotated_names = annotate.annotate_names_context(tokens)
        annotated_text = to_text(annotated_names)
        expected_text = "We hebben o.a. gesproken om een verwijsbrief te verzorgen naar Ajax, " \
                        "<MEERDEREPERSONEN <PREFIXNAAM PJ> en Pieter>"
        self.assertEqual(expected_text, annotated_text)

    def test_annotate_initials(self):
        parts = ['C', '.', ' ', 'geeft', ' ', 'aan', ' ', 'dood', ' ', 'te', ' ', 'willen', '.', ' ', 'C', '.', ' ',
                 'tot', ' ', 'op', ' ', 'nu', ' ', 'blij']
        start_ix = 0
        tokens = []
        for part in parts:
            tokens.append(Token(start_ix, start_ix + len(part), part, ''))
            start_ix = start_ix + len(part)
        annotated_names = annotate.annotate_names(
            tokens,
            patient_first_names="Peter Charles",
            patient_surname="de Jong",
            patient_initial="PC",
            patient_given_name="Charlie",
        )
        '''expected_text = (
            "<INITIAALPAT C.> geeft aan dood te willen. <INITIAALPAT C.> tot op nu blij"
        )'''
        # noinspection PyTypeChecker
        expected = [TokenGroup(tokens[:2], 'INITIAALPAT')] + tokens[2:14] \
                   + [TokenGroup(tokens[14:16], 'INITIAALPAT')] + tokens[16:]
        self.assertEqual(expected, annotated_names)

    def test_annotate_initials_attached(self):
        patient_first_names = "Nicholas David"
        patient_initials = "ND"
        patient_surname = "de Jong"
        patient_given_name = "Niek"
        tokens = ['Toegangstijd', ':', ' ', 'N', '.', 'v', '.', 't', '.']
        start_ix = 0
        for i, token in enumerate(tokens):
            tokens[i] = Token(start_ix, start_ix + len(token), token, '')
            start_ix = start_ix + len(token)
        annotated_names = annotate.annotate_names(
            tokens,
            patient_first_names=patient_first_names,
            patient_surname=patient_surname,
            patient_initial=patient_initials,
            patient_given_name=patient_given_name,
        )
        # expected_text = "Toegangstijd: <INITIAALPAT N.>v.t."
        expected = tokens[:3] + [TokenGroup(tokens[3:5], 'INITIAALPAT')] + tokens[5:]
        self.assertEqual(expected, annotated_names)

    def test_annotate_address_no_number(self):
        text = "I live in Havikstraat since my childhood"
        tokens = tokenize(text)
        address = annotate.annotate_address(text, tokens)
        expected = tokens[:6] + [Token(10, 21, 'Havikstraat', 'LOCATIE')] + tokens[7:]
        self.assertEqual(expected, address)

    def test_annotate_address_with_number(self):
        text = "I live in Havikstraat 43 since my childhood"
        tokens = tokenize(text)
        address = annotate.annotate_address(text, tokens)
        expected = tokens[:6] + \
                   [TokenGroup([Token(10, 21, 'Havikstraat', ''), Token(21, 24, ' 43', '')], 'LOCATIE'),
                    Token(24, 25, ' ', '')] + \
                   tokens[8:]
        self.assertEqual(expected, address)

    def test_annotate_address_long_number(self):
        text = "I live in Havikstraat 4324598 since my childhood"
        tokens = tokenize(text)
        address = annotate.annotate_address(text, tokens)
        # noinspection PyTypeChecker
        expected = tokens[:6] + \
                   [TokenGroup([tokens[6], Token(21, 29, ' 4324598', '')], 'LOCATIE'), Token(29, 30, ' ', '')] + \
                   tokens[8:]
        self.assertEqual(
            expected, address
        )

    def test_coordinating_nexus_with_preceding_name(self):
        text = "Adalberto <ACHTERNAAMONBEKEND Koning> en Mariangela"
        tokens = tokenize(text)
        annotated = annotate.annotate_names_context(tokens)
        annotated_text = to_text(annotated)
        expected_text = "<MEERDEREPERSONEN <INITIAAL Adalberto <ACHTERNAAMONBEKEND Koning>> en Mariangela>"
        self.assertEqual(expected_text, annotated_text)

    def test_preserve_institution_casing(self):
        annotated_institutions_text = annotate.annotate_institution([Token(0, 8, 'Altrecht', '')])
        expected_text = [TokenGroup([Token(0, 8, 'Altrecht', '')], 'INSTELLING')]
        self.assertEqual(expected_text, annotated_institutions_text)

    def test_skip_mg(self):
        text = 'Hoofdstraat is mooi. (br)Lithiumcarbonaat 1600mg. Nog een zin'
        spans = tokenize(text)
        spans[0] = Token(0, len('Hoofdstraat'), 'Hoofdstraat', 'LOCATIE')
        annotated_postcodes_text = annotate.annotate_postcode(text, spans)
        self.assertTrue(all([not span.is_annotation() or span.text == 'Hoofdstraat'
                        for span in annotated_postcodes_text]))

    def test_annotate_postcode(self):
        text = 'Mijn postcode is 3500LX, toch?'
        spans = tokenize(text)
        annotated_postcodes_text = annotate.annotate_postcode(text, spans)
        expected_token = Token(text.index('3500LX'), text.index('3500LX') + len('3500LX'), '3500LX', 'LOCATIE')
        expected_text = spans[:5] + [Token(text.index('3') - 1, text.index('3'), ' ', ''), expected_token] + spans[7:]
        self.assertEqual(len(expected_text), len(annotated_postcodes_text))
        self.assertTrue(all([expected_text[i] == annotated_postcodes_text[i]
                             for i in range(len(expected_text)) if i != 6]))
        found_token = annotated_postcodes_text[6]
        self.assertTrue(expected_token.start_ix == found_token.start_ix
                        and expected_token.end_ix == found_token.end_ix
                        and expected_token.text == found_token.text
                        and expected_token.annotation == found_token.annotation)

    def test_annotate_altrecht(self):
        text = 'Opname bij xxx afgerond'
        start_ix = text.index('xxx')
        len_wd = len('altrecht')
        len_lun = len('lunetten')
        ann = 'INSTELLING'
        examples = [('altrecht lunetten',
                     [TokenGroup([Token(start_ix, start_ix + len_wd, 'altrecht', '')], ann),
                      Token(start_ix + len_wd, start_ix + len_wd + 1, ' ', ''),
                      Token(start_ix + len_wd + 1, start_ix + len_wd + 1 + len_lun, 'lunetten', '')]),
                    ('altrecht Lunetten',
                     [TokenGroup([Token(start_ix, start_ix + len_wd, 'altrecht', ''),
                                  Token(start_ix + len_wd, start_ix + len_wd + 1, ' ', ''),
                                  Token(start_ix + len_wd + 1, start_ix + len_wd + 1 + len_lun, 'Lunetten', '')],
                                 ann)]),
                    ('Altrecht lunetten',
                     [TokenGroup([Token(start_ix, start_ix + len_wd, 'Altrecht', '')], ann),
                      Token(start_ix + len_wd, start_ix + len_wd + 1, ' ', ''),
                      Token(start_ix + len_wd + 1, start_ix + len_wd + 1 + len_lun, 'lunetten', '')]),
                    ('Altrecht Lunetten',
                     [TokenGroup([Token(start_ix, start_ix + len_wd, 'Altrecht', ''),
                                  Token(start_ix + len_wd, start_ix + len_wd + 1, ' ', ''),
                                  Token(start_ix + len_wd + 1, start_ix + len_wd + 1 + len_lun, 'Lunetten', '')],
                                 ann)]),
                    ('Altrecht Lunetten Lunetten',
                     [TokenGroup([Token(start_ix, start_ix + len_wd, 'Altrecht', ''),
                                  Token(start_ix + len_wd, start_ix + len_wd + 1, ' ', ''),
                                  Token(start_ix + len_wd + 1, start_ix + len_wd + 1 + len_lun, 'Lunetten', ''),
                                  Token(start_ix + len_wd + 1 + len_lun, start_ix + len_wd + 1 + len_lun + 1, ' ', ''),
                                  Token(start_ix + len_wd + 2 + len_lun,
                                        start_ix + len_wd + 2 + 2 * len_lun,
                                        'Lunetten',
                                        '')],
                                 ann)]),
                    ('Altrecht Lunetten lunetten',
                     [TokenGroup([Token(start_ix, start_ix + len_wd, 'Altrecht', ''),
                                  Token(start_ix + len_wd, start_ix + len_wd + 1, ' ', ''),
                                  Token(start_ix + len_wd + 1, start_ix + len_wd + 1 + len_lun, 'Lunetten', '')],
                                 ann),
                      Token(start_ix + len_wd + 1 + len_lun, start_ix + len_wd + 1 + len_lun + 1, ' ', ''),
                      Token(start_ix + len_wd + 1 + len_lun + 1, start_ix + len_wd + 2 + len_lun * 2, 'lunetten', '')]),
                    ('ALtrecht Lunetten',
                     [TokenGroup([Token(start_ix, start_ix + len_wd, 'ALtrecht', ''),
                                  Token(start_ix + len_wd, start_ix + len_wd + 1, ' ', ''),
                                  Token(start_ix + len_wd + 1, start_ix + len_wd + 1 + len_lun, 'Lunetten', '')],
                                 ann)])]
        annotated = []
        tails = []
        for i, el in enumerate(examples):
            tokenized = tokenize(text.replace('xxx', el[0]))
            tails.append(tokenized[[i for i, t in enumerate(tokenized) if t.text == 'afgerond'][0] - 1:])
            annotated.append(annotate.annotate_institution(tokenized))
        # noinspection PyTypeChecker
        expected = [tokenize('Opname bij ') + el[1] + tails[i] for i, el in enumerate(examples)]
        self.assertEqual(expected, annotated)

    def test_annotate_context_keep_initial(self):
        text = 'Mijn naam is M <ACHTERNAAMONBEKEND Smid> de Vries'
        tokens = tokenize(text)
        annotated_context_names = annotate.annotate_names_context(tokens)
        annotated_text = to_text(annotated_context_names)
        expected = 'Mijn naam is <INTERFIXACHTERNAAM <INITIAAL M <ACHTERNAAMONBEKEND Smid>> de Vries>'
        self.assertEqual(expected, annotated_text)

    def test_keep_punctuation_after_date(self):
        text = 'Medicatie actueel	26-10, OXAZEPAM'
        annotated_dates = annotate.annotate_date(text, tokenize(text))
        expected = Token(text.index('2'), text.index('2') + 5, '26-10', 'DATUM')
        self.assertEqual(1, len([span for span in annotated_dates if span.is_annotation() and span.matches(expected)]))

    def test_two_dates_with_comma(self):
        text = '24 april, 1 mei: pt gaat geen constructief contact aan'
        annotated_dates = annotate.annotate_date(text, tokenize(text))
        found_annotations = [span for span in annotated_dates if span.is_annotation()]
        expected = [TokenGroup([Token(0, 3, '24 ', ''), Token(3, 8, 'april', '')], 'DATUM'),
                    TokenGroup([Token(10, 12, '1 ', ''), Token(12, 15, 'mei', '')], 'DATUM')]
        self.assertEqual(expected, found_annotations)

    def test_strip_match(self):
        token = annotate.strip_match_and_tag_(' peter', 10, '')
        self.assertEqual(Token(11, 16, 'peter', ''), token)

    def test_intersect(self):
        span = Token(0, 2, 'la', '')
        token = Token(0, 2, 'la', '')
        self.assertTrue(annotate.intersect_(span, token))

    def test_intersect_before(self):
        span = Token(2, 4, 'la', '')
        token = Token(0, 2, 'la', '')
        self.assertFalse(annotate.intersect_(span, token))

    def test_intersect_before_overlap(self):
        span = Token(2, 4, 'la', '')
        token = Token(1, 3, 'la', '')
        self.assertTrue(annotate.intersect_(span, token))

    def test_intersect_after_overlap(self):
        span = Token(2, 4, 'la', '')
        token = Token(3, 5, 'la', '')
        self.assertTrue(annotate.intersect_(span, token))

    def test_intersect_after(self):
        span = Token(0, 2, 'la', '')
        token = Token(2, 4, 'la', '')
        self.assertFalse(annotate.intersect_(span, token))

    def test_split_at_match_boundaries(self):
        spans = [Token(0, 2, 'la', ''), Token(2, 4, 'pa', ''), Token(4, 6, 'ra', '')]
        match = Token(1, 5, 'apar', 'LOCATIE')
        token_group = TokenGroup([Token(1, 2, 'a', ''), Token(2, 4, 'pa', ''), Token(4, 5, 'r', '')], 'LOCATIE')
        expected_spans = [Token(0, 1, 'l', ''), token_group, Token(5, 6, 'a', '')]
        new_spans = annotate.split_at_match_boundaries_(spans, match)
        self.assertEqual(expected_spans, new_spans)

    def test_split_at_match_boundaries_single(self):
        # 1 span that coincides with the match
        spans = [Token(0, 3, 'Raf', '')]
        match = Token(0, 3, 'Raf', 'LEGEND')
        expected_result = [Token(0, 3, 'Raf', 'LEGEND')]
        self.assertEqual(expected_result, annotate.split_at_match_boundaries_(spans, match))

    def test_split_at_match_boundaries_single_subset(self):
        # 1 span that is bigger than the match
        spans = [Token(0, 9, 'Raffaella', '')]
        match = Token(0, 3, 'Raf', 'LEGEND')
        expected_result = [Token(0, 3, 'Raf', 'LEGEND'), Token(3, 9, 'faella', '')]
        self.assertEqual(expected_result, annotate.split_at_match_boundaries_(spans, match))

    def test_split_at_match_boundaries_single_subset_tag(self):
        # 1 span that is bigger than the match, and the span is an annotation
        spans = [Token(0, 9, 'Raffaella', 'SINGER')]
        match = Token(0, 3, 'Raf', 'LEGEND')
        expected_result = [TokenGroup([match, Token(3, 9, 'faella', '')], 'SINGER')]
        self.assertEqual(expected_result, annotate.split_at_match_boundaries_(spans, match))

    def test_split_at_match_boundaries_two_annotations(self):
        # 2 spans that correspond to the match; one of the spans is an annotation
        # This should result in an error, as you can't find a raw text in "<TAG text> text" if you look at "texttext"
        spans = [Token(0, 9, 'Raffaella', 'SINGER'), Token(9, 10, ' ', ''), Token(10, 15, 'Carra', '')]
        match = TokenGroup([Token(0, 9, 'Raffaella', ''), Token(9, 10, ' ', ''), Token(10, 15, 'Carra', '')], 'LEGEND')
        self.assertRaisesRegex(
            AnnotationError,
            'The spans corresponding to the match belong to annotations',
            lambda: annotate.split_at_match_boundaries_(spans, match)
        )

    def test_annotate_pattern(self):
        pattern = 'pablo'
        text = 'this is a text about pablo picasso'
        spans = tokenize(text)
        annotation = 'PERSOON'
        start_ix = text.index(pattern)
        new_spans = annotate.insert_matches_([Token(start_ix, start_ix + len(pattern), pattern, annotation)], spans)
        expected = [span
                    if span.text != pattern
                    else Token(start_ix, start_ix + len(pattern), pattern, annotation)
                    for span in spans]
        self.assertEqual(expected, new_spans)

    def test_remove_mg(self):
        no_mg = annotate.remove_mg_([Token(0, 6, '3500mg', 'LOCATIE')])
        expected = [Token(0, 6, '3500mg', '')]
        self.assertEqual(expected, no_mg)

    def test_annotate_residence(self):
        spans = tokenize('Lage Vuursche')
        expected = [TokenGroup(spans, 'LOCATIE')]
        self.assertEqual(expected, annotate.annotate_residence(spans))

    def test_annotate_patient_number(self):
        spans = [Token(98, 109, '06-12345678', 'TELEFOONNUMMER')]
        expected_tokens = [Token(98, 101, '06-', ''),
                           Token(101, 108, '1234567', 'PATIENTNUMMER'),
                           Token(108, 109, '8', '')]
        expected = [TokenGroup(expected_tokens, 'TELEFOONNUMMER')]
        annotated = annotate.annotate_patient_number(' ' * 98 + '06-12345678', spans)
        self.assertEqual(expected, annotated)

    def test_annotate_email(self):
        address = 'j.jnsen@email.com'
        spans = tokenize(address)
        expected_text = '<URL ' + address + '>'
        annotated = annotate.annotate_email(address, spans)
        self.assertEqual(1, len(annotated))
        self.assertEqual(expected_text, annotated[0].as_text())

    def test_annotate_url_ignore_email(self):
        address = 'j.jnsen@email.com'
        spans = tokenize(address)
        expected_text = '<URL ' + address + '>'
        token_group = TokenGroup(spans, 'URL') # Previously annotated email address
        annotated = annotate.annotate_url(address, [token_group])
        self.assertEqual(1, len(annotated))
        self.assertEqual(expected_text, annotated[0].as_text())

if __name__ == "__main__":
    unittest.main()
