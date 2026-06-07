#!/usr/bin/env python3
"""
Python port of EvalDiac.java — evaluates Arabic diacritization accuracy
by comparing a reference file against a system-output file.

Mirrors the Java implementation's behavior (including its multi-reference
handling and edge-case quirks) so results are bit-identical to the Java
version.
"""
import argparse
import os
import re
import sys

DIAC_CODE_EMPTY = '0'
DIAC_CODE_FATHA = '1'
DIAC_CODE_KASRA = '2'
DIAC_CODE_DAMMA = '3'
DIAC_CODE_SUKUN = '4'
DIAC_CODE_FATHATAN = '5'
DIAC_CODE_KASRATAN = '6'
DIAC_CODE_DAMMATAN = '7'
DIAC_CODE_SHADDA = '9'
DIAC_CODE_SHADDA_FATHA = 'A'
DIAC_CODE_SHADDA_KASRA = 'B'
DIAC_CODE_SHADDA_DAMMA = 'C'
DIAC_CODE_SHADDA_FATHATAN = 'D'
DIAC_CODE_SHADDA_KASRATAN = 'E'
DIAC_CODE_SHADDA_DAMMATAN = 'F'
DIAC_CODE_SHADDA_SUKUN = 'G'

CH_DIAC_CODE_EMPTY = '0'
CH_DIAC_CODE_FATHA = '1'
CH_DIAC_CODE_KASRA = '2'
CH_DIAC_CODE_DAMMA = '3'
CH_DIAC_CODE_SUKUN = '4'
CH_DIAC_CODE_FATHATAN = '5'
CH_DIAC_CODE_KASRATAN = '6'
CH_DIAC_CODE_DAMMATAN = '7'
CH_DIAC_CODE_SHADDA = '9'
CH_DIAC_CODE_SHADDA_FATHA = 'A'
CH_DIAC_CODE_SHADDA_KASRA = 'B'
CH_DIAC_CODE_SHADDA_DAMMA = 'C'
CH_DIAC_CODE_SHADDA_FATHATAN = 'D'
CH_DIAC_CODE_SHADDA_KASRATAN = 'E'
CH_DIAC_CODE_SHADDA_DAMMATAN = 'F'
CH_DIAC_CODE_SHADDA_SUKUN = 'G'


def load_file(filename):
    if not os.path.isfile(filename):
        return None
    lines = []
    with open(filename, 'r', encoding='utf-8', newline=None) as f:
        for raw in f:
            line = raw.rstrip('\n').rstrip('\r')
            if len(line.strip()) == 0:
                continue
            lines.append(line)
    return lines


def remove_default_diac(s):
    out = s
    out = out.replace('َا', 'ا')           # fatha + alef -> alef
    out = out.replace('ِي', 'ي')           # kasra + ya   -> ya
    out = out.replace('ُو', 'و')           # damma + waw  -> waw
    out = out.replace('الْ', 'ال')  # alef-lam-sukun -> alef-lam

    out = out.replace('ْ', '')                       # drop sukun

    # the next six are no-ops in the Java code (replace X with X);
    # kept here so the behavior matches exactly.
    out = out.replace('َّ', 'َّ')
    out = out.replace('ِّ', 'ِّ')
    out = out.replace('ُّ', 'ُّ')
    out = out.replace('ًّ', 'ًّ')
    out = out.replace('ٍّ', 'ٍّ')
    out = out.replace('ٌّ', 'ٌّ')

    out = out.replace('اَ', 'ا')           # alef + fatha -> alef

    # consonant clustering normalisation
    out = out.replace('اِ', 'ا')           # alef + kasra -> alef
    out = out.replace('لِا', 'لا')  # lam-kasra-alef -> lam-alef

    out = out.replace('اً', 'ًا')     # alef + fathatan -> fathatan + alef

    return out


def get_diac_codes(s):
    out = []
    n = len(s)
    i = 0
    while i < n:
        ch = s[i]
        out.append(ch)
        diac = 0
        code = DIAC_CODE_EMPTY
        if i < n - 1:
            ch2 = s[i + 1]
            if ch2 == 'َ':       # fatha
                diac, code = 1, DIAC_CODE_FATHA
            elif ch2 == 'ِ':     # kasra
                diac, code = 1, DIAC_CODE_KASRA
            elif ch2 == 'ُ':     # damma
                diac, code = 1, DIAC_CODE_DAMMA
            elif ch2 == 'ْ':     # sukun
                diac, code = 1, DIAC_CODE_SUKUN
            elif ch2 == 'ً':     # fathatan
                diac, code = 1, DIAC_CODE_FATHATAN
            elif ch2 == 'ٍ':     # kasratan
                diac, code = 1, DIAC_CODE_KASRATAN
            elif ch2 == 'ٌ':     # dammatan
                diac, code = 1, DIAC_CODE_DAMMATAN
            elif ch2 == 'ّ':     # shadda
                diac, code = 1, DIAC_CODE_SHADDA
                if i < n - 2:
                    ch3 = s[i + 2]
                    if ch3 == 'َ':
                        diac, code = 2, DIAC_CODE_SHADDA_FATHA
                    elif ch3 == 'ِ':
                        diac, code = 2, DIAC_CODE_SHADDA_KASRA
                    elif ch3 == 'ُ':
                        diac, code = 2, DIAC_CODE_SHADDA_DAMMA
                    elif ch3 == 'ً':
                        diac, code = 2, DIAC_CODE_SHADDA_FATHATAN
                    elif ch3 == 'ٍ':
                        diac, code = 2, DIAC_CODE_SHADDA_KASRATAN
                    elif ch3 == 'ٌ':
                        diac, code = 2, DIAC_CODE_SHADDA_DAMMATAN
                    elif ch3 == 'ْ':
                        diac, code = 2, DIAC_CODE_SHADDA_SUKUN
        out.append(code)
        i += 1 + diac
    return ''.join(out)


def restore_words_from_diac_codes(s, no_case_ending):
    out = []
    n = len(s)
    end = (n + no_case_ending) // 2
    for i in range(end):
        ch = s[i * 2]
        out.append(ch)
        if (i * 2 + 1) >= n:
            break
        code = s[i * 2 + 1]
        if code == CH_DIAC_CODE_FATHA:
            out.append('َ')
        elif code == CH_DIAC_CODE_KASRA:
            out.append('ِ')
        elif code == CH_DIAC_CODE_DAMMA:
            out.append('ُ')
        elif code == CH_DIAC_CODE_SUKUN:
            out.append('ْ')
        elif code == CH_DIAC_CODE_FATHATAN:
            out.append('ً')
        elif code == CH_DIAC_CODE_KASRATAN:
            out.append('ٍ')
        elif code == CH_DIAC_CODE_DAMMATAN:
            out.append('ٌ')
        elif code == CH_DIAC_CODE_SHADDA:
            out.append('ّ')
        elif code == CH_DIAC_CODE_SHADDA_FATHA:
            out.append('ّ'); out.append('َ')
        elif code == CH_DIAC_CODE_SHADDA_KASRA:
            out.append('ّ'); out.append('ِ')
        elif code == CH_DIAC_CODE_SHADDA_DAMMA:
            out.append('ّ'); out.append('ُ')
        elif code == CH_DIAC_CODE_SHADDA_FATHATAN:
            out.append('ّ'); out.append('ً')
        elif code == CH_DIAC_CODE_SHADDA_KASRATAN:
            out.append('ّ'); out.append('ٍ')
        elif code == CH_DIAC_CODE_SHADDA_DAMMATAN:
            out.append('ّ'); out.append('ٌ')
        elif code == CH_DIAC_CODE_SHADDA_SUKUN:
            out.append('ّ'); out.append('ْ')
    return ''.join(out)


def normalize_word(t, normalize_common, normalize_hamza, remove_diac):
    s = t
    if normalize_common:
        s = s.replace('أ', 'ا')
        s = s.replace('إ', 'ا')
        s = s.replace('آ', 'ا')
        s = s.replace('ى', 'ي')
        s = s.replace('ة', 'ه')
        if normalize_hamza:
            s = s.replace('ؤ', 'ء')
            s = s.replace('ئ', 'ء')
    if remove_diac:
        for d in ('َ', 'ُ', 'ِ', 'ّ', 'ْ',
                  'ٌ', 'ً', 'ٍ', 'ـ'):
            s = s.replace(d, '')
    return s


_WS_RE = re.compile(r'\s+')


def java_split_ws(s):
    """Replicate Java's String.split("\\s+") behavior."""
    parts = _WS_RE.split(s)
    # Java's split with a positive default limit (0) removes trailing empty
    # strings but keeps a leading empty string when the input starts with a
    # match.
    while parts and parts[-1] == '':
        parts.pop()
    return parts


def calc_diac_accuracy(ref_file, sys_file, stem_accuracy, consonant_clustering):
    ref_lines = load_file(ref_file)
    sys_lines = load_file(sys_file)
    nof_ref_lines = len(ref_lines)
    nof_sys_lines = len(sys_lines)  # noqa: F841 (matches Java's unused var)

    show_diff_only = True
    nof_words = 0
    errors = 0
    errors2 = 0
    errors3 = 0
    nof_letters = 0
    correct_words = 0
    correct_letters = 0
    nof_multi_ref_words = 0

    i = 0
    for i in range(nof_ref_lines):
        r = ref_lines[i]
        s_line = sys_lines[i]

        fields_ref = java_split_ws(r)
        fields_sys = java_split_ws(s_line)

        if len(fields_ref) != len(fields_sys):
            errors += 1
            print(f"Error in number of words: Ref:{len(fields_ref)} Sys:{len(fields_sys)}, line:{i + 1}")
            continue

        for word_index in range(len(fields_sys)):
            nof_words += 1

            ref = fields_ref[word_index].strip()
            sys_word = fields_sys[word_index].strip()

            if consonant_clustering and word_index < len(fields_sys) - 1:
                if sys_word == 'عَنْ':         # عَنْ
                    if fields_ref[word_index + 1].startswith('ا'):
                        sys_word = 'عَنِ'      # عَنِ
                elif sys_word == 'مِنْ':       # مِنْ
                    if fields_ref[word_index + 1].startswith('ا'):
                        sys_word = 'مِنَ'      # مِنَ

            ref = remove_default_diac(ref)

            is_multi_ref_word = False
            got_multi_ref_correct = False
            curr_ref = ref

            ref_diac_codes = get_diac_codes(ref)
            ref_diac_codes_len = len(ref_diac_codes)

            sys_diac_codes = get_diac_codes(sys_word)
            sys_diac_codes_len = len(sys_diac_codes)

            if len(ref) > 1 and ref_diac_codes_len != sys_diac_codes_len:
                all_refs = ref.split('/')
            else:
                all_refs = [ref]

            if len(all_refs) > 1:
                nof_multi_ref_words += 1
                is_multi_ref_word = True

            for current_ref in all_refs:
                curr_ref = current_ref
                sys_word = remove_default_diac(sys_word)

                msg = ''

                ref_diac_codes = get_diac_codes(current_ref)
                ref_diac_codes_len = len(ref_diac_codes)

                sys_diac_codes = get_diac_codes(sys_word)
                sys_diac_codes_len = len(sys_diac_codes)

                diff = False
                nof_letters += ref_diac_codes_len // 2

                if ref_diac_codes_len == sys_diac_codes_len:
                    half = ref_diac_codes_len // 2
                    j = 0
                    while j < half:
                        if stem_accuracy and (j == half - 1):
                            break

                        if ref_diac_codes[j * 2] != sys_diac_codes[j * 2]:
                            errors3 += 1

                        ch1 = ref_diac_codes[j * 2]          # noqa: F841
                        d1 = ref_diac_codes[j * 2 + 1]
                        ch2 = sys_diac_codes[j * 2]          # noqa: F841
                        d2 = sys_diac_codes[j * 2 + 1]

                        next_ch1 = 'X'                       # noqa: F841
                        next_ch2 = 'Y'                       # noqa: F841
                        next_diac1 = 'Z'
                        next_diac2 = 'W'
                        if j < half - 1:
                            next_ch1 = ref_diac_codes[(j + 1) * 2]          # noqa: F841
                            next_diac1 = ref_diac_codes[(j + 1) * 2 + 1]
                            next_ch2 = sys_diac_codes[(j + 1) * 2]          # noqa: F841
                            next_diac2 = sys_diac_codes[(j + 1) * 2 + 1]

                        if d1 != d2:
                            if d1 == CH_DIAC_CODE_EMPTY:
                                d1 = d2
                            elif (d1 == CH_DIAC_CODE_SHADDA) and (d2 in (
                                CH_DIAC_CODE_SHADDA_FATHA,
                                CH_DIAC_CODE_SHADDA_KASRA,
                                CH_DIAC_CODE_SHADDA_DAMMA,
                                CH_DIAC_CODE_SHADDA_FATHATAN,
                                CH_DIAC_CODE_SHADDA_KASRATAN,
                                CH_DIAC_CODE_SHADDA_DAMMATAN,
                                CH_DIAC_CODE_SHADDA_SUKUN,
                            )):
                                d1 = d2

                        if (d1 != d2
                            and d1 == CH_DIAC_CODE_FATHATAN
                            and next_diac1 == CH_DIAC_CODE_EMPTY
                            and d2 == CH_DIAC_CODE_EMPTY
                            and next_diac2 == CH_DIAC_CODE_FATHATAN):
                            d1 = d2
                            j += 1
                            correct_letters += 1

                        if d1 == d2:
                            correct_letters += 1
                        else:
                            diff = True
                            if not show_diff_only:
                                msg += f' {ref_diac_codes[j * 2]}'

                        j += 1

                    if not diff:
                        correct_words += 1
                        print(current_ref)
                        if is_multi_ref_word:
                            got_multi_ref_correct = True
                        break
                    elif not is_multi_ref_word:
                        print(f"ERROR   Ref: {current_ref} Sys: {sys_word}")
                else:
                    errors2 += 1
                    print(f"Error in length of words: current_ref:{current_ref} Sys:{sys_word}, Line:{i + 1}, Word:{word_index + 1}")
                    break

                if not show_diff_only:
                    print(msg)

            if is_multi_ref_word and not got_multi_ref_correct:
                print(f"multi-ref word error: current_ref:{curr_ref} Sys:{sys_word}, Line:{i + 1}, Word:{word_index + 1}")

    i_final = nof_ref_lines  # Java prints the loop counter, which equals nofRefLines after the for loop completes
    if not stem_accuracy:
        wer = 100.0 - ((correct_words * 100.0) / nof_words) if nof_words else 0.0
        der = 100.0 - ((correct_letters * 100.0) / nof_letters) if nof_letters else 0.0
        msg = (f"lines:{i_final}/{nof_ref_lines}\twords:{nof_words}\tcorrectWords:{correct_words}\t"
               f"letters:{nof_letters}\tcorrectLetters:{correct_letters}\t"
               f"WER:{wer:.2f}%\tDER:{der:.2f}%\t"
               f"lineErrors:{errors}\twordErrors:{errors2}\tMultiRefWords:{nof_multi_ref_words}")
    else:
        wer = 100.0 - ((correct_words * 100.0) / nof_words) if nof_words else 0.0
        msg = (f"lines:{i_final}/{nof_ref_lines}\twords:{nof_words}\tcorrectWords:{correct_words}\t"
               f"letters:{nof_letters}\tcorrectLetters:{correct_letters}\t"
               f"WER:{wer:.2f}%\t"
               f"lineErrors:{errors}\twordErrors:{errors2}\tMultiRefWords:{nof_multi_ref_words}")
    print(msg)


def _str2bool(v):
    return str(v).lower() == 'true'


def main(argv):
    n = len(argv)
    if n == 0 or (n != 4 and n != 5 and n != 6):
        print("Evaluate the diacritization accuracy by comparing reference and system output files\n"
              "Usage: EvalDiac <--help|-h> <[-r|--ref] [refFilename]> <[-s|--sys] [sysFilename]> "
              "<[-t|--stemAccuracy] true|false> <[-c|--consonantClustering] true|false>")
        sys.exit(-1)

    for idx, a in enumerate(argv):
        print(f"arg:{idx} {a}")

    ref_file = ''
    sys_file = ''
    stem_accuracy = False
    consonant_clustering = False

    i = 0
    while i < n:
        arg = argv[i]
        if arg in ('--help', '-h'):
            print("Evaluate the diacritization accuracy by comparing reference and system output files\n"
                  "Usage: EvalDiac <--help|-h> <[-r|--ref] [refFilename]> <[-s|--sys] [sysFilename]> "
                  "<[-t|--stemAccuracy] true|false> <[-c|--consonantClustering] true|false>")
            sys.exit(-1)
        if arg in ('--ref', '-r'):
            if i < n - 1:
                ref_file = argv[i + 1]
                i += 1
        if arg in ('--sys', '-s'):
            if i < n - 1:
                sys_file = argv[i + 1]
                i += 1
        if arg in ('--stemAccuracy', '-t'):
            if i < n - 1:
                if argv[i + 1].lower() == 'true':
                    stem_accuracy = True
                i += 1
        if arg in ('--consonantClustering', '-c'):
            if i < n - 1:
                if argv[i + 1].lower() == 'true':
                    consonant_clustering = True
                i += 1
        i += 1

    print(f"\nReference filename:\t{ref_file}\nSystem filename:\t{sys_file}\n"
          f"stem Accuracy:\t\t{str(stem_accuracy).lower()}\nconsonant Clustering:\t{str(consonant_clustering).lower()}\n")

    if not os.path.isfile(ref_file) or not os.path.isfile(sys_file):
        print("Reference or system file not found!")
        sys.exit(-1)

    print("Evaluating Diacritization Accuracy...", file=sys.stderr)
    calc_diac_accuracy(ref_file, sys_file, stem_accuracy, consonant_clustering)
    print("Done!", file=sys.stderr)


if __name__ == '__main__':
    main(sys.argv[1:])
