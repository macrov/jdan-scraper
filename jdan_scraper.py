#!/usr/bin/python

import bs4
import requests
import pickle
import json
import re


JDAN_URL = "http://jandan.net"
JDAN_PIC_URL = "http://jandan.net/pic"

JDAN_VOTE_SUPPORT_PATTERN = "cos_support-\d+"
JDAN_VOTE_UNSUPPORT_PATTERN = "cos_unsupport-\d+"

JDAN_COOKIES_LOCAL = "jdan-cookies.pickle"

HEADER_TEMPLATE = "headers.pickle"

SAVES = "SAVES.json"


session = None
jdan_pic_largestPage = None
cookies = None
headers = None

proxyDict = {
        "http":"localhost:3128",
        "https":"localhost:3128"
        }


class PIC:
    def __init__(self, author, pic_url, support_votes, unsupport_votes):
        """docstring for __init__"""
        self.author = author
        self.pic_url = pic_url
        self.support_votes = support_votes
        self.unsupport_votes = unsupport_votes

def get_jdan_cookie_from_local(cookies_file_name): 
    cookies_file = open(cookies_file_name)
    cookies = pickle.load(cookies_file)
    return cookies

def get_headers_template_from_local(headers_file_name):
    headers_file = open(headers_file_name)
    headers = pickle.load(headers_file)
    return headers

def save_cookies(cookies,cookies_file_name):
    pickle.dump(cookies,open(cookies_file_name,'w'))

def initial_session():
    global headers,cookies,session
    headers = get_headers_template_from_local(HEADER_TEMPLATE)
    cookies = get_jdan_cookie_from_local(JDAN_COOKIES_LOCAL)
    session = requests.Session()

def close_session():
    save_cookies(session.cookies,JDAN_COOKIES_LOCAL)

def get_url(url):
    res = session.get(url,headers=headers,cookies=cookies,proxies=proxyDict)
    return res

def get_pic_page_by_page_number(pageNumber):
    url = JDAN_PIC_URL + "/" + "page-" + str(pageNumber)
    return get_url(url)

def get_largest_pic_page_number():
    res = get_url(JDAN_PIC_URL)
    bsObj = bs4.BeautifulSoup(res.text, "html.parser")
    largest_page_str = bsObj.find(class_='current-comment-page').get_text().strip('[]')
    largest_page = int(largest_page_str)
    return largest_page

def is_end_page(bsObj):
    cluse = u'\u5c31\u770b\u5230\u8fd9\u91cc\u4e86\u3002'
    if bsObj.find("h3",{"class":"title","src":cluse}):
        print "is end page"
        return True
    else :
        return False
def get_authors(bsObj):
    authors = []
    for author_block in bsObj:
        authors.append(author_block.find("strong").get_text())
    return authors
        
    

def get_votes(bsObj):
    support_votes = int(bsObj.find('span',{"id":re.compile(JDAN_VOTE_SUPPORT_PATTERN)}).get_text())
    unsupport_votes = int(bsObj.find('span',{"id":re.compile(JDAN_VOTE_UNSUPPORT_PATTERN)}).get_text())
    return (support_votes,unsupport_votes)

def get_pics_by_page_number(pageNumber):
    pics = []
    res = get_pic_page_by_page_number(pageNumber)
    #print res.text
    bsObj = bs4.BeautifulSoup(res.text,"html.parser")
    if is_end_page(bsObj):
        return []
    try:
        authors = get_authors(bsObj.findAll("li",{"id":re.compile("comment-\d+")}))
        for order,section in enumerate(bsObj.findAll(class_="text")):
            for pic in section.findAll("img"):
                img_src = None
                if pic.attrs.has_key('org_src'):
                    #pics.append(pic.attrs['org_src'])
                    img_src = pic.attrs['org_src']
                elif pic.attrs.has_key("src"):
                    #pics.append(pic.attrs['src'])
                    img_src = pic.attrs['src']
                support_votes,unsupport_votes = get_votes(section)
                picObj = PIC(authors[order],img_src,support_votes,unsupport_votes)
                pics.append(picObj)
        return pics
    except KeyError as e:
        print section
        print e

def save_scraping(pics):
    save_file = open("pics",'a')
    for line in pics:
        save_file.write(line.encode('utf-8'))
        save_file.write('\n')
    #save_file.writelines(pics)
    save_file.close()

def main_loop():
    initial_session()
    try:
        jdan_pic_largestPage =  get_largest_pic_page_number()
        page = jdan_pic_largestPage 
        pics = []
        while True:
            pics_tmp = get_pics_by_page_number(page)
            if len(pics_tmp) > 0:
                #save_scraping(pics_tmp)
                for picObj in pics_tmp:
                    print "author:%s  img:%s  s-v:%d  us-v:%d" %(picObj.author, picObj.pic_url, picObj.support_votes, picObj.unsupport_votes)
                pics.extend(pics_tmp)
                page = page - 1
            else:
                break
        print "**********scraping end*******************"
        print "*********page total: %d *****************" % (jdan_pic_largestPage - page)
        print "*********pic total: %d ******************" % len(pics)
            
    finally:
        close_session()

main_loop()
