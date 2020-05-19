#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 26 22:31:22 2020

@author: valenetjong

Note 1: plural words are not marked as rhymes or different verb tenses (FIXED)
Note 2: if multisyllable you can mark 
Note 3: use SQL/pandas? That way you can store number of times word appears...
Note 4: Maybe start at the end of each sentence and then start working backwards,
and look for words right next to commas and periods 
Note 5: Use CMU pronounciation thing and just do this--step 1: break everything 
into phenotypes; step 2: search for assonance matches

AH EH OH 
list; indices; list with only vowel sounds


"""
import inflect
import pandas as pd
import string
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer

p = inflect.engine()

RHYME_DICT = {} # global rhyming dict w/ key: word & value: rhymes in lyrics
VOWELS = ['AA1', 'AE1', 'AH1', 'AO1', 'AW1', 'AY1', 'EH1', 'ER1', 
            'EY1', 'IH1', 'IY1', 'OW1', 'OY1', 'UH1', 'UW1'] # stressed vowel

def txt_Dict():
    filepath = "phodict.txt"
    dict1 = dict()
    with open(filepath) as file1:
        for line in file1:
            words = line.split() # splits line on whitespace
            dict1[words[0]] = tuple(words[1:])
    return dict1
            
PHODICT = txt_Dict() # phonetic dictionary

def rhyme_generator():
    "Takes user inputted lyrics and stores into list and dictionary"
    lyrics = input("Input lyrics to rhyme scheme analyzer: ")
    BAR_LIST = text_cleaner(lyrics)
    bar_processor(BAR_LIST)
    assonance()
    post_processor()
    df = pd.DataFrame.from_dict(RHYME_DICT, orient='index')
    df.to_excel('output_rhymes.xls', sheet_name = 'Rhymes')
    
def text_cleaner(lyrics):
    "Helper function that cleans up lyrics for list and rhyme dictionary"
    tokens = word_tokenize(lyrics)
    # converts words to lowercase 
    tokens = [element.lower() for element in tokens] 
    table = str.maketrans('', '', string.punctuation)   
    stripped = [w.translate(table) for w in tokens] # strips punctuation
    BAR_LIST = [word for word in stripped if word.isalpha()] # keep alpha words
    stop_words = set(stopwords.words('english')) # set of words to ignore 
    BAR_LIST = [word for word in BAR_LIST if not word in stop_words] # filter 
    return BAR_LIST

def bar_processor(BAR_LIST):
    "Function iterates through the list and searches each word for its rhymes"
    bar_set = set(BAR_LIST)    
    bool_dict = dict.fromkeys(bar_set, False)
    for i in bar_set:
        if (bool_dict[i]):  # if visited, skip]
            continue
        intersection = same_stem(i, bool_dict)
        # find intersection bw rhymes & words in bar set
        intersection2 = bar_set.intersection(word_rhymes(BAR_LIST,i))
        intersection3 = dedup(intersection2, bool_dict)
        intersection |= intersection3
        for j in intersection:  # mark as True b/c visited now
            bool_dict[j] = True
        list_rhyme = list(intersection) 
        RHYME_DICT[i] = list_rhyme
        
def same_stem(word, bool_dict):
    '''Checks which words have the same stem and place them into the same 
    rhyme group'''
    stemmer = SnowballStemmer("english")
    stem = stemmer.stem(word)
    intersection = set()
    intersection = {w for w in bool_dict.keys() if (not bool_dict[w] and 
                    (stemmer.stem(w) == stem))}
    return intersection

def word_rhymes(BAR_LIST, word):
    "Calls scraper for perfect and near rhymes of argument word from lyrics"
    perfect_rhymes = rhyme_dataframe(word, 'rhy') # perfect rhymes
    if (len(BAR_LIST) > 500):
        return(perfect_rhymes)
    near_rhymes = rhyme_dataframe(word, 'nry')
    df_rhy = perfect_rhymes | near_rhymes 
    return(df_rhy)
        
def rhyme_dataframe(word, rhyme_type):
    "Scrapes rhymes into pandas df and outputs set" 
    base_url = 'https://api.datamuse.com/words?rel_'
    url = base_url + rhyme_type + '=' + word + "&max=50"
    df_rhy = (pd.read_json(url)) # url provides data in json format
    if (df_rhy.empty): 
        return(set())
    df_rhy = df_rhy.loc[:, ['word']]['word']
    df_rhy = set(df_rhy.unique())
    return df_rhy

def dedup(set1, bool_dict):
    "Prevents additioon of duplicate words"
    set2 = {w for w in set1 if (not bool_dict[w])}
    return set2

def assonance():
    "Refines dictionary items by combining assonance rhymes"
    syl_dict = {}
    for i in RHYME_DICT:
        try:
            if (syllableCount(i.upper()) == 1):
                syl_dict[i] = PHODICT[i.upper()]
        except KeyError:
            pass
    for vow in VOWELS:
        vow_list = [word for word in syl_dict.keys() if vow in syl_dict[word]]
        length = len(vow_list)
        vow_set = set()
        for index in range(length):
            word = vow_list[index]
            vow_set |= set(RHYME_DICT[word])
            if (index == length - 1): 
                RHYME_DICT[word] = list(vow_set)
                break
            RHYME_DICT.pop(word)
            
def syllableCount(word):
    "Calculates number of syllables in argument word"
    word = word.upper()
    syllables = PHODICT[word]
    return sum(int(syllable[0] in "AEIOU") for syllable in syllables)

def post_processor():
    "Removes single length rhyme groups"
    RHYME_DICT_COPY = RHYME_DICT.copy()
    for word in RHYME_DICT_COPY.keys():
        if (len(RHYME_DICT_COPY[word]) == 1):
            RHYME_DICT.pop(word)

rhyme_generator()

