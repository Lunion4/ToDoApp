class Lang:
    def __init__(self, language):
        self.language = language
        self.dictionary = {}

        self.with_loaded_lang_file(self.parse_lang_file)

    def with_loaded_lang_file(self, function_with):
        try:
            with open("langs/" + self.language + ".txt", encoding="utf-8") as file:
                function_with(file)
        except FileNotFoundError:
            raise ValueError(f"Language \"{self.language}\" doesn't have it's lang file!")

    def parse_lang_file(self, file):
        lines = file.readlines()
        self.dictionary["language"] = lines[0][:-1]
        for line in lines[1:]:
            comment = line.find("#")
            if comment >= 0: line = line[:comment]
            if line.replace(" ", "") == "\n": continue
            start_cut = line.find(" ")
            end_cut = start_cut
            while line[end_cut] == " ":
                end_cut += 1
            path = line[:start_cut]
            value = line[end_cut:-1].replace('|', "\n")

            self.dictionary[path] = value

    def set_language(self, new_language):
        self.language = new_language
        self.with_loaded_lang_file(self.parse_lang_file)

    def __getitem__(self, item) -> str:
        try:
            result = self.dictionary[item]
        except KeyError:
            return f'"{item}" not found!'
        except TypeError:
            return f'"{item}" not found!'
        return result


if __name__ == "__main__":
    new_lang = Lang("ru_RU")  # load russian lang

    print(new_lang["language"])  # get string with code "language"
    print(new_lang.dictionary.keys())  # get all codes



