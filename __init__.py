import os


import pandas as pd
import numpy as np
from fontTools import ttLib
from fontTools.ttLib.tables._n_a_m_e import NameRecord
from typing import List


def sortNamingTable(names: List[NameRecord]) -> List[NameRecord]:
    # https://stackoverflow.com/a/72228817/15096247
    """
    Parameters:
        names (List[NameRecord]): Naming table
    Returns:
        The sorted naming table.
        Based on FontConfig:
        - https://gitlab.freedesktop.org/fontconfig/fontconfig/-/blob/d863f6778915f7dd224c98c814247ec292904e30/src/fcfreetype.c#L1127-1140
    """

    def isEnglish(name: NameRecord) -> bool:
        # From: https://gitlab.freedesktop.org/fontconfig/fontconfig/-/blob/d863f6778915f7dd224c98c814247ec292904e30/src/fcfreetype.c#L1111-1125
        return (name.platformID, name.langID) in ((1, 0), (3, 0x409))

    # From: https://github.com/freetype/freetype/blob/b98dd169a1823485e35b3007ce707a6712dcd525/include/freetype/ttnameid.h#L86-L91
    PLATFORM_ID_APPLE_UNICODE = 0
    PLATFORM_ID_MACINTOSH = 1
    PLATFORM_ID_ISO = 2
    PLATFORM_ID_MICROSOFT = 3
    # From: https://gitlab.freedesktop.org/fontconfig/fontconfig/-/blob/d863f6778915f7dd224c98c814247ec292904e30/src/fcfreetype.c#L1078
    PLATFORM_ID_ORDER = [
        PLATFORM_ID_MICROSOFT,
        PLATFORM_ID_APPLE_UNICODE,
        PLATFORM_ID_MACINTOSH,
        PLATFORM_ID_ISO,
    ]

    return sorted(
        names,
        key=lambda name: (
            PLATFORM_ID_ORDER.index(name.platformID),
            name.platEncID,
            -isEnglish(name),
            name.langID,
        ),
    )


def get_font_names(font: ttLib.TTFont, nameID: int) -> List[NameRecord]:
    """
    Parameters:
        font (ttLib.TTFont): Font
        nameID (int): An ID from the naming table. See: https://learn.microsoft.com/en-us/typography/opentype/spec/name#name-ids
    Returns:
        A list of each name that match the nameID code.
        You may want to only use the first item of this list.
    """

    names = sortNamingTable(font["name"].names)

    return list(filter(lambda name: name.nameID == nameID, names))


def get_all_fonts_from_path():
    allfonts = os.listdir(os.path.join(os.environ["WINDIR"], "fonts"))
    allfonts = [os.path.join(os.environ["WINDIR"], "fonts", x) for x in allfonts]
    return allfonts


def get_all_fonts():
    loo = [4]
    allf = []
    fonts = get_all_fonts_from_path()
    for f in fonts:
        try:
            font = ttLib.TTFont(f)
            allfx = []
            for l in loo:
                allf.append([f, l, get_font_names(font, l)])
            allf.append(allfx.copy())
        except Exception:
            pass
    df = pd.DataFrame(allf).dropna()
    df = df.loc[df[2].apply(np.any) != False]
    df = (
        df.explode(2)
        .drop(columns=1)
        .astype("string")
        .drop_duplicates()
        .rename(columns={0: "path", 2: "font"})
        .reset_index(drop=True)
    )
    return df
