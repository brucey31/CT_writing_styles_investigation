__author__ = "Bruce Pannaman"

import csv
import pandas as pd
import requests
from lxml import etree
from io import StringIO
from src.Article import Article
import random
import json
import numpy as np
from datetime import datetime
import multiprocessing as mp
import sys
import uuid
from tqdm import tqdm
import os
sys.setrecursionlimit(100000)

staging_folder_name = "files"

def article_to_dataframe_parsing(article):
        now = datetime.now()
        try:
            os.mkdir(staging_folder_name)
        except Exception as e:
            print("Staging Folder already made")
        try:
            return_obj = Article(article).__dict__
            # print("Finished article - " + article)
            if return_obj["title"] is None or len(return_obj) < 1:
                return_obj={}
        except Exception as e:
            return_obj = {}
        F = open("%s/%s" % (staging_folder_name, uuid.uuid4().hex,"w"))
        F.write(json.dumps(return_obj))
        del F
        del return_obj
        del now


class WebsiteScraper:
    
    def __init__(self, threads=100):
        self.root_xml = "https://theculturetrip.com/sitemap.xml/"
        self.article_URL_dictionary = []
        self.dataframe = None
        self.num_articles = 0
        self.urls_csv_filename = "CT_urls.csv"
        self.article_df_filename = "CT_article_dataframe.csv"
        self.processes = threads
        self.multithreaded_article_count = 0
    
    def __str__(self):
        return """
            This class aims to pull down all articles and interesting paragraphs from 
            the website
        """
    
    def get_page(self, url):
        response = requests.request("GET", url)
        assert response.status_code == 200, "Failed Call"
        return response.content
    
    
    def save_to_csv(self, name, listo):
        file = open(name,'w')

        for item in listo:
            file.write(item + "\n")
        
    def read_from_csv(self, filename):
        try:
            file = open(filename,'r')
            reader = csv.reader(file)
            urls = []

            for row in reader:
                urls = urls + row
            self.article_URL_dictionary = urls
            return True

        except FileNotFoundError as e:
            return False
         
        
    def sitemap_urls(self, xml_text, articles_only=True):
        """
        Gets URLs from a sitemap
        """
        tree = etree.fromstring(xml_text)
        
        xmlDict = []
        for sitemap in tree:
            children = sitemap.getchildren()
            for field in children:
                if "http" in field.text:
                    if articles_only and "article" in field.text:
                        xmlDict.append(field.text)
                    if articles_only is False:
                        xmlDict.append(field.text)
        return xmlDict
        
        
    def get_web_page_dictionary(self, verbose=False, articles_only=True):
        """
        Helped from here:
        https://stackoverflow.com/questions/31276001/parse-xml-sitemap-with-python
        
        """
        
        if self.read_from_csv(self.urls_csv_filename) is False:
            child_xmls = self.sitemap_urls(self.get_page(self.root_xml), articles_only=False)

            for iterator, child in enumerate(child_xmls):
                try:
                    new_urls = self.sitemap_urls(self.get_page(child), articles_only=articles_only)
                    self.article_URL_dictionary = self.article_URL_dictionary + new_urls
                except etree.XMLSyntaxError as e:
                    continue
                if iterator % 10 == 0 & verbose:
                    print("At xml # " + str(iterator) + " out of " + str(len(child_xmls)))

            self.save_to_csv(self.urls_csv_filename, self.article_URL_dictionary)
        else:
            print("Loading from backup CSV")
        self.num_articles = len(self.article_URL_dictionary)
        print("Loaded up with %s urls" % str(self.num_articles))
        return
    
    def parse_to_dataframe(self, num_articles_rendered = None, multithreaded=True):
        """
        Uses the Article Class to scrape the articles down, parses and amends them to the inputted
        dataframe
        
        num_articles_rendered: This takes a random sample of X article URLS and builds your dataframe from this random sample
        multithreaded: I hate waiting so the class has a multithread pool to distribute the work - influenced by https://stackoverflow.com/questions/33242439/multiprocessing-pool-return-results-as-available

        """
        def article_to_dataframe_parsing_single_thread(article):
                article_obj = Article(article)
                self.dataframe = article_obj.add_to_DataFrame(self.dataframe)

        if num_articles_rendered is None or not isinstance(num_articles_rendered, int):
            num_articles_rendered = int(self.num_articles)
            url_list = self.article_URL_dictionary
        else:
            url_list = []
            for x in range(num_articles_rendered):
                url_list.append(self.article_URL_dictionary[random.randint(0,self.num_articles)])
        
        # Create new DataFrame
        article_1 = Article(self.article_URL_dictionary[2])
        column_list = [x for x in article_1.__dict__]
        self.dataframe = pd.DataFrame(columns = column_list)
        
        # Fill it
        print("Sample size = " + str(num_articles_rendered))
        
        if multithreaded:
            process_list = []
            for x in self.article_URL_dictionary[:num_articles_rendered]:
                process_list.append(x)
                if len(process_list) >= self.processes:
                    threadpool = mp.Pool(self.processes)
                    article_list_batch = []
                    threadpool.map_async(article_to_dataframe_parsing, process_list)
                    # output = threadpool.map(article_to_dataframe_parsing, self.article_URL_dictionary[:num_articles_rendered])
                    # print("Finished the threads, parsing output")
                    # for row in output:
                    #     self.dataframe = self.dataframe.append(row, ignore_index=True)
                                
                    threadpool.close()
                    threadpool.join()
                    process_list = []

        else:
            timing_list = []
            for i, article in enumerate(url_list):
                now = datetime.now()
                if i % 10 == 0:
                    print("At Article %s of %s articles" % (i, len(url_list)))
                    print("Taking on average %s seconds per article" % round(np.mean(timing_list),3))
                article_to_dataframe_parsing_single_thread(article)
                timing_list.append((datetime.now()- now).seconds)
        self.compile_file()
        
        def compile_file(self):
            file1 = open(self.article_df_filename, "w")
            writer = csv.writer(file1)

            writer.writerow(["URL", "title", "author", "region", "country", "header_image", "date", "content", "links"])

            for filename in tqdm(os.listdir(staging_folder_name)):
                if filename != ".DS_Store":
                    file = open("%s/%s" % (staging_folder_name, filename), "r")
                    file = file.read()
                    try:
                        content = json.loads(file)
                        writer.writerow([content["URL"],
                            content["title"],
                            content["author"],content["region"],
                            content["country"],content["header_image"],
                            content["date"], content["content"].replace("\n", "").replace(",", ""), 
                            content["links"]])


                    except (json.decoder.JSONDecodeError, KeyError) as e:
                        continue

