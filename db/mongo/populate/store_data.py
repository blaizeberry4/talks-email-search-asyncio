#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 20 11:28:42 2018

@author: s0k00rp
"""
import os
import csv
import io
import re
from pymongo import MongoClient
import sys
import pymongo



class EmailDataStorage():
    """ 
    Object made to store data in a database
    
    """
    
    
    def __init__(self, filepath):
        """
        Create the database for the emails
        
        :param {str} filepath:
            Filepath to the current set of data being added to the database
        
        """
        emailClient = MongoClient()
        self.db = emailClient['JohnEnronEmailData']
        self.emails = self.db.emails
        self.currPath = filepath
    

    def move_data(self):
        """
        Read the data from the CSV files and move it into a database
        
        :local {list} files:
            Container that stores all the Enrom Email .csv files
            
        """
        num_row = 0
        num_added = 0
        files = os.listdir(self.currPath)
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
                                num_added += 1
                                self.add_data(row)
                        # if something can't be read, we should ignore that row and
                        # keep going with the rest of the file
                        except pymongo.errors.DuplicateKeyError:
                            print("Duplicate Key Eror")
                        except IndexError:
                            pass
                except csv.Error as e:
                    print(e)
                    print ("error")
                    print(row)
                    print(email_file)
                    

#                    except Exception as e:
#                        print(e)
#                        pass
        print("The total number of rows in the .csv files"  + str(num_row))
        print("The total number of rows added to the database from the .csv files " + str(num_added))
  
    
    def add_data(self, row):
        """
        Put the data in the database. Multiple parts to each row. 
        
        :param {tuple} row:
            Tuple of values that contain the information about a specific email. 
        
        :local {dict} email_data:
            Dict that contains values for a new row in the database. 
        
        """
        
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
            'content': self.clean_content(row[13]),
            'email_counter': eval(row[0]), 
        }
        self.emails.insert_one(email_data)


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
            x = row[index].replace("frozenset({","[").replace("})","]")
            x = eval(x)
            return x
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
        

#client = MongoClient()
#client.drop_database('EnronEmailData')

if __name__ == "__main__":
    if not len(sys.argv) > 1:
        raise ValueError("Path to email CSV directory is a required argument.")
    quickTest = EmailDataStorage(sys.argv[1])
    quickTest.move_data()