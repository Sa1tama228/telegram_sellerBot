import json


class DictObj:
	def __init__(self, in_dict: dict):
		assert isinstance(in_dict, dict)
		for key, val in in_dict.items():
			if isinstance(val, (list, tuple)):
				setattr(self, key, [DictObj(x) if isinstance(x, dict) else x for x in val])
			else:
				setattr(self, key, DictObj(val) if isinstance(val, dict) else val)


def load():
	global CONFIG

	with open('config.json', encoding='utf-8') as f:
		x = json.load(f)
		CONFIG = DictObj(x)
		f.close()

	return CONFIG


def numeral_noun_declension(
    number,
    nominative_singular,
    genetive_singular,
    nominative_plural
):
	return (
        (number in range(5, 20)) and nominative_plural or
        (1 in (number, (diglast := number % 10))) and nominative_singular or
        ({number, diglast} & {2, 3, 4}) and genetive_singular or nominative_plural
    )

tags = {
        "Таргет Fb & Insta": "fb_insta",
        "Сайты/Разработка": "sites_dev",
        "SMM/Instagram": "smm_instagram",
        "Дизайн": "design",
        "Копирайтинг": "copywriting",
        "Видео/монтаж": "video_editing",
        "Аккаунты/Буст/Предметы": "boost_items"
    }
