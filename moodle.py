"""
# Moodle downloader for Concordia University

## HOW TO USE?

$ scrapy runspider \
        -a usr=[YOUR USERNAME] \
        -a pwd=[YOUR PASSWORD] \
        -a root_dir=/home/user/Desktop/School/Moodle/ \
    moodle

### Filter by course name

$ scrapy runspider \
        -a usr=[YOUR USERNAME] \
        -a pwd=[YOUR PASSWORD] \
        -a root_dir=/home/user/Desktop/School/Moodle/ \
        -a course=SOEN\ 6431 \
    moodle

## DEPENDENCIES

$ pip install scrapy
"""
import os
import urlparse

from scrapy import Spider, Request, FormRequest


class MoodleSpider(Spider):
    name = 'moodle'
    start_urls = ('https://moodle.concordia.ca/moodle/login/index.php',)

    def parse(self, response):
        return FormRequest.from_response(response,
                formdata={'username': self.usr, 'password': self.pwd},
                callback=self.parse_courses)

    def parse_courses(self, response):
        for url in response.css('.block_course_list_conu a'):
            name = url.xpath('text()').extract_first()
            url = url.xpath('@href').extract_first()
            if hasattr(self, 'course'):
                if self.course in name:
                    yield Request(url, callback=self.parse_course_page,
                            meta={'course': name})
                    break
            else:
                yield Request(url, callback=self.parse_course_page,
                                meta={'course': name})

    def parse_course_page(self, response):
        for week in response.css('ul.weeks > li'):
            section_name = week.css('h3.sectionname > span::text').extract_first()
            path = self.root_dir + response.meta['course'] + '/' + section_name
            try:
                os.makedirs(path)
            except OSError as e:
                pass
            # resources are downloadable files
            for res in week.xpath('.//a[contains(@href, "resource/view.php")]'):
                name = res.css('span::text').extract_first()
                url = res.xpath('@href').extract_first()
                yield Request(url, callback=self.download,
                        meta={'name': name, 'path': path})

    def download(self, response):

        def getFileName(url, headers):
            if 'Content-Disposition' in headers:
                cd = dict(map(
                    lambda x: x.strip().split('=') if '=' in x else (x.strip(),''),
                    headers['Content-Disposition'].split(';')))
                if 'filename' in cd:
                    filename = cd['filename'].strip("\"'")
                    if filename: return filename
            return os.path.basename(urlparse.urlsplit(url)[2])

        with open(response.meta['path'] + '/' + getFileName(response.url, response.headers), 'wb') as f:
            f.write(response.body)
