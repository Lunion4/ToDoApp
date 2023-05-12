import os
import requests
from localisation import Lang


original = Lang('en_US')
max_indent = len(max(original.dictionary.keys(), key=len)) / 4
if int(max_indent) == max_indent:
    max_indent += 1
max_indent = int(max_indent)
langs = ["ru_RU", "be_BY", "es_ES"]
custom_langs = "custom_langs"
if custom_langs not in os.listdir(): os.mkdir(custom_langs)
for lang in langs:
    with open(custom_langs + '/' + lang + '.txt', 'w', encoding="utf-8") as file:
        for k, v in original.dictionary.items():
            indent = max_indent - len(k) // 4 + 1

            end = lang[:2]
            url = f"https://translate.google.com/translate_a/single?client=gtx&sl=auto&tl={end}&dt=t&q={v}"
            response = requests.get(url)
            translated = response.json()[0][0][0].capitalize()

            file.write(k + '\t' * indent + translated + '\n')
            print(translated)
