# -*- coding: utf-8 -*-
"""
Created on Wed May 16 09:36:13 2018

@author: rein9
"""

import scrapy
from insta_crawl.items import InstaCrawlItem

import scrapy
from bs4 import BeautifulSoup
from scrapy import Request
from scrapy.exceptions import CloseSpider
import urllib.request
import json
import re
import os
import datetime

article_list_re = re.compile('var msgList = (.*?)}}]};')

class CrawlerSpider(scrapy.Spider):
    #spider name, has to be unique to be called
    name = 'crawler'
    '''
    A method os spider, when called, pass the "response" of the
    starting url as the argument.
    when the method finishes parsing the response data, generate item
    and further generate objects for the next request
    '''
    def __init__(self, account='', videos='', timestamp='', *args, **kwargs):
        super(CrawlerSpider, self).__init__(*args, **kwargs)
        self.videos = videos
        self.account =account
        if account == '':
            self.account = input("Name of the account ?")
        if videos == '':
            self.videos = input("Download the video ? (y/n)")
        if timestamp == '':
            timestamp = input("Add timestampe ? (y/n)")
        self.start_urls = ["https://www.instagram.com/" + self.account]
        self.savedir = "@" + self.account
        if timestamp == "y":
            self.savedir = self.getCurrentTime() + self.savedir
        if not os.path.exists(self.savedir):
            os.makedirs(self.savedir)
        self.checkpoint_path = os.path.join(self.savedir, '.checkpoint')
        self.readCheackpoint()

    def parse(self, response):
# =============================================================================
#        raise Exception('WZ: EEE')
#        soup = BeautifulSoup(response.text, features='lxml')
#        info = soup.find_all('script', {'src': re.compile('.*.jpg')})
#        profile_link = soup.find_all(uigs = 'account_image_0')[0]['href']
#        file = open('./img_info.txt', 'w')
#        file.write('Image :' + info[0].string + '\n')
#        file.write(profile_link)
#        file.close()
#        yield Request(profile_link, callback = self.parse_profile)
# =============================================================================
        request = Request(response.url, callback = self.parse_profile)
        yield request

    def parse_profile(self, response):
# =============================================================================
#       parse the page to see if a photo or video exists
# =============================================================================
        #<script type="text/javascript">window.__initialDataLoaded(window._sharedData);</script>
        js = response.selector.xpath('//script[contains(.,"window._sharedData")]/text()').extract()
#        print(js)
        js = js[0].replace("window._sharedData = ", "")
        jscleaned = js[:-1]
        log = open(self.account + 'log', 'w')
        log.write(js)
        log.close()

        loc = json.loads(jscleaned)
#        print("location information:", loc["entry_data"]["ProfilePage"][0])
        user = loc["entry_data"]["ProfilePage"][0]["graphql"]["user"]
        if user["is_private"]:
            print("Access Denied, Private Account");
            return

        has_next = user["edge_saved_media"]["page_info"]["has_next_page"]
        medias = user["edge_owner_to_timeline_media"]["edges"]

        if not hasattr(self, 'starting_shorcode') and len(medias):
            self.starting_shorcode = medias[0]['node']['shortcode']
            filename = self.checkpoint_path
            f = open(filename, 'w')
            f.write(self.starting_shorcode)

        # photo parsing
        for media in medias:
            node = media["node"]
            url = node["display_url"]
            id = node["id"]
            type = node["__typename"]
            code = node["shortcode"]
            if(self.checkAlreadyScraped(code)):
                return

            if type == "GraphSidecar":
                print("request url for sidecar is: ", "https://www.instagram.com/p/" + code)
                yield Request("https://www.instagram.com/p/" + code, callback=self.parse_sideCar)

            elif type == "GraphImage":
                print("request url for graphimage is: ", "https://www.instagram.com/p/" + code)
                yield Request(url, meta = {"id": id, "extension": ".jpg"}, callback = self.save_media)

            elif type == "GraphVideo" and self.videos =="y":
                yield Request("https://www.instagram.com/p/" + code, callback=self.parse_graphVideo)

        if has_next:
            print("has next page")
            end_cursor = user["edge_saved_media"]["page_info"]["end_cursor"]
            url = "https://www.instagram.com/p/" + self.account + "/?max_id=" + end_cursor
            yield Request(url, callback = self.parse_profile)#recursively requesting for the next page

    def parse_sideCar(self, response):
# =============================================================================
#         parse the page with photo
#"edge_sidecar_to_children":{"edges":[{"node":{"__typename":"GraphImage","id":"1861575656606717611","shortcode":"BnVpTJWjtar","dimensions":{"height":1079,"width":1080},"gating_info":null,"media_preview":null,"display_url":"https://scontent-lax3-2.cdninstagram.com/vp/cd71bb1907c8db72bd38353cd6372481/5C15244B/t51.2885-15/e35/40072022_1303023659834379_3971085169526358205_n.jpg","display_resources":[{"src":"https://scontent-lax3-2.cdninstagram.com/vp/a0ba1fbfaf473aad1959d332f42e275f/5C3715F1/t51.2885-15/sh0.08/e35/s640x640/40072022_1303023659834379_3971085169526358205_n.jpg","config_width":640,"config_height":639}
# =============================================================================
        js = response.selector.xpath('//script[contains(., "window._sharedData")]/text()').extract()
        js = js[0].replace("window._sharedData = ", "")
        jscleaned = js[:-1]
        log = open(self.account + 'logcar', 'w')
        log.write(js)
        log.close()

        photo = json.loads(jscleaned)
        photo = photo["entry_data"]["PostPage"][0]

        edges = photo["graphql"]["shortcode_media"]["edge_sidecar_to_children"]["edges"]
        for edge in edges:
            url = edge["node"]["display_url"]
            id = edge["node"]["id"]
            yield Request(url, meta = {"id": id, "extension": ".jpg"}, callback = self.save_media)

    def parse_graphVideo(self, response):
# =============================================================================
#         `parse the video information
# =============================================================================
        id = response.url.split("/")[-2]
        js = response.selector.xpath('//meta[@property="og:video"]/@content').extract()
        print("xpath from parsing video content", js)
        url = js[0]
        #Download the video
        yield Request(url, meta={"id": id, "extension" :".mp4"}, callback=self.save_media)

    def readCheackpoint(self):
        filename = self.checkpoint_path
        if not os.path.exists(filename):
            self.last_crawled = ''
            return
        self.last_crawled = open(filename).readline().rstrip()

    def checkAlreadyScraped(self,shortcode):
        return self.last_crawled == shortcode

    def save_media(self, response):
# =============================================================================
# download the photo and videos from the parsed url
# =============================================================================
        print("URL for Photo and Videos: " + response.url)
        file = os.path.join(self.savedir, response.meta["id"] + response.meta["extension"])
        urllib.request.urlretrieve(response.url, file)

    def getCurrentTime(self):
        now = datetime.datetime.now()
        return now.strftime("%Y-%m-%d-%H:%M")

    def get_article(self, response):
        soup = BeautifulSoup(response.text, features="lxml")
        title = soup.select(".rich_media_title")
        print("title" + str(len(title)))
        if not title:
            return
        item = InstaCrawlItem()
        item['title'] = title[0].get_text()
        item['link'] = response.url
        item['content'] = response.text

        title = title[0].get_text()

        title = title.strip("\r").strip("\n").strip(" ")
        file = open("./content/%s" % title, "w")
        file.write(item["content"])
        file.close()

    @staticmethod
    def __replace_str_html(content):
        transfer = [
            ('&#39;', '\''),
            ('&quot;', '"'),
            ('&amp;', '&'),
            ('amp;', ''),
            ('&lt;', '<'),
            ('&gt;', '>'),
            ('&nbsp;', ' '),
            ('\\', '')
        ]
        for item in transfer:
            content = content.replace(item[0], item[1])
        return content


class HashSpider(scrapy.Spider):
    name = "hashcrawl"
    def __init__(self, timestamp = '', hashtag = ''):
        self.hashtag = hashtag
        if hashtag == '':
            self.hashtag = input("Name of the hashtag ?")
        if timestamp == '':
            timestamp = input("Add timestampe ? (y/n)")

        self.start_urls = ["https://www.instagram.com/explore/tags/"+self.hashtag+"/?__a=1"]
        self.savedir = "#" + self.hashtag
        if timestamp == "y":
            self.savedir = self.getCurrentTime() + self.savedir

        if not os.path.exits(self.savedir):
            os.makedirs(self.savedir)
        self.checkpoint_path = self.savedir + '.checkpoint'
        self.readCheackpoint()

    def readCheackpoint(self):
        filename = self.checkpoint_path
        if not os.path.exists(filename):
            self.last_crawled = ''
            return
        self.last_crawled = open(filename).readline().rstrip()

    def parse(self, response):
# =============================================================================
#        raise Exception('WZ: EEE')
#        soup = BeautifulSoup(response.text, features='lxml')
#        info = soup.find_all('script', {'src': re.compile('.*.jpg')})
#        profile_link = soup.find_all(uigs = 'account_image_0')[0]['href']
#        file = open('./img_info.txt', 'w')
#        file.write('Image :' + info[0].string + '\n')
#        file.write(profile_link)
#        file.close()
#        yield Request(profile_link, callback = self.parse_profile)
# =============================================================================
        yield Request(response.url, callback = self.parse_profile)

    def parse_hashtag(self, response):
# =============================================================================
#         process hastag parsing request
# =============================================================================
        js = json.loads(response.text)
        has_next = js["graphql"]["hashtag"]["edge_hashtag_to_media"]["page_info"]["has_next_page"]
        edges = js["graphql"]["hashtag"]["edge_hashtag_to_media"]["edges"]

        if not hasattr(self, "starting_shortcode") and len(edges):
            self.starting_shortcode = edges[0]["node"]["shortcode"]
            filename = self.checkpoint_path
            f = open(filename, "w")
            f.write(self.starting_shortcode)
        for edge in edges:
            node = edge["node"]
            shortcode = node["shortcode"]
            if self.checkAlreadyScraped(shortcode):
                return
            yield Request("https://www.instagram.com/p/"+shortcode+"/?__a=1", callback = self.parsepost)
        if has_next:
            end_cursor = js["graphql"]["hashtag"]["edge_hashtag_to_media"]["page_info"]["end_cursor"]
            yield Request("https://www.instagram.com/explore/tags/"+self.hashtag+"/?__a=1&max_id="+end_cursor, callback=self.parse_htag)

    def checkAlreadyScraped(self,shortcode):
        return self.last_crawled == shortcode

    def parse_post(self, response):
# =============================================================================
#         TO Be implemented
# =============================================================================
        js = json.loads(response.text)
        media = js['graphql']['shortcode_media']
        location = media.get('location', {})

        if location is not None:
            loc_id = location.get('id', 0)
            request = scrapy.Request("https://www.instagram.com/explore/locations/"+loc_id+"/?__a=1",
                                     callback=self.parse_post_loc, dont_filter=True)
            request.meta['media'] = media
            yield request
        else:
            media['location'] = {}
            yield self.makePost(media)

    def parse_post_loc(self, response):
        media = response.meta['media']
        location = json.loads(response.text)
        location = location['location']
        media['location'] = location
        yield self.makePost(media)

    def makePost(self, media):
        location = media['location']
        caption = ''
        if len(media['edge_media_to_caption']['edges']):
            caption = media['edge_media_to_caption']['edges'][0]['node']['text']
        return PostItem(id=media['id'],
                    shortcode=media['shortcode'],
                    caption=caption,
                    display_url=media['display_url'],
                    loc_id=location.get('id', 0),
                    loc_name=location.get('name',''),
                    loc_lat=location.get('lat',0),
                    loc_lon=location.get('lng',0),
                    owner_id =media['owner']['id'],
                    owner_name = media['owner']['username'],
                    taken_at_timestamp= media['taken_at_timestamp'])

    def getCurrentTime():
        now = datetime.datetime.now()
        return now.strftime("%Y-%m-%d-%H:%M")