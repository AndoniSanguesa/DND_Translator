import json,urllib.request
from urllib.error import HTTPError
import tkinter as tk

to_delete = ["ˈ", "-", "/", "(", ")", "ˌ", "ː", " "]
dipthongs = ["aɪ", "ɔɪ", "eɪ", "oʊ", "tʃ", "dʒ"]

file = open("not_words", "r")
not_words = []

for line in file.readlines():
    not_words.append(line.rstrip().lower())
file.close()


def delete_chars(word):
    for char in to_delete:
        word = word.replace(char, "")
    return word


def get_ipa(word):
    ret = []
    while word != "":
        if word[0:2] in dipthongs:
            if word[0:2] == "aɪ":
                ret.append("a")
                ret.append("i")
            elif word[0:2] == "ɔɪ":
                ret.append("ɔ")
                ret.append("i")
            else:
                ret.append(word[0:2])
            word = word[2:]
        else:
            if word[0] == "ŋ":
                ret.extend(["n", "g"])
            else:
                ret.append(word[0])
            word = word[1:]
    return ret

def gen_sentence(sentence):
    sentence = "".join(filter(lambda x: x.isalpha() or x == " ", sentence))
    trans_dict = {ord("ō"): ord("o")}
    # TEMP SYMBOLS: j, ɔ, dʒ, z --> s, ʒ --> sh
    symb_map = {"oʊ": "O", "o": "O", "g": "H", "n": "N", "tʃ": "C", "l": "K", "u": "V", "ɛ": "E", "ɪ": "E", "θ": "U",
                "ə": "A", "a": "A", "ɒ": "A", "ɑ": "A", "æ": "A", "r": "Q", "ɹ": "Q", "d": "D", "k": "J", "h": "M", "ʃ": "S",
                "s": "R", "p": "P", "eɪ": "F", "m": "L", "f": "G", "t": "T", "w": "X", "i": "I", "b": "B", "v": "W", "j": "I",
                "ɔ": "O", "dʒ": "H", "ʊ": "V", "ɡ": "H", "ð": "U", "z": "R", "ʌ": "A", "ʒ": "S", "e": "E"}

    phon_dict = open("phon_dict.json", "r")
    data = json.load(phon_dict)

    words = []

    for word in list(map(lambda x: x.lower(), sentence.split())):
        if word not in data.keys():
            try:
                mw_data = urllib.request.urlopen(f"https://api.dictionaryapi.dev/api/v2/entries/en_US/{word}").read()
            except HTTPError as c:
                print(c)
                if "404" in str(c):
                    not_words.append(word)
                print(f"{word} could not be found.")
                return

            output = json.loads(mw_data)
            try:
                pronounciation = output[0]["phonetics"][0]["text"]
            except IndexError:
                print(f"No pronunciation found for {output[0]['word']}")
                not_words.append(word)
                return

            data[word] = delete_chars(pronounciation.translate(trans_dict))
        words.append(get_ipa(data[word]))
    phon_dict.close()
    phon_dict = open("phon_dict.json", "w")
    phon_dict.close()

    ret = []
    for word in words:
        word_str = ""
        for ind in range(len(word)):
            word_str += symb_map[word[ind]]
        ret.append(word_str)

    return ret

size = 25
width, height = 1600, 1600
cur_text = ""
cur_words = []
cur_phons = []
root = tk.Tk()
root.title("App")
root.geometry(f"{width}x{height}")
root.update()
sentence = tk.StringVar()
text = tk.Text(root, width=1)
text.pack(fill=tk.BOTH,side=tk.LEFT, expand=True)
label = tk.Label(root, font=("dnd", size), textvariable=sentence, width=1, height=1, anchor="nw", wraplength=width/2)

label.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)


def update_sentence():
    global cur_text, cur_words, cur_phons
    this_txt = text.get("1.0", "end")
    found = False
    if this_txt != cur_text:
        these_words = this_txt.split()
        if len(these_words) == len(cur_words):
            for ind in range(len(cur_words)):
                if cur_words[ind] != these_words[ind] and these_words[ind] not in not_words:
                    new_phon = gen_sentence(these_words[ind])
                    if new_phon is None:
                        root.after(100, update_sentence)
                        return
                    if len(cur_phons) == 0 or ind >= len(cur_phons):
                        cur_phons.append(new_phon[0])
                    else:
                        cur_phons[ind] = new_phon[0]
        elif len(these_words) == len(cur_words) - 1:
            for ind in range(len(these_words)):
                if cur_words[ind] != these_words[ind]:
                    cur_phons.pop(ind)
                    found = True
                    break
            if not found:
                cur_phons.pop(len(cur_phons)-1)
        elif len(these_words) == len(cur_words) + 1:
            for ind in range(len(cur_words)):
                if cur_words[ind] != these_words[ind] and these_words[ind] not in not_words:
                    new_phon = gen_sentence(these_words[ind])
                    found = True
                    if new_phon is None:
                        root.after(100, update_sentence)
                        return
                    cur_phons.insert(ind, new_phon[0])
                    break
            if not found and these_words[-1] not in not_words:
                new_phon = gen_sentence(these_words[-1])
                if new_phon is None:
                    root.after(100, update_sentence)
                    return
                cur_phons.append(new_phon[0])
        else:
            these_phons = gen_sentence(this_txt)
            cur_text = this_txt
            sentence.set(gen_sentence(text.get("1.0", "end")))
            if type(these_phons) == list:
                cur_phons = these_phons
            else:
                cur_phons = []
        cur_words = these_words
        sentence.set(" ".join(cur_phons))
        #print(cur_words, cur_phons)
    root.after(100, update_sentence)


root.after(100, update_sentence)
tk.mainloop()

file = open("not_words", "w")
for word in not_words:
    file.write(word + "\n")
file.close()
