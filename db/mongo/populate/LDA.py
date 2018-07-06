#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 20 15:46:20 2018

@author: s0k00rp
"""

#from store_data import EmailDataStorage 
from gensim import corpora
from gensim.corpora import Dictionary
from gensim.models import ldamodel
from nltk.corpus import stopwords
import os
import pyLDAvis 
import pyLDAvis.gensim
import pymongo
from pymongo import MongoClient
import pickle
import re


class LDAModelMaker():
    
    def __init__(self, create_texts, texts_filepath, corpus_filepath,  dictionary_filepath):
        """
        Pull up information required for generating the LDA Model. 
        
        :param {boolean} create_texts:
            Whether or not we must create texts. 
        
        :param {str} texts_filepath: 
            Either the location of where to load texts from or where we must save texts to. 
            Explained above. 
            
        :param {str} corpus_filepath: 
            Location of where we must save or load the corpus from. 
        
        :param {str} dictionary_filepath: 
            Location of where we must save or load the dictionary from. 
        
        """
        
        emailClient = MongoClient()
        self.db = emailClient[os.getenv('email_database_name')]
        self.col = self.db[os.getenv('email_collection_name')]
        self.texts = []
        self.stopWords = set(stopwords.words('english'))
        self.dictionary = Dictionary()
        self.remove = '\!"#$%&()*+,-.:;<=>?@[^_`{|}~]'
        
        if eval(create_texts):
            self.start_cleaning_process(texts_filepath, corpus_filepath, dictionary_filepath)
            self.email_database_content()
        else:
            self.load_texts(texts_filepath)
            self.load_corpus(corpus_filepath)
            self.load_dictionary(dictionary_filepath)
        

    def start_cleaning_process(self, texts_filepath, corpus_filepath, dictionary_filepath):
        """
        Clean texts for later use. Pulls values from EnronEmailData database. Generates corpus and dictionary. 
        
        :param {str} texts_filepath: 
            Where to save the generated texts to. 
        
        :param {str} corpus_filepath: 
            Where to save the generated corpus to. 
            
        :param {str} dictionary_filepath: 
            Where to save generated dictionary to. 
        
        """
        self.col.create_index('email_counter')
        table = str.maketrans('', '', self.remove)
        counter = 0
        for email in self.col.find().sort('email_counter', pymongo.ASCENDING):
            if email['email_counter'] != counter:
                raise IndexError('the email_counter and the actual counter do not match up')
            counter += 1
            text_line = self.clean_data(table, email['content'])
            self.texts.append(text_line)
#        print("DONE")
        self.frequency_check(corpus_filepath, dictionary_filepath)
        self.save_texts(texts_filepath)
    

    def clean_data(self, table, text):
        """
        Remove characters that aren't letters or numbers
        
        :param {str} text: 
            container that has one email 
        
        :param table:
            structure that maps the characters in self.remove to blank spaces
        
        """

        clean_text = []
        text = text.translate(table).lower()
        text_array = text.split()
        for token in text_array: 
            token.replace('/hou', '').replace('/etc', '')
            if token not in self.stopWords and len(token) > 1:
                clean_text.append(token)
        return clean_text
    

    def frequency_check(self, corpus_filepath, dictionary_filepath):
        """
        Remove tokens that only occur once in the entire corpus
        
        :param {str} corpus_filepath: 
            Where to save the generated corpus to. 
            
        :param {str} dictionary_filepath: 
            Where to save generated dictionary to. 
        
        """
        # update frequencies of each value in the dict created below
        frequency = {}
        for text in self.texts:
            for token in text:
                if token in frequency:
                    frequency[token] += 1
                else:
                    frequency[token] = 1
        
        # remove words that have a frequency of 1
        self.texts = [[token for token in text if frequency[token] > 2] for text in self.texts]
        self.set_dict_corp(corpus_filepath, dictionary_filepath)
    

    def email_database_content(self):
        """
        Join each list in self.texts to form strings which can be later manipulated
        to be stored in the email database. 
        
        Need to do this if calling setEmailDatabase
        
        """
        self.texts = [' '.join(text) for text in self.texts]
        self.set_email_database()

    
    def save_texts(self, filepath):
        """
        Save self.texts to a file so we don't have to keep re-computing
        
        :param {str} filepath:
            Filepath of where to save information. 

        """
        # filepath = '../../../Enron/Texts/texts.txt'
        
        with open(filepath, 'wb') as save:
            pickle.dump(self.texts, save)
            
    
    def load_texts(self, filepath):
        """
        Load self.texts from a file it was saved to earlier.
        
        :param {str} filepath:
            Filepath of where to load information from. 

        """
        # filepath = '../../../Enron/Texts/texts.txt'
        
        with open(filepath, 'rb') as save:
            self.texts = pickle.load(save)
        print(len(self.texts))
    
    
    def load_dictionary(self, dictionary_location):
        """
        Load self.dictionary from a file it was saved to earlier. 

        :param {str} dictionary_location: 
            Filepath of where to load information from. 
        
        """
        # dictionaryLocation = '../../../Enron/LDAVar/dictionary.dict'
        self.dictionary = self.dictionary.load(dictionary_location)
    
    
    def load_corpus(self, corpus_location):
        """
        Load self.corpus from a file it was saved to earlier.
        
        :param {str} corpus_location: 
            Filepath of where to load information from. 

        """
        # corpusLocation = '../../../Enron/LDAVar/corpus.mm'
        self.corpus = corpora.MmCorpus(corpus_location)
            
            
    """
        TO-DO:
            For code meant to work with updating the corpus: analyze trade-off. 
                figure out if passing texts as parameter is better than just re-running 
                with complete self.texts
            If not: don't worry about it
    """
    def set_dict_corp(self, corpus_location, dictionary_location):
        """
            texts: container that has the lists of lists of strings for the dictionary
            
            :param {str} dictionary_location: 
                Filepath of where to load information from. 
            
            :param {str} corpus_location: 
                Filepath of where to load information from. 

            AT THE END OF THIS METHOD:
                self.dictionary will be updated with the new values
                self.corpus will have a new value that will be an updated version
                    of the previous one. 
                
            NOTE: if you make new dictionaries and corpuses (?) each time you run through this
                then the previous data will be lost. you want to keep all the data. 
                
            ISSUE: when updating the dictionary, new words may be introduced. that means in previous
                additions to the corpus those words that initially weren't there will only show up 
                for the latter ones. Dictionary is fine, corpus is not. 
        """
        self.dictionary.add_documents(self.texts) 
        # self.dictionary.save('../../../Enron/LDAVar/dictionary.dict')
        self.dictionary.save(dictionary_location)
        self.corpus = self.make_corpus()
        print(len(self.corpus))
        # don't need to serialize the corpus anymore b/c the data is in the email database
        #corpora.MmCorpus.serialize('../../../Enron/LDAVar/corpus.mm', self.corpus)
        corpora.MmCorpus.serialize(corpus_location, self.corpus)


    
    """ Maybe make an object out of this? Separate class maybe? """
    def make_corpus(self):
        """ 
        Make corpus 
        
        """
        return [self.dictionary.doc2bow(text) for text in self.texts]
    
    
    def get_domain(self, list_filtered_emails, email):
        """ 
        Find domain of the email. 
        
        :param {str} list_filtered_emails:
            List of filtered emails. 
        
        :param {line in database} email:
            One line in the database
        """
        
        if list_filtered_emails is None:
            return None
        try:
            domains = [re.search('@[\w.]+', e).group() for e in list_filtered_emails]
        except Exception as e:
            print(e)
            return None
        return domains
    
    
    def set_email_database(self):
        """
        Add the filtered content of each email and document in corpus to the email database.
        Now, don't need to serialize self.corpus: it's always in the email database
        
        NOTE: It doesn't matter that we're not iterating through the database in the correct numerical order!
        It's pulling the value from the corresponding index in self.texts
        
        """ 

        
        for email in self.col.find():
            try:
                self.col.update_one({'_id': email['_id']}, {'$set': {
                    'filtered_content': self.texts[email['email_counter']],
                    'email_corpus_value': self.corpus[email['email_counter']]}},  
    #                'sender_domain': self.getDomain(email['sender_email'], email), 
    #                'recipient_domain': self.getDomain(email['recipient_email'], email)}}, 
                    upsert = False)
            except IndexError:
                print(email['email_counter'])
                print(email['_id'])
                
    
    def fit_LDA(self, lda_filepath, pyldavis_filepath, num_topics):
        """ 
        Fit data in LDA. currently assuming that number of cores remains constant at 1. 
        
        :param {str} lda_filepath: 
            Where to save lda model to. 
            
        :param {str} pyldavis_filepath: 
            Where to save pyldavis model to. 
        
        :param {int} num_topics: 
            Number of topics the LDA model should look for. 
            
        """
        self.get_run_param()
        self.lda = ldamodel.LdaModel(corpus=self.corpus, alpha='auto', id2word=self.dictionary, num_topics=num_topics, 
                                     minimum_probability = 0.00, passes = 5, **self.run_parameters,)
        lda_vis_serialized = pyLDAvis.gensim.prepare(self.lda, self.corpus, self.dictionary, sort_topics = False)
#        pyLDAvis.save_html(lda_vis_serialized, '../../../Enron/Result/ldaModelDaRealOne.html')
        pyLDAvis.save_html(lda_vis_serialized, pyldavis_filepath)
        self.lda.save(lda_filepath)
    
    
    def save_LDA(self, lda_filepath):
        """ save lda model in the directory given by the filepath 
        
        :param {str} lda_filepath: 
            Filepath of where to save lda model to.

        """
        # self.lda.save('../../../Enron/LDAResult/ldaModel')
        self.lda.save(lda_filepath)
    
    
    def get_run_param(self):
        """
            This method will be used for generating the run parameters required
                this test. 
                Rachel used json.load(...). Ask her about it next Thurs
        """
            
        """ Just have simple input for user or they can just manually change code """
        #self.run_parameters = {'cores': 1} 
        self.run_parameters = {}
        
        
    def print_database(self):
        for email in self.col.find():
            print(email)
            print("\n")


if __name__ == "__main__":
    import argparse
    import sys
    if not len(sys.argv) > 1:
        raise ValueError("Whether or not creating new texts is a required argument")
    parser = argparse.ArgumentParser(description='Process texts')
    parser.add_argument('-x', required = True)
    parser.add_argument('-t', required = True)
    parser.add_argument('-l', required = True)
    parser.add_argument('-p', required = True)
    parser.add_argument('-n', required = True)
    parser.add_argument('-c', required = True)
    parser.add_argument('-d', required = True)
    args = parser.parse_args()
    tester = LDAModelMaker(create_texts = args.x, texts_filepath = args.t, corpus_filepath = args.c, dictionary_filepath = args.d)
    tester.fit_LDA(lda_filepath = args.l, pyldavis_filepath = args.p, num_topics = args.n)
    
    
#tester = LDAModelMaker()
#tester.load_texts('../../../Enron/Texts/texts.txt')