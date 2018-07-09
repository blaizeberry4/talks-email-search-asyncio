#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 20 11:28:42 2018

@author: Sanjana Kapoor
"""

import sys
import os


class EmailDataStorage():
    """ 
    Object made to store data in a database
    
    """
    
    
    def __init__(self, reading_process = 'csv', database = 'mongo'):
        """
        Create the database for the emails
        
        :param {str} filepath:
            Filepath to the current set of data being added to the database
        
        """
        
        self.next_step = {'csv': self.csv, 
                         'mongo': self.mongo}
        
        self.apply = self.next_step[reading_process]
        self.store = self.next_step[database]
        
        self.result = []
        
        
    def csv(self, filepath):
        """
        Read in data from .csv files. 
        
        :param {str} filepath:
            Filepath to the current set of data being added to the database
        
        """
        
        import csv
        import io
        
        num_row = 0
        num_added = 0
        files = [f for f in os.listdir(filepath) if f.endswith('.csv')]
        csv.field_size_limit(sys.maxsize)
        for email_file in files:
            email_file = self.currPath + "/" + email_file
            # utf-8 doesn't read properly
            with io.open(email_file, 'rU', newline = '', encoding = "ISO-8859-1", errors='ignore') as csvfile: 
                mult_emails = csv.reader(csvfile)
                try: 
                    for row in mult_emails:
                        num_row += 1
                        try:
    #                        if row[0] != '' and row[1][0] == '<':
                            if row[0] != '' and row[0].isdigit():
                                if row[0] != num_added:
                                    raise IndexError('the email_counter and the actual counter do not match up')
                                    quit
                                num_added += 1
                                self.store(row)
                        # if something can't be read, we should ignore that row and
                        # keep going with the rest of the file
                        except IndexError:
                            pass
                        except UnicodeEncodeError as e:
                            print(e)
                            print("this is the number of docs we were able to add")
                            print(num_added)
                except csv.Error as e:
                    print(e)
                    print("error")
                    print(row)
                    print(email_file)
        print("The total number of rows in the .csv files"  + str(num_row))
        print("The total number of rows added to the database from the .csv files " + str(num_added))
        
        return self.result
        

    
    def mongo(self, row):
        """
        Put the data in the database. Multiple parts to each row. 
        
        :param {tuple} row:
            Tuple of values that contain the information about a specific email. 
        
        :local {dict} email_data:
            Dict that contains values for a new row in the database. 
        
        """
        
        from pymongo import MongoClient
        import pymongo
        
        emailClient = MongoClient()
        emailClient.drop_database(os.getenv('EMAIL_DATABASE_NAME'))
        self.db = emailClient[os.getenv('EMAIL_DATABASE_NAME')]
        self.emails = self.db[os.getenv('EMAIL_COLLECTION_NAME')]
        
        content = self.clean_content(row[13])
        
        try: 
            email_data = {
                '_id': row[1].lstrip('<').rstrip('>'), # this is the message id
                'date': row[2],
                'sender': row[6],
                'sender_email': self.clean_emails(row, True),
                'recipient': row[7], 
                'recipient_email': self.clean_emails(row, False), 
                'subject': row[5], 
                'cc': row[8], 
                'bcc': row[9], 
                'content': content,
                'email_counter': eval(row[0]), 
            }
            self.emails.insert_one(email_data)
            self.result.append(content)
        
        except pymongo.errors.DuplicateKeyError:
            print("Duplicate Key Error")
        


    def clean_emails(self, row, sender_recip):
        """
        Clean the email addresses
        
        TO-DO: FIgure out why changing code to list(eval(row)) results in an error.
        
           ' change code to list(eval(row)). This will change the method to return
            a list instead of a long string of emails. '
        
        :param {tuple} row:
            Tuple of values that contain the information about a specific email. 
            
        :param {boolean} sender_recip:
            Indicates whether or not this is the sender's email or recipient's email
        
        """
        if sender_recip:
            index = 3
        else:
            index = 4
        try: 
            list_emails = "[" + row[index].lstrip("frozenset({","[").rstrip("})","]") + "]"
            list_emails = eval(list_emails)
            return list_emails
        except Exception as e:
            return row[index + 3]
    

    def clean_content(self, unfiltered_content):
        """
        Remove =20's from row. Not required to understand the meaning of the message.
        Should remove because it just clutters the content
        
        :param {str} unfiltered_content: 
            Content of one (singular) email
        
        """
        cleaned_content = unfiltered_content.replace('=20', '').replace('=09', '').strip()
        return cleaned_content
        

if __name__ == "__main__":
    import argparse
    if not len(sys.argv) > 1:
        raise ValueError("Path to email CSV directory is a required argument.")
    parser = argparse.ArgumentParser(description='Save data')
    parser.add_argument('-r', required = True)
    parser.add_argument('-s', required = True)
    parser.add_argument('-f', required = True)
    args = parser.parse_args()
    quickTest = EmailDataStorage(reading_process = args.r, storing_process = args.s)
    quickTest.apply(filepath = args.f)
