import os
import threading
import urllib.parse
import requests
import html
import math

# -----> USER INPUT VARIABLES
main_url = input("Enter the Confluence website you would like to scan (Ex. wiki.contoso.com): ").strip()
space = input("Enter the Confluence space key you would like to scan (Ex: HSDS, DataWorks): ").strip()
confluence_token = input("Go to https://{}/plugins/personalaccesstokens/usertokens.action > Create token\nPaste your Personal Access Token here: ".format(main_url)).strip()

# -----> DECLARE VARIABLES
confluence_headers = {"Accept": "application/json", "Authorization": "Bearer {}".format(confluence_token)}
pages_dict = {}
links_dict = {}
broken_dict = {}
urls = []
pages = []
bad_links = []
bypass_auth_list = []
o_lines = ""
breaker = "-------------------------------------------------------"
lookup_url_count = 0
extract_pages_count = 0

# -----> Grab lookup info
def authenticate():
    global response
    _url = 'https://{}/pages/listpages-alphaview.action?key={}&startsWith=&startIndex=0'.format(main_url, space)
    print("Authenticating into {}...".format(main_url))
    response = requests.request("GET", _url, headers=confluence_headers)
    if response.status_code != 200:
        quit(response.status_code)
    print("\tAccess granted. Hello {}!\n{}".format(response.headers['X-AUSERNAME'], breaker))
    return response

# -----> Grab page info
def create_urls(_response):
    global lookup_url_count
    html_index = 0
    print("Getting lookup urls...")
    for lookup_line in _response.text.split('\n'):
        if '<li><a href="listpages-alphaview.action?key={}&amp;startsWith=&amp;startIndex='.format(space) in lookup_line and int(lookup_line.strip().replace('&amp;', '&').split('startIndex=')[-1].split('">')[0]) >= html_index:
            html_index = int(lookup_line.strip().replace('&amp;', '&').split('startIndex=')[-1].split('">')[0])
    for start_index in range(0, html_index + 1, 30):
        lookup_url_count += 1
        url = 'https://{}/pages/listpages-alphaview.action?key={}&startsWith=&startIndex={}'.format(main_url, space, start_index)
        urls.append(url)
    validate_html = math.ceil(float(html_index + 1) / 30)

    # VALIDATION
    if validate_html == lookup_url_count:
        print("\tSUCCESS")
        print('{}'.format(breaker))
        return urls

def create_pages_dict(_urls):
    print("Extracting page names and links...")
    threads = []
    for _index in range(len(_urls)):
        x = threading.Thread(target=extract_pages, args=(_index,))
        threads.append(x)
        x.start()

    for thread in threads:
        thread.join()

    if extract_pages_count == len(pages):
        print("\tSUCCESS")
        print('{}'.format(breaker))
        return pages_dict

def extract_pages(index):
    global extract_pages_count
    responser = requests.request("GET", urls[index], headers=confluence_headers)
    if responser.status_code != 200:
        quit(responser.status_code)
    print("\tCompleted page {}/{}".format(index, len(urls)))
    r_list = responser.text.split('\n')
    for items in r_list:
        if (
                '<a  href="/display/{}'.format(space) in items
                or '<a  href="/pages/viewpage.action?pageId=' in items
        ):
            extract_pages_count += 1
            page_name = html.unescape(items.strip().split('>')[-2].split('<')[0].replace(' ', '+')).replace('%20', '+')
            page_link = items.strip().split('href="')[1].split('">')[0]
            pages.append(page_name)
            pages_dict[page_name] = page_link

# -----> Grab link info
def create_links_dict(_pages_dict):
    print("Getting links...")
    for page_name, link in _pages_dict.items():
        crawling_page = 'https://{}/display/{}/{}'.format(main_url, space, page_name)
        page_id = _pages_dict[page_name].split('=')[-1]
        _url = 'https://{}/rest/api/content?title={}&spacekey={}&expand=space,body.view,version,container'.format(main_url, page_name, space)
        if page_id.isdigit():
            _url = 'https://{}/rest/api/content/{}?expand=space,body.view,version,container'.format(main_url, page_id)
        else:
            _url = convert_name_to_page_id(_url)
        _response = requests.request("GET", _url, headers=confluence_headers)
        if _response.status_code != 200:
            _url = 'https://{}/rest/api/content?title={}&spacekey={}&expand=space,body.view,version,container'.format(main_url, page_name, space)
            _response = requests.request("GET", _url, headers=confluence_headers)
        r_json = _response.json()
        html_body = []
        if 'content?title=' in _url and r_json['results']:
            for index in range(len(r_json['results'])):
                html_body.append(r_json['results'][index]['body']['view']['value'].replace('><', '>\n<').split('\n'))
        else:
            html_body.append(r_json['body']['view']['value'].replace('><', '>\n<').split('\n'))
        print('\n~{}'.format(crawling_page))
        for chunk in html_body:
            for line in range(len(chunk)):
                extract_links(crawling_page, chunk, line)

    print('{}'.format(breaker))
    return links_dict

def convert_name_to_page_id(_url):
    _response = requests.request("GET", _url, headers=confluence_headers)
    try:
        r_json = _response.json()
        for index in range(len(r_json['results'])):
            if r_json['results'][index]['space']['key'] == space:
                page_id = r_json['results'][index]['id']
                return 'https://{}/rest/api/content/{}?expand=space,body.view,version,container'.format(main_url, page_id)
        return _url
    except:
        return _url

def extract_links(crawling_page, chunk, line):
    _line = chunk[line]
    # WHITELISTS WEBSITES
    site = urllib.parse.unquote(html.unescape(_line)).split('href="')[-1].split('"')[0]

    if 'safelinks.protection.outlook.com' in site:
        # CONVERT OUTLOOK SAFE LINKS TO RAW LINKS
        site = urllib.parse.unquote(site.split('url=')[-1].split('%2F&amp;data=')[0].replace('%3A', ':').replace('%2F', '/'))
    # !!!ADD FILTERS HERE!!!!
    if (
            'href="http' in _line
            and 'http' in _line.split('href="')[-1].split('"')[0]
            and 'localhost:' not in site.lower()
            and not site.split('/')[2].replace('.', '').replace(':', '').isdigit()  # FILTERS OUT IP ADDRESS LINKS
    ):
        # PARSE RAW CONTENT
        try:
            link_text = html.unescape(_line.split('rel="nofollow">')[-1].split('<')[0])
        except:
            link_text = ""
        if link_text == "":
            link_text = html.unescape(extract_span_text(_line, chunk))
        if '.' in site:
            if site.split('.')[-1] not in ['id', 'id/', 'name', 'name/']:
                website = html.unescape(site).replace('%20', '+').replace(' ', '+')
                if crawling_page not in links_dict.keys():
                    links_dict[crawling_page] = []
                links_dict[crawling_page].append("{} :=: {}".format(link_text, website))
                print('--->{} = {}'.format(link_text, website))
        else:
            website = html.unescape(site).replace('%20', '+').replace(' ', '+')
            if crawling_page not in links_dict.keys():
                links_dict[crawling_page] = []
            links_dict[crawling_page].append("{} :=: {}".format(link_text, website))
            print('--->{} = {}'.format(link_text, website))

def extract_span_text(_line, chunk):
    link_text = ""
    for index in range(len(chunk)):
        if _line == chunk[index]:
            # Try to extract span
            try:
                if chunk[index + 1].split(';">')[-1].split('<')[0] != "":
                    link_text = chunk[index + 1].split(';">')[-1].split('<')[0].strip()
                elif chunk[index + 1].split('>')[1].split('</')[0] != "":
                    link_text = chunk[index + 1].split('>')[1].split('</')[0].strip()
                elif chunk[index].split('">')[-1].split('</')[0] != "":
                    link_text = chunk[index].split('">')[-1].split('</')[0].strip()
                elif chunk[index].strip() != "":
                    print('Could not format:\n\t\t'.format(chunk[index]))
                return link_text
            except:
                if chunk[index].strip() != "":
                    print('Could not format:\n\t\t'.format(chunk[index]))
                return link_text

# -----> Grab and test broken links
# New Function: Test Link and Handle Results
def test_link_and_handle_results(crawling_page, text, website, good_links, good_link_count, bad_link_count):
    if website in good_links:
        good_link_count += 1
        print(f'{website} - STILL GOOD!')
    elif website in bad_links:
        bad_link_count += 1
        add_to_broken_dict(crawling_page, text, website)
        print(f'{website} - STILL BAD!')
    else:
        if test_link_authenticated(website):
            good_link_count += 1
            good_links.append(website)
            print(f'{website} - GOOD!')
        else:
            bad_link_count += 1
            add_to_broken_dict(crawling_page, text, website)
            print(f'{website} - BAD!')

def test_link(crawling_page, text, website, good_links, good_link_count, bad_link_count):
    if website.startswith(f'https://{main_url}/'):
        test_link_and_handle_results(crawling_page, text, website, good_links, good_link_count, bad_link_count)
    else:
        try:
            if website.startswith('http:'):
                secure_website = website.replace('http:', 'https:')
                secured_get_url = requests.get(secure_website, timeout=20)
                if secured_get_url.status_code == 403:
                    test_link_and_handle_results(crawling_page, text, website, good_links, good_link_count, bad_link_count)
                elif secured_get_url.status_code == 200:
                    good_link_count += 1
                    good_links.append(website)
                    print(f'{website} - GOOD!')
                else:
                    bad_link_count += 1
                    add_to_broken_dict(crawling_page, text, website)
                    print(f'{website} - BAD!')
            else:
                bad_link_count += 1
                add_to_broken_dict(crawling_page, text, website)
                print(f'{website} - BAD!')
        except:
            bad_link_count += 1
            add_to_broken_dict(crawling_page, text, website)
            print(f'{website} - BAD!')

def create_broken_dict(_links_dict):
    link_count = 0
    bad_link_count = 0
    good_link_count = 0
    good_links = []
    print("Testing all links...")
    for crawling_page, content_list in _links_dict.items():
        for pair in content_list:
            text = pair.split(' :=: ')[0]
            website = pair.split(' :=: ')[-1]
            test_link(crawling_page, text, website, good_links, good_link_count, bad_link_count)
            link_count += 1
    print('{} links checked, {} bad links, {} good links, {} bypass auth'.format(link_count, bad_link_count, good_link_count, bypass_auth_list))
    print('{}'.format(breaker))
    return broken_dict

def add_to_broken_dict(_crawling_page, _text, _website):
    bad_links.append(_website)
    if _crawling_page not in broken_dict.keys():
        broken_dict[_crawling_page] = []
    broken_dict[_crawling_page].append('The raw text "{}", has a bad link to {}'.format(_text, _website))

# -----> Send results
def send_bad_links(_broken_dict):
    global o_lines
    o_lines += 'The following is a Confluence web scraper script created by Brandon Volesky.\n\nBroken Wiki Links:\n'
    print(breaker)
    for k, v in _broken_dict.items():
        if v:
            print(k + "\n\t" + "\n\t".join(str(x) for x in v) + '\n')
            o_lines += ('\t' + k + "\n\t\t" + "\n\t\t".join(str(x) for x in v) + '\n\n')

    with open('{}_Broken_Links.txt'.format(space), 'w') as output_file:
        output_file.write(o_lines)

__response = authenticate()
__urls = create_urls(__response)
__pages_dict = create_pages_dict(__urls)
__links_dict = create_links_dict(__pages_dict)
__broken_dict = create_broken_dict(__links_dict)
send_bad_links(__broken_dict)
