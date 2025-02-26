from typing import Literal


Lang = Literal["VA", "VCN", "VF", "VJ", "VKR", "VQC", "VO"]

LangId = Literal["va", "vcn", "vf", "vf1", "vf2", "vj", "vkr", "vqc", "vostfr"]

lang2ids: dict[Lang, list[LangId]] = {
    "VO": ["vostfr"],
    "VA": ["va"],
    "VCN": ["vcn"],
    "VF": ["vf", "vf1", "vf2"],
    "VJ": ["vj"],
    "VKR": ["vkr"],
    "VQC": ["vqc"],
}

id2lang: dict[LangId, Lang] = {
    lang_id: lang for lang, langs_id in lang2ids.items() for lang_id in langs_id
}

lang_ids = list(id2lang.keys())

flags: dict[Lang | LangId, str] = {
    "VO": "",
    "VA": "🇬🇧",
    "VCN": "🇨🇳",
    "VF": "🇫🇷",
    "VJ": "🇯🇵",
    "VKR": "🇰🇷",
    "VQC": "🏴󠁣󠁡󠁱󠁣󠁿",
}

for language, language_ids in lang2ids.items():
    for lang_id in language_ids:
        flags[lang_id] = flags[language]


if __name__ == "__main__":
    import re
    from pprint import pprint

    import httpx

    URL = "https://anime-sama.fr/js/contenu/script_videos.js"
    page = httpx.get(URL).text
    langs = {}

    matchs = re.findall(r"if\((.+)\){langue = \"(.+)\";}", page)
    for match in matchs:
        langs[match[1]] = match[0].split('"')[1::2]

    pprint(langs)
