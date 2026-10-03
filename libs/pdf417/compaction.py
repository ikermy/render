from itertools import chain
from functools import partial
from .data import CHARACTERS_LOOKUP, SWITCH_CODES, Submode
from .util import switch_base, to_base, chunks


# -- Number compaction mode ----------------------------------------------------


def compact_numbers(config, data, count):
    """Encodes data into code words using the Numbers compaction mode.

    Can encode: Digits 0-9, ASCII
    Rate compaction: 2.9 bytes per code word
    """

    def compact_chunk(chunk):
        number = "".join([chr(x) for x in chunk])
        value = int("1" + number)
        return to_base(value, 900)

    compacted_chunks = [compact_chunk(chunk) for chunk in chunks(data, size=44)]
    return chain(*compacted_chunks)


# -- Text compaction mode ------------------------------------------------------


def compact_text_interim(config, data, count):
    def exists_in_submode(char, submode):

        return char in CHARACTERS_LOOKUP and submode in CHARACTERS_LOOKUP[char]

    def get_submode(char):
        if char not in CHARACTERS_LOOKUP:
            raise ValueError("Cannot encode char: {}".format(char))

        submodes = CHARACTERS_LOOKUP[char].keys()

        preference = [Submode.LOWER, Submode.UPPER, Submode.MIXED, Submode.PUNCT]

        for submode in preference:
            if submode in submodes:
                return submode

        raise ValueError("Cannot encode char: {}".format(char))

    # By default, encoding starts with uppercase submode
    submode = Submode.UPPER
    codes = []
    encoding = config["encoding"]
    code13 = None
    code13_2 = None
    code27 = None
    code39 = None
    code42 = None
    code44 = None
    code45 = None
    code46 = None
    code46_2 = None
    code97 = False
    last_r = None
    last_r2 = None
    last_r3 = None
    small_in = None
    no10code = False
    withSignature = None
    try:
        code13 = bool(config["code13"])
    except:
        pass
    try:
        last_r = bool(config["last_r"])
    except:
        pass
    try:
        code13_2 = bool(config["code13_2"])
    except:
        pass
    try:
        last_r2 = bool(config["last_r2"])
    except:
        pass
    try:
        last_r3 = bool(config["last_r3"])
    except:
        pass
    try:
        code27 = bool(config["code27"])
    except:
        pass
    try:
        code39 = bool(config["code39"])
    except:
        pass
    try:
        code42 = bool(config["code42"])
    except:
        pass
    try:
        code44 = bool(config["code44"])
    except:
        pass
    try:
        code45 = bool(config["code45"])
    except:
        pass
    try:
        code46 = bool(config["code46"])
    except:
        pass
    try:
        code97 = bool(config["code97"])
    except:
        pass
    try:
        code46_2 = bool(config["code46_2"])
    except:
        pass
    try:
        small_in = bool(config["small_in"])
    except:
        pass
    try:
        no10code = bool(config["no10code"])
    except:
        pass
    try:
        withSignature = bool(config["withSignature"])
    except:
        pass

    # TODO this code переключение символов
    for idx, char in enumerate(data):
        # Do we need to switch submode?
        if small_in:
            if last_r3:
                try:
                    if char == 10 and data[idx + 1] == 13:
                        codes.extend([29, 15])
                        continue
                except:
                    pass
            if char == 10 and data[idx - 1] == 110:
                codes.extend([29, 15])
                continue
            if char == 100:
                codes.extend([27, 3])
                continue
            if char == 97 and not code97:
                codes.extend([27, 0])
                continue
            if char == 103:
                codes.extend([27, 6])
                continue
            if char == 95:
                codes.extend([29, 7])
                continue
            if char == 105:
                codes.extend([27, 8])
                continue
            if char == 110:
                submode = Submode.LOWER
                codes.extend([13])
                continue
            if char == 39:
                codes.extend([29, 28])
                continue

        if not small_in and code39:
            if char == 39:
                codes.extend([29, 28])
                continue
        if not small_in and code44:
            if char == 44:
                codes.extend([29, 13])
                continue
        if code45:
            if char == 45:
                codes.extend([29, 16])
                continue
        if code46:
            if char == 46:
                codes.extend([29, 17])
                continue
        if code46_2:
            if char == 46:
                codes.extend([28, 17])
                submode = Submode.MIXED
                continue
        if last_r:
            if char == 13 and len(data) == idx + 1:
                codes.extend([11, 29, 30, 0])
                break
        if last_r2:
            if char == 10 and len(data) == idx + 1:
                codes.extend([29])
                break
        if not no10code:
            if char == 10:
                try:
                    if data[idx + 1] != 13:
                        codes.extend([29, 15])
                        continue
                except:
                    codes.extend([29, 15])
                    continue
        if code13:
            if char == 13 and submode != Submode.MIXED:
                codes.extend([29, 11])
                continue
            if char == 13 and submode == Submode.MIXED:
                codes.extend([11, 28])
                submode = Submode.UPPER
                continue
        if code13_2:
            if char == 13 and submode != Submode.MIXED:
                codes.extend([29, 11])
                continue
            if char == 13 and submode == Submode.MIXED:
                codes.extend([11, 29])
                submode = Submode.UPPER
                continue
        if code13:
            if char == 13 and submode != Submode.MIXED:
                codes.extend([28, 11])
                continue
            if char == 13 and submode == Submode.MIXED:
                codes.extend([11, 28])
                submode = Submode.UPPER
                continue

        if count[3] > 0:
            if encoding == "902 913":
                if char == 64:
                    codes.extend([29, 3])
                    continue
            else:
                if char == 64:
                    codes.extend([28, 25, 3, 15])
                    break
            count[3] -= 1
        else:
            if char == 64 and submode not in [Submode.PUNCT, Submode.MIXED]:
                codes.extend([29, 3])
                continue
            elif char == 64 and submode == Submode.PUNCT:
                codes.extend([3])
                continue
            elif char == 64:
                codes.extend([25, 3])
                submode = Submode.PUNCT
                continue
        if code42:
            if char == 42 and data[idx - 1] in [45]:
                codes.extend([22])
                continue
        if withSignature:
            if char == 60 and submode != Submode.PUNCT and Submode.MIXED != submode:
                codes.extend([29, 1])
                continue
            if char == 45 and submode not in [Submode.PUNCT, Submode.MIXED]:
                codes.extend([28, 16])
                submode = Submode.MIXED
                continue
            elif char == 45 and submode in [Submode.PUNCT, Submode.MIXED]:
                codes.extend([16])
                continue

            if char == 63 and submode != Submode.PUNCT:
                codes.extend([29, 25])
                continue

            if char == 91 and submode not in [Submode.PUNCT, Submode.MIXED]:
                codes.extend([29, 4])
                continue

            if char == 93 and submode != Submode.PUNCT:
                codes.extend([29, 6])
                continue
            elif char == 93 and submode == Submode.PUNCT:
                codes.extend([6])
                continue

            if char == 40 and submode != Submode.PUNCT:
                codes.extend([29, 23])
                continue

            if char == 41 and submode != Submode.PUNCT and data[idx + 1] not in [93]:
                codes.extend([29, 24])
                continue
            elif char == 41:
                codes.extend([25, 24])
                submode = Submode.PUNCT
                continue
            if char == 42 and submode not in [Submode.PUNCT, Submode.MIXED]:
                codes.extend([28, 22])
                submode = Submode.MIXED
                continue
            elif char == 42 and submode == Submode.MIXED:
                codes.extend([22])
                submode = Submode.MIXED
                continue
            elif char == 42:
                codes.extend([22])
                continue

            if char == 36 and submode not in [Submode.PUNCT, Submode.MIXED]:
                codes.extend([28, 18])
                submode = Submode.MIXED
                continue
            elif char == 36 and submode == Submode.MIXED:
                codes.extend([18])
                continue
            if char == 92 and submode != Submode.PUNCT:
                codes.extend([29, 5])
                continue

            if char == 61 and submode != Submode.PUNCT:
                codes.extend([28, 23])
                submode = Submode.MIXED
                continue

            if char == 62 and submode != Submode.PUNCT:
                codes.extend([29, 2])
                continue

            if char == 95 and submode != Submode.PUNCT:
                codes.extend([29, 7])
                continue

            if char == 96 and submode != Submode.PUNCT:
                codes.extend([29, 8])
                continue

            if char == 59 and submode not in [Submode.PUNCT, Submode.MIXED]:
                codes.extend([29, 0])
                continue
            elif char == 59 and submode == Submode.PUNCT:
                codes.extend([0])
                continue
            elif char == 59 and data[idx - 1] in [37]:
                codes.extend([29, 0])
                continue
            if char == 33 and (
                submode not in [Submode.PUNCT, Submode.MIXED]
                or data[idx + 1] in range(48, 58)
            ):
                codes.extend([29, 10])
                continue
            elif char == 33 and submode == Submode.MIXED:
                codes.extend([25, 10])
                submode = Submode.PUNCT
                continue

            if char == 34 and submode != Submode.PUNCT:
                codes.extend([29, 20])
                continue
            if char == 126 and submode != Submode.PUNCT:
                codes.extend([29, 9])
                continue
            if char == 37 and submode not in [Submode.PUNCT, Submode.MIXED]:
                codes.extend([28, 21])
                submode = Submode.MIXED
                continue

            if submode == Submode.LOWER and char in range(60, 91):
                codes.append(27)
                codes.append(CHARACTERS_LOOKUP[char][Submode.UPPER])
                continue
            if char > 64 and char < 91 and submode == Submode.LOWER:
                codes.append(27)
                submode = Submode.UPPER
                continue

        if not exists_in_submode(char, submode):

            prev_submode = submode
            submode = get_submode(char)

            switch_codes = SWITCH_CODES[prev_submode][submode]
            codes.extend(switch_codes)

        if code27:
            if Submode.LOWER == submode:
                codes.append(CHARACTERS_LOOKUP[char][submode])
                codes.append(27)
                submode = Submode.UPPER
                continue

        codes.append(CHARACTERS_LOOKUP[char][submode])

    return codes


def compact_text(config, data, count):
    """Encodes data into code words using the Text compaction mode.

    Can encode: ASCII 9, 10, 13 and 32-126
    Rate compaction: 2 bytes per code word
    """
    # Since each code word consists of 2 characters, a padding value is
    # needed when encoding a single character. 29 is used as padding because
    # it's a switch in all 4 submodes, and doesn't add any data.

    PADDING_INTERIM_CODE = 29

    def compact_chunk(chunk):
        if len(chunk) == 1:
            chunk.append(PADDING_INTERIM_CODE)

        return 30 * chunk[0] + chunk[1]

    interim_codes = compact_text_interim(config, data, count)
    if (
        len(interim_codes) % 2
        and len(interim_codes) > 2
        and (
            (
                interim_codes[len(interim_codes) - 1] == 0
                and interim_codes[len(interim_codes) - 2] == 30
            )
            or (
                interim_codes[len(interim_codes) - 1] == 28
                and interim_codes[len(interim_codes) - 2] == 11
            )
        )
    ):
        interim_codes.pop()
    return [compact_chunk(chunk) for chunk in chunks(interim_codes, 2)]


# -- Bytes compaction mode -----------------------------------------------------


def compact_bytes(config, data, count):
    """Encodes data into code words using the Byte compaction mode.

    Can encode: ASCII 0 to 255
    Rate compaction: 1.2 byte per code word
    """

    def compact_chunk(chunk):
        return (
            compact_full_chunk(chunk)
            if len(chunk) == 6
            else compact_incomplete_chunk(chunk)
        )

    def compact_full_chunk(chunk):
        """Encodes a chunk consisting of exactly 6 bytes.

        The chunk is encoded to 5 code words by changing
        the base from 256 to 900.
        """

        digits = [i for i in chunk]
        return switch_base(digits, 256, 900)

    def compact_incomplete_chunk(chunk):
        """Encodes a chunk consisting of less than 6 bytes.

        The chunk is encoded to 6 code words leaving the base unchanged.
        """

        return [i for i in chunk]

    compacted_chunks = [compact_chunk(chunk) for chunk in chunks(data, size=6)]

    return chain(*compacted_chunks)


# -- Bringing it all together --------------------------------------------------
def compact(config, data, numeric_compaction=True):
    """Encodes given data into an array of PDF417 code words."""
    count = [3, False, 0, 1]
    encoding = "simple"
    try:
        encoding = config["encoding"]
    except:
        pass

    def compact_chunks(chunks, count):
        compacted_chunks = [
            compact_chunk(ordinal, count, *args) for ordinal, args in enumerate(chunks)
        ]

        return chain(*compacted_chunks)

    def compact_chunk(ordinal, count, chunk, compact_fn):
        code_words = []

        # Add the switch code if required
        add_switch_code = ordinal >= 0 or compact_fn != compact_text
        if encoding == "simple":
            code_words.append(get_switch_code(compact_fn, chunk))
            code_words.extend(compact_fn(config, chunk, count))

        elif encoding == "901":
            if add_switch_code:
                if count[0] == 3:
                    code_words.append(901)
                if count[0] == 1:
                    code_words.append(get_switch_code(compact_fn, chunk))
                if count[0] != 1:
                    count[0] -= 1
                if count[0] > 1:
                    code_words.extend(chunk)
                else:
                    code_words.extend(compact_fn(config, chunk, count))
        elif encoding == "901 !902":
            if add_switch_code:
                if count[0] == 3:
                    code_words.append(901)
                if count[0] == 1:
                    code_words.append(get_switch_code(compact_fn, chunk))
                if count[0] != 1:
                    count[0] -= 1
                if count[0] > 1:
                    code_words.extend(chunk)
                else:
                    code_words.extend(compact_fn(config, chunk, count))

        elif encoding == "902 913":
            if add_switch_code:
                if count[1]:
                    code_words.append(get_switch_code(compact_fn, chunk))
                if get_switch_code(compact_fn, chunk) == 902 and not count[1]:
                    count[1] = True
                    code_words.append(get_switch_code(compact_fn, chunk))
            if chunk == [30]:
                code_words.append(913)
            if count[0] != 1:
                count[0] -= 1

            code_words.extend(compact_fn(config, chunk, count))
        return code_words

    def split_to_chunks(config, data):
        """Splits a string into chunks which can be encoded with the
        same encoder.

        Implemented as a generator which yields chunks and
        the appropriate encoder.

        TODO: Currently always switches to the best encoder, even if it's just
        for one character, consider a better algorithm.
        """

        # Default compaction mode is Text
        # (does not require an initial switch code)
        function = compact_text
        chunk = []
        for char in data:

            new_function = get_optimal_compactor_fn(config, char)
            if function != new_function:
                if chunk:

                    yield chunk, function

                chunk = []
                function = new_function
            chunk.append(char)

        if chunk:
            yield chunk, function

    def compact_equals(chunks):
        prev_chunk = None
        prev_fn = None

        for chunk, fn in iter(chunks):
            if prev_chunk is None:
                prev_chunk, prev_fn = chunk, fn
                continue

            if prev_fn == fn:
                prev_chunk.extend(chunk)
                continue

            yield prev_chunk, prev_fn
            prev_chunk, prev_fn = chunk, fn

        if prev_chunk:
            yield prev_chunk, prev_fn

    def replace_short_numbers(chunks):
        prev_chunk = None
        prev_fn = None
        sn16 = None
        try:
            sn16 = bool(config["sn16"])
        except:
            pass
        for chunk, fn in iter(chunks):
            if prev_chunk is None:
                prev_chunk, prev_fn = chunk, fn
                continue

            if len(chunk) < (16 if sn16 else 13) and fn is compact_numbers:
                if prev_fn is compact_text:
                    yield prev_chunk + chunk, prev_fn
                    prev_chunk, prev_fn = None, None
                else:
                    yield prev_chunk, prev_fn
                    prev_chunk, prev_fn = chunk, compact_text
            else:
                yield prev_chunk, prev_fn
                prev_chunk, prev_fn = chunk, fn

        if prev_chunk:
            yield prev_chunk, prev_fn

    chunks = split_to_chunks(config, data)

    if numeric_compaction:
        chunks = compact_equals(replace_short_numbers(chunks))

    return compact_chunks(chunks, count)


def get_optimal_compactor_fn(config, char):
    compactionType = config["compactionType"]
    if 48 <= char <= 57:
        if compactionType == "text":
            return compact_text
        elif compactionType == "numeric":
            return compact_numbers

    if char in CHARACTERS_LOOKUP:
        return compact_text

    return compact_bytes


def get_switch_code(compact_fn, data):
    TEXT = 900
    BYTES = 901
    BYTES_ALT = 924
    NUMBERS = 902

    if compact_fn == compact_text:
        return TEXT

    if compact_fn == compact_bytes:
        return BYTES_ALT if len(data) % 6 == 0 else BYTES

    if compact_fn == compact_numbers:
        return NUMBERS

    assert False, "Nonexistant compaction function"
