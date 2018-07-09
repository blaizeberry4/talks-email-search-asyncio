#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 20 15:46:20 2018

@author: Sanjana Kapoor
"""

#from store_data import EmailDataStorage 
from gensim import corpora
from gensim.corpora import Dictionary
from gensim.models import ldamodel
import pyLDAvis 
import pyLDAvis.gensim
import pickle
import re


class LDAModelMaker():
    
    def __init__(self, create, texts_filepath, corpus_filepath, dictionary_filepath, lda_filepath, pyldavis_filepath, 
                 database = None, **run_parameters):
        """
        Pull up information required for generating the LDA Model. 
        
        :param {boolean} create:
            Whether or not we must create texts. 
        
        :param {str} texts_filepath: 
            Either the location of where to load texts from or where we must save texts to. 
            Explained above. 
            
        :param {str} corpus_filepath: 
            Location of where we must save or load the corpus from. 
        
        :param {str} dictionary_filepath: 
            Location of where we must save or load the dictionary from. 
        
        :param {str} lda_filepath: 
            Location of where we must save the lda model to. 
            
        :param {str} pyldavis_filepath: 
            Location of where we must save the pyldavis to.
        
        :param {str} database: 
            Which kind of database we will be using. 
        """
        
        self.next_steps = {'mongo': self.mongo}
        
        self.texts_filepath = texts_filepath
        self.corpus_filepath = corpus_filepath
        self.dictionary_filepath = dictionary_filepath
        self.lda_filepath = lda_filepath
        self.pyldavis_filepath = pyldavis_filepath

        self.dictionary = Dictionary()
        self.run_parameters = run_parameters

        if create: 
            self.apply = self.create_corpus_dict
        else:
            self.apply = self.load_corpus_dict
            
        if database:
            self.database = self.next_steps[database]


    def create_corpus_dict(self, texts):
        """
        Save texts, dictionary, and corpus. Generate and save lda & pyldavis model. 
        
        :param {list[list[str]]} texts:
            Tokenized words
        
        """
        
        self.texts = texts
        self.save_texts()
        self.set_dict_corp()
        
        self.database()
        self.fit_LDA()
    
    
    def mongo(self):
        import os
        from pymongo import MongoClient
        
        emailClient = MongoClient()
        self.db = emailClient[os.getenv('EMAIL_DATABASE_NAME')]
        self.col = self.db[os.getenv('EMAIL_COLLECTION_NAME')]
        self.email_database_content()
    
    
    def load_corpus_dict(self, useless):
        self.texts = self.load_texts()
        self.dictionary = self.load_dictionary()
        self.corpus= self.load_corpus()
        self.fit_LDA()

    
    def save_texts(self):
        """
        Save self.texts to a file so we don't have to keep re-computing

        """
        with open(self.texts_filepath, 'wb') as save:
            pickle.dump(self.texts, save)
            
    
    def load_texts(self):
        """
        Load self.texts from a file it was saved to earlier.

        """
        with open(self.texts_filepath, 'rb') as save:
            self.texts = pickle.load(save)
#        print(len(self.texts))
    
    
    def load_dictionary(self):
        """
        Load self.dictionary from a file it was saved to earlier. 
        
        """
        self.dictionary = self.dictionary.load(self.dictionary_filepath)
    
    
    def load_corpus(self):
        """
        Load self.corpus from a file it was saved to earlier.

        """
        self.corpus = corpora.MmCorpus(self.corpus_filepath)
            
            
    """
        TO-DO:
            For code meant to work with updating the corpus: analyze trade-off. 
                figure out if passing texts as parameter is better than just re-running 
                with complete self.texts
            If not: don't worry about it
    """
    def set_dict_corp(self):
        """
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
        self.dictionary.save(self.dictionary_filepath)
        self.corpus = self.make_corpus()
#        print(len(self.corpus))
        corpora.MmCorpus.serialize(self.corpus_filepath, self.corpus)

    
    """ Maybe make an object out of this? Separate class maybe? """
    def make_corpus(self):
        """ 
        Make corpus 
        
        """
        return [self.dictionary.doc2bow(text) for text in self.texts]
    
    
    def fit_LDA(self):
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
        self.lda = ldamodel.LdaModel(corpus=self.corpus, alpha='auto', id2word=self.dictionary, **self.run_parameters)
        lda_vis_serialized = pyLDAvis.gensim.prepare(self.lda, self.corpus, self.dictionary, sort_topics = False)
        pyLDAvis.save_html(lda_vis_serialized, self.pyldavis_filepath)
        self.lda.save(self.lda_filepath)

    
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
    

    def email_database_content(self):
        """
        Join each list in self.texts to form strings which can be later manipulated
        to be stored in the email database. 
        
        Need to do this if calling setEmailDatabase
        
        """
        self.texts = [' '.join(text) for text in self.texts]
        self.set_email_database()
        
    
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
    print("THE SAVING HAS FINISHED")
    tester.fit_LDA(lda_filepath = args.l, pyldavis_filepath = args.p, num_topics = args.n)
    print('finished')
# tester = LDAModelMaker('False', '../../../Enron/Tester/original/texts.txt', '../../../Enron/Tester/original/corpus.mm', '../../../Enron/Tester/original/dictionary.dict')
#tester.fit_LDA('../../../Enron/Tester/ldamodel_topics_35_folder/ldamodel_topics_35', '../../)
#tester.load_texts('../../../Enron/Texts/texts.txt')