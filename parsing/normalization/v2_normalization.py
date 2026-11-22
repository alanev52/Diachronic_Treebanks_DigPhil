import os
import re
import time
import json
import math
import unicodedata
import difflib
import pandas as pd
from functools import lru_cache
from collections import defaultdict
from difflib import SequenceMatcher
from conllu import parse_incr
from rules_based_norm import normalize_historical_swedish

# LOAD WORDLIST + FREQS
df = pd.read_csv(
    "flex.csv",
    sep="\t",
    header=None,
    names=["word", "novels", "newspapers", "forums"]
)

df = df.dropna(subset=["word"])
df = df.dropna(subset=["novels", "newspapers", "forums"])
df = df[(df["novels"] > 0) | (df["newspapers"] > 0) | (df["forums"] > 0)]
df = df.sort_values(by="novels", ascending=False)
lookup = df.set_index("word")

def novels_freq(word):
    return lookup["novels"].get(word, 0)

modern_words = df["word"].tolist()


# REGEX RULES (COMPILED ONCE)

pattern_v = re.compile(r'^(hv|w)', re.IGNORECASE)
pattern_vi = re.compile(r'^hui', re.IGNORECASE)
pattern_kv = re.compile(r'^qv', re.IGNORECASE)
pattern_j_ = re.compile(r'^(ie|ia)', re.IGNORECASE)
pattern_j_out = re.compile(r'^(ja|jä)', re.IGNORECASE)
pattern_jhz = re.compile(r'(j|h|z)$', re.IGNORECASE)
pattern_dtfgk_h = re.compile(r'(?<=[d|t|f|g|k|e])h', re.IGNORECASE)
pattern_j = re.compile(r'(j)$',re.IGNORECASE)
pattern_2m = re.compile(r'([aeiouyåäö])mm(an|ar)$', re.IGNORECASE)

# PRE-INDEX BY LENGTH
words_by_length = defaultdict(list)
for w in modern_words:
    if isinstance(w, str):
        words_by_length[len(w)].append(w)
    
# FAST TOKENIZER
def fast_tokenize(text):
    return re.findall(r"\w+|[^\w\s]", text, re.UNICODE)


# PUNCT CHECK
def is_punct(token):
    return all(unicodedata.category(ch).startswith("P") for ch in token)


# FAST SIMILARITY
def custom_similarity(a, b):  #a - word, b - cand
    # a_norm = unicodedata.normalize('NFC', a)
    # b_norm = unicodedata.normalize('NFC', b)

    

    sm = SequenceMatcher(None, a, b)
    ratio = sm.ratio()

    if a == b:
        ratio += 3.0
    if set(b)-set(a) == {'ä'} and (set(a)-set(b)) == {'e'}:
        ratio += 0.15
    if abs(len(a) - len(b)) > 2:
        ratio -= 1.0
    if sum(1 for code in sm.get_opcodes() if code[0] != "equal") == 1:
        ratio += 0.2
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "insert" and b[j1:j2] == a[-3:-2]:
            ratio += 0.03

    return ratio

# MAIN NORMALIZER (CACHED)
@lru_cache(maxsize=50000)
def normalize_word(word):
    #print("entered normalize_word:", word)
    n = len(word)
    ranking, candidates = [],[]
    word = word.lower()
    word_to_look = word

    # Candidate pool by length only
    if len(word) <= 5:
        candidates_pool = (
            words_by_length[n-1] +
            words_by_length[n] +
            words_by_length[n+1]
        )
    else:
        candidates_pool = (
            words_by_length[n-1] +
            words_by_length[n]
        )

    filtered_words = candidates_pool
    
    # CHECK PROBLEM WORD==========================================#
    # original_spelling = 'det'
    # wrong_spelling = 'ett'  #"sjelt": "stelt", 
    # correct_spelling = 'det'
    
   
    # if word == original_spelling:
    #     print(correct_spelling, "found in modern words:", correct_spelling in modern_words)
    #     print(len(candidates_pool), correct_spelling in candidates_pool)
    #     print(correct_spelling.capitalize(),'found in filtered:', len(filtered_words), correct_spelling in filtered_words)
    #=====================


    word_to_look =  normalize_historical_swedish(word)   

    #=======================
    # if word == original_spelling:
    #     print("before candicates:", word_to_look)
    #========================
  
    candidates = difflib.get_close_matches(word_to_look, filtered_words, n=20, cutoff=0.6)
    
    
    #======================
    # if word == original_spelling:
    #     print(correct_spelling, 'in candidates found:',correct_spelling in candidates)
    #=======================
    
  

    for cand in candidates:
        c_fr = 0
        
        # sm = SequenceMatcher(None, word_to_look, cand)
        # #print(word_to_look, cand, sum(1 for code in sm.get_opcodes() if code[0] != "equal"))
        # if sum(1 for code in sm.get_opcodes() if code[0] != "equal") <= 2:
        #     #print("lost here!")
        #     return word_to_look
      
        freq = novels_freq(cand)
        c_fr = freq / 10000 if freq else 0
        score = c_fr + custom_similarity(word_to_look, cand)
        ranking.append((cand, score))
        #====================
        # if cand == original_spelling:
        #     print(word, "the candidate:", cand,  'fr:',c_fr,'sim:', score - c_fr)
        # if cand == wrong_spelling:
        #     print(word, "the candidate:",cand,  'fr:',c_fr,'sim:', score - c_fr)
        # if cand == correct_spelling:
        #     print(word, "the candidate:",cand, 'fr:',c_fr,'sim:', score - c_fr)    
        # #====================
    ranking.sort(key=lambda x: x[1] if not math.isnan(x[1]) else 0, reverse=True)
    # print(ranking)
    #======================
    # if ranking:
    #     print(word_to_look.capitalize(),'!!!', correct_spelling in ranking, ranking[0][0])
    # else: 
    #     print(word, len(ranking))
    #======================
    #print (word_to_look, ranking[0][0])
    return ranking[0][0] if ranking else word_to_look


# SENTENCE NORMALIZER
def normalize_sentence(text):
    tokens = fast_tokenize(text)
    normalized = [normalize_word(tok) if not is_punct(tok) else tok for tok in tokens]
    # print("norm:", normalized)
    mapping = {}
    output = []

    for hw, nw in zip(tokens, normalized):
        if hw.istitle():
            output.append(hw)
            mapping[hw] = nw #hw
        else:
            output.append(nw)
            mapping[hw] = nw

    return " ".join(output), mapping

class ConlluReader:
    def __init__(self, input_path, output_path):
        self.in_path = input_path
        self.out_path = output_path
       

    def conllu_from_hist_to_modern(self):
        start = time.time()
        for filename in os.listdir(self.in_path):
            if not filename.endswith(".conllu"):
                continue
            file_path = os.path.join(self.in_path, filename)
            out_file_path = os.path.join(self.out_path, filename)
             
            with open(file_path, "r", encoding="utf-8") as f_in, \
                open(out_file_path, "w", encoding="utf-8") as f_out:

                for sentence in parse_incr(f_in):
                    for token in sentence:
                        if token["form"] is not None:
                            token["misc"] = token["form"]
                            token["form"] = normalize_word(token["form"])

                    f_out.write(sentence.serialize())
                    f_out.write("\n")
        print("TOTAL TIME:", (time.time() - start)/60)


    def from_hist_conllu_to_modern_txt(self):
        start = time.time()
        all_sent_m_to_h = defaultdict(dict)

        if os.path.isdir(self.in_path):
            files = [os.path.join(self.in_path,p) for p in os.listdir(self.in_path) if p.endswith(".conllu")]
        elif os.path.isfile(self.in_path):
            files = [self.in_path]
        else:
            print("Path does not exist")

        # for filename in os.listdir(self.in_path):
        #     file_path = os.path.join(self.in_path, filename)
        #     if filename.endswith(".conllu"):
        for file in files:
            f_name = file.split("/")[-1]
            #f_name = self.in_path.split("/")[-1]
            out_filename = f_name.rstrip('.conllu') + ".txt"
            out_file_path = os.path.join(self.out_path, out_filename)

            #sample_name = filename.split("-")[1]
            sample_name = file.split("-")[1]
              
            #with open(file_path, "r", encoding="utf-8") as in_f, \
            with open(file, "r", encoding="utf-8") as in_f, \
                open(out_file_path, "w", encoding="utf-8") as out_f:

                for tokenlist in parse_incr(in_f):
                    sent_id = tokenlist.metadata.get("sent_id")
                    text = tokenlist.metadata.get("text")
                    #print(sent_id)
                    norm_sent, m_to_h = normalize_sentence(text)
                    all_sent_m_to_h[sample_name][sent_id] = m_to_h

                    out_f.write(norm_sent + "\n")
        # SAVE MAPPING JSON
        with open("all_sent_m_to_h.json", "w", encoding="utf-8") as f:
            json.dump(all_sent_m_to_h, f, ensure_ascii=False, indent=2)

        print("TOTAL TIME:", (time.time() - start)/60)

    # TODO: def for hist txt to modern txt

if __name__ == "__main__":
    import sys
    # usage: python3 v2_normalization.py INPUT_FOLDER OUTPUT_FOLDER
    # (run from this folder, with flex.csv unzipped next to the script)
    in_path, out_path = sys.argv[1], sys.argv[2]
    os.makedirs(out_path, exist_ok=True)
    ConlluReader(in_path, out_path).conllu_from_hist_to_modern()

  
   
