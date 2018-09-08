__author__ = "Bruce Pannaman"

from bs4 import BeautifulSoup
import requests

class Article:
    def __init__(self, URL):
        self.URL = URL
        self.title = None
        self.author = None
        self.region = None
        self.country = None
        self.header_image = None
        self.date = None
        self.content = None
        self.links = None

        self.parse_article()
    
    def __str__(self):
        return """
            This is an object for a CT article and metadata associated with it
        """
    def get_page(self, url):
        response = requests.request("GET", url)
        assert response.status_code == 200, "Failed Call"
        return response.content

    def parse_article(self):
        if "article" not in self.URL:
            return None
        try:
            content = self.get_page(self.URL)
            soup = BeautifulSoup(content, 'html.parser')
            url_parts = self.URL.replace("https://theculturetrip.com/", "").split("/")
            url_parts = [x.replace("-", " ")for x in url_parts]
            for x, y in enumerate(url_parts):
                if x == "articles":
                    break
                else:
                    if x == 0:
                        self.region = y
                    if x == 1:
                        self.country = y
            # Title
            try:
                self.title = soup.title.string
            except AttributeError as e:
                self.title = None
            # Author
            self.author = soup.find("meta", {"name": "author"}).get("content")
            # Header Image
            try:
                self.header_image = soup.find("div", {"class": "flipboard-image"}).find("img").get("src")
            except AttributeError as e:
                self.header_image = None
            # Date
            try:
                self.date = soup.find("dd", {"class": "update-timestyled__UpdateTime-s1pucr1-0"}).string.replace("Updated: ", "")
            except AttributeError as e:
                self.date = None
            # Content
            #print(soup.find("div", {"id": "first-paragraph"}).string)
            content = ""
            content_paragraphs = soup.findAll("p", {"class": "paragraph-wraperstyled__ParagraphWrapper-s1xg03x1-0"})
            for paragraph in content_paragraphs:
                content += paragraph.getText() + "\n\n"
            self.content = content
            # Links
            link_list = []
            for paragraph in content_paragraphs:
                links = paragraph.findAll("a")
                if len(links) >0:
                    for link in links:
                        link_list.append({link.contents[0]: link.get("href")})
            
            self.links = link_list
            return

        except AssertionError as e:
            print("URL doesn't work - " + self.URL)
            print()
            return
        
    def add_to_DataFrame(self, df):
        df = df.append(self.__dict__, ignore_index=True)
        return df
        
    