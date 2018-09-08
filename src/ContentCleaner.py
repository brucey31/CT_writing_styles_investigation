__author__ = "Bruce Pannaman"

import spacy
from pyphen import Pyphen
nlp = spacy.load('en')
from tqdm import tqdm_notebook as tqdm
import re
import pandas as pd
import math


class ContentCleaner:
    def __init__(self, dataset, content_column):
        self.dataset = dataset.reset_index()
        self.content_column = content_column
        self.dic = Pyphen(lang='en_US')
        
        
        self.process_data()
    
    def __str__(self):
        return"""
            This class takes a raw dataset of data and builds a
            clean NLP dataset with features of out of it
        """
    
    def lower_case(self):
        self.dataset[self.content_column] = self.dataset[self.content_column].str.lower()
    
    def remove_html_tags(self):
        cleanr = re.compile('<.*?>.*<.*>')
        self.dataset[self.content_column] = [re.sub(cleanr, '', r) for r in self.dataset[self.content_column]]
    
    def stem_words(self):
        """
        https://stackoverflow.com/questions/38763007/how-to-use-spacy-lemmatizer-to-get-a-word-into-basic-form
        """
        print("Stemming Words")
        for i, row in tqdm(self.dataset.iterrows()):
            stemmed_string = ""
            content_row = nlp(row["content"])
            for word in content_row:
                stemmed_string += " " + word.lemma_
            self.dataset.loc[i, "content"] = stemmed_string
    
    def remove_stop_words(self):
        print("Removing Stop Words")
        for i, row in tqdm(self.dataset.iterrows()):
            sentence_sans_stop_words = ""
            content_row = nlp(row["content"])
            
            for word in content_row:
                if word.is_stop is False:
                    sentence_sans_stop_words += " " + word.text
            self.dataset.loc[i, "content"] = sentence_sans_stop_words
            self.dataset.loc[i, "num_words"] = len(content_row)
    
    def count_adjectives(self):
        """
        see:
        https://spacy.io/api/annotation
        https://spacy.io/usage/linguistic-features
        """
        print("Counting Adjectives")
        for i, row in tqdm(self.dataset.iterrows()):
            adjective_count = 0
            content_row = nlp(row["content"])
            
            for word in content_row:
                if word.pos_ == "ADJ":
                    adjective_count += 1
            self.dataset.loc[i, "adjectives"] = adjective_count
        
    def biggest_word(self):
        """
        Taken from https://github.com/shivam5992/textstat
        """
        self.dic = Pyphen(lang='en_US')
        print("Finding Biggest Words")
        for i, row in tqdm(self.dataset.iterrows()):
            biggest_word = 0
            content_row = nlp(row["content"])
            
            for word in content_row:
                word_hyphenated = self.dic.inserted(word.text)
                word_size = max(1, word_hyphenated.count("-") + 1)
                if word_size > biggest_word:
                    biggest_word = word_size
                
            self.dataset.loc[i, "biggest_word_syllables"] = biggest_word
    
    def readability_score(self):
        """
        Taken from - https://github.com/shivam5992/textstat
        
        Based on The Flesch Reading Ease formula
        """
        def avg_sentence_length(text): 
            sentences = re.split(r' *[\.\?!][\'"\)\]]*[ |\n](?=[A-Z])', text)
            ignore_count = 0
            sentence_lengths = []
            for sentence in sentences:
                if len(sentence.split(" ")) <= 2:
                    ignore_count += 1
                else:
                    sentence_lengths.append(len(sentence.split(" ")))
            sentence_count = max(1, len(sentences) - ignore_count)
            sentence_length_mean = sum(sentence_lengths)
            return sentence_length_mean/sentence_count
            
            
        def avg_syllables_per_word(text):
            words = nlp(row["content"])
            syllables = []
            self.dic = Pyphen(lang='en_US')
            
            for word in words:
                word_hyphenated = self.dic.inserted(word.text)
                syllables.append(max(1, word_hyphenated.count("-") + 1))
            return sum(syllables)/len(words)
        
        def legacy_round(number, points=0):
            p = 10 ** points
            return float(math.floor((number * p) + math.copysign(0.5, number))) / p
        
        # code from https://github.com/shivam5992/textstat
        print("Assessing Readability Score")
        for i, row in tqdm(self.dataset.iterrows()):
            sentence_length = avg_sentence_length(row["content"])
            syllables_per_word = avg_syllables_per_word(row["content"])
            flesch = (
                206.835
                - float(1.015 * sentence_length)
                - float(84.6 * syllables_per_word)
            )
            Flesch_reading_score = legacy_round(flesch, 2)
            self.dataset.loc[i, "flesch_reading_score"] = Flesch_reading_score
        
        
    def count_alliteration(self):
        print("Counting Alliteration")
        for i, row in tqdm(self.dataset.iterrows()):
            repeat_letter = None
            consecutive = False
            alliteration_count = 0
            
            if len(row["content"]) > 0:
                
                words = row["content"].split(" ")
                for word in words:
                    if len(word) > 0:
                        # Start of new alliteration
                        if str(word)[0] == repeat_letter and consecutive is False:
                            alliteration_count += 1
                            repeat_letter = str(word)[0]
                            consecutive = True
                        # In the middle of a consecutive streak of alliteration
                        elif str(word)[0] == repeat_letter and consecutive:
                            repeat_letter = str(word)[0]

                        # End of an alliteration
                        elif str(word)[0] != repeat_letter:
                            repeat_letter = str(word)[0]
                            consecutive = False
                self.dataset.loc[i, "alliteration"] = alliteration_count
            
            else:
                self.dataset.loc[i, "alliteration"] = 0
    
    def process_data(self):
        self.count_alliteration()
        self.count_adjectives()
        self.biggest_word()
        self.readability_score()
        self.remove_html_tags()
        self.lower_case()
        self.remove_stop_words()
        self.stem_words()
        
        