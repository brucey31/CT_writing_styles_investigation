# Culture Trip Articles and Writing Styles Investigation
-- Bruce Pannaman
[![N|Solid](https://lever-client-logos.s3.amazonaws.com/52aaf896-c74d-45bb-9429-1481df4377ec-1526046157413.png)](https://nodesource.com/products/nsolid)

To get into the editorial mindset of Culture Trip I wanted to see what differences there were in the articles, and other information about what is happening.

## Research Points
- Find out how many authors there are contribution to Culture trip, where they write for and how many articles each they have written?
- When is the key time of the year for Culture trip to create content?
- How has the bredth of cultures been written about during the company's history?
- Is there a distinctive **writing style** that defines Culture trip articles using the "[Elements of Writing Style](http://write-site.athabascau.ca/documentation/elements-of-style.pdf)" by Athabasca University

  
## Method
1. I used the sitemap.xml of the culture trip website and downloaded features from each url including the article itself, author, links and title
2. I parsed through and cleaned this data to get good article content data
3. EDA-ed the data and answered the easier of the questions
4. Added NLP features of the articles themselves (only took last 5 articles from authors with > 10 articles submitted)