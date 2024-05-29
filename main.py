# -*- coding: utf-8 -*-
# @Time : 2021/12/8 10:20
# @Author : MinChess Modified by Lynnette 2024.5.29
# @File : main.py
# @Software: PyCharm
import requests
from lxml import etree
import csv
from urllib.parse import quote
import re
import time
import random


max_comment_pages = 5 #在这里设置评论爬取上限
from html.parser import HTMLParser
headers_com = {
        'Cookie': '你的微博cookie写这里',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0'
        }
headers_cn = {
    'Cookie': '你的微博评论页cookie写这里 注意和上面不一样 可以先写好上面的 跑一次拿到网址 然后去看',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0'

        }

baseUrl = 'https://s.weibo.com/weibo?q=%23{}%23&Refer=index'
topic = '测试话题'
csvfile = open(topic+ '.csv', 'a', newline='', encoding='utf-8-sig')
writer = csv.writer(csvfile)

def getTopic(url):
    page = 0
    pageCount = 1

    while True:
        weibo_content = []
        weibo_liketimes = []
        weibo_date = []
        page = page + 1
        tempUrl = url + '&page=' + str(page)
        print('-' * 36, tempUrl, '-' * 36)
        response = requests.get(tempUrl, headers=headers_com)
        html = etree.HTML(response.text, parser=etree.HTMLParser(encoding='utf-8'))
        count = len(html.xpath('//div[@class="card-wrap"]')) - 2
        for i in range(1, count + 1):
            try:
                contents = html.xpath('//div[@class="card-wrap"][' + str(i) + ']/div[@class="card"]/div[1]/div[2]/p[@node-type="feed_list_content_full"]')
                contents = contents[0].xpath('string(.)').strip()  # 读取该节点下的所有字符串
            except:
                contents = html.xpath('//div[@class="card-wrap"][' + str(i) + ']/div[@class="card"]/div[1]/div[2]/p[@node-type="feed_list_content"]')
                # 如果出错就代表当前这条微博有问题
                try:
                    contents = contents[0].xpath('string(.)').strip()
                except:
                    continue
            contents = contents.replace('收起全文d', '')
            contents = contents.replace('收起d', '')
            contents = contents.split(' 2')[0]

            # 发微博的人的名字
            name = html.xpath('//div[@class="card-wrap"][' + str(i) + ']/div[@class="card"]/div[1]/div[2]/div[1]/div[2]/a')[0].text
            print(name)
            # 微博url
            weibo_url = html.xpath('//div[@class="card-wrap"][' + str(i) + ']/div[@class="card"]/div[1]/div[2]/div[@class="from"]/a/@href')[0]

            url_str = '.*?com\/\d+\/(.*)\?refer_flag=\d+_'
            res = re.findall(url_str, weibo_url)
            weibo_url = res[0]
            host_url = 'https://weibo.cn/comment/'+weibo_url
            # 发微博的时间
            timeA = html.xpath('//div[@class="card-wrap"][' + str(i) + ']/div[@class="card"]/div[1]/div[2]/div[@class="from"]/a')[0].text.strip()
            # 点赞数
            likeA = html.xpath('//div[@class="card-wrap"][' + str(i) + ']/div[@class="card"]/div[2]/ul[1]/li[3]/a/button/span[2]')[0].text
            hostCommenta = html.xpath('//div[@class="card-wrap"][' + str(i) + ']/div[@class="card"]/div[2]/ul[1]/li[2]/a')[0].xpath('text()')
            hostComment = int(hostCommenta[0])
            print(timeA,likeA,hostComment)
            # 如果点赞数为空，那么代表点赞数为0
            if likeA is None:
                likeA = 0
            try:
                hosturl,host_sex, host_location, hostcount, hostfollow, hostfans=getpeople(name)
                list = ['微博', name, hosturl, host_sex, host_location, hostcount, hostfollow, hostfans,contents, timeA, likeA]
                print(list)
                writer.writerow(list)
                csvfile.flush()
            except:
                continue
            if hostComment != 0:
                print('正在爬取第',page,'页，第',i,'条微博的评论。')
                getComment(host_url)

            print('=' * 66)
        try:
            if pageCount == 1:
                pageA = html.xpath('//*[@id="pl_feedlist_index"]/div[5]/div/a')[0].text
                print(pageA)
                pageCount = pageCount + 1
            elif pageCount == 50:
                print('没有下一页了')
                break
            else:
                pageA = html.xpath('//*[@id="pl_feedlist_index"]/div[5]/div/a[2]')[0].text
                pageCount = pageCount + 1
                print(pageA)
        except:
            print('没有下一页了')
            break

def getpeople(name):
    findPoeple=0
    url2 = 'https://s.weibo.com/user?q='
    while True:
        try:
            response = requests.post('https://weibo.cn/search/?pos=search', headers=headers_cn,data={'suser': '找人', 'keyword': name})
            tempUrl2 = url2 + str(name)+'&Refer=weibo_user'
            print('搜索页面',tempUrl2)
            response2 = requests.get(tempUrl2, headers=headers_com)
            html = etree.HTML(response2.content, parser=etree.HTMLParser(encoding='utf-8'))
            hosturl_01 =html.xpath('/html/body/div[1]/div[2]/div/div[2]/div[1]/div[3]/div[1]/div[2]/div/a/@href')[0]
            url_str = '.*?com\/(.*)'
            res = re.findall(url_str, hosturl_01)
            hosturl = 'https://weibo.cn/'+res[0]
            print('找人主页：',hosturl)
            break
        except:
            if findPoeple==10:
                stop=random.randint(60,300)
                print('IP被封等待一段时间在爬',stop,'秒')
                time.sleep(stop)
            if response.status_code==200:
                return
            print('找人')
            time.sleep(random.randint(0,10))
            findPoeple=findPoeple+1
    while True:
        try:
            response = requests.get(hosturl, headers=headers_cn)
            # print('微博主人个人主页',hosturl)
            html = etree.HTML(response.content, parser=etree.HTMLParser(encoding='utf-8'))
            # 获取微博数
            # html2 = etree.HTML(html)
            # print(html2)
            hostcount = html.xpath('/html/body/div[4]/div/span')[0].text
            # 正则表达式，只获取数字部分
            # print(hostcount)
            hostcount = re.match('(\S\S\S)(\d+)', hostcount).group(2)
            # 获取关注数
            hostfollow = html.xpath('/html/body/div[4]/div/a[1]')[0].text
            # 正则表达式，只获取数字部分
            hostfollow = re.match('(\S\S\S)(\d+)', hostfollow).group(2)
            # 获取粉丝数
            hostfans = html.xpath('/html/body/div[4]/div/a[2]')[0].text
            # 正则表达式，只获取数字部分
            hostfans = re.match('(\S\S\S)(\d+)', hostfans).group(2)
            # 获取性别和地点
            host_sex_location = html.xpath('/html/body/div[4]/table/tr/td[2]/div/span[1]/text()')
            # print(hostcount, hostfollow, hostfans, host_sex_location)
            break
        except:
            print('找人失败')
            time.sleep(random.randint(0, 10))
            pass
    try:
        host_sex_locationA = host_sex_location[0].split('\xa0')
        host_sex_locationA = host_sex_locationA[1].split('/')
        host_sex = host_sex_locationA[0]
        host_location = host_sex_locationA[1].strip()
    except:
        host_sex_locationA = host_sex_location[1].split('\xa0')
        host_sex_locationA = host_sex_locationA[1].split('/')
        host_sex = host_sex_locationA[0]
        host_location = host_sex_locationA[1].strip()

    # print('微博信息',name,hosturl,host_sex,host_location,hostcount,hostfollow,hostfans)
    # nickname, hosturl, host_sex, host_location, hostcount, hostfollow, hostfans
    return hosturl,host_sex, host_location, hostcount, hostfollow, hostfans

def getComment(hosturl):
    page=0
    pageCount=1
    count = []#内容
    date = []#时间
    like_times = []#赞
    user_url = []#用户url
    user_name = []#用户昵称
    while True:
        page=page+1
        print('正在爬取第',page,'页评论')
        if page == 1:
            url = hosturl
        else:
            url = hosturl+'?page='+str(page)
        print(url)
        try:
            response = requests.get(url, headers=headers_cn)
        except Exception as e:
            print(e)
            break
        html = etree.HTML(response.content, parser=etree.HTMLParser(encoding='utf-8'))
        user_re = '<div\sclass="c"\sid="C_\d+.*?<a\shref="(.*?)"'
        user_name_re = '<div\sclass="c"\sid="C_\d+.*?<a\shref=".*?">(.*?)</a>'
        co_re = '<div\sclass="c"\sid="C_\d+.*?<span\sclass="ctt">(.*?)</span>'
        zan_re = '<div\sclass="c"\sid="C_\d+.*?赞\[(.*?)\]'
        date_re = '<div\sclass="c"\sid="C_\d+.*?<span\sclass="ct">(.*?);'
        count_re = '回复<a.*</a>:(.*)'

        user_name2 = re.findall(user_name_re,response.text)
        zan = re.findall(zan_re,response.text)
        date_2 = re.findall(date_re,response.text)
        count_2 = re.findall(co_re, response.text)
        user_url2 = re.findall(user_re,response.text)
        #print(user_name2,zan,date_2,count_2,user_url2)
        flag = len(zan)
        for i in range(flag):
            count.append(count_2[i])
            date.append(date_2[i])
            like_times.append(zan[i])
            user_name.append(user_name2[i])
            user_url.append('https://weibo.cn'+user_url2[i])
        try:
            if pageCount==1: #第一页找下一页标志代码如下
                pageA = html.xpath('//*[@id="pagelist"]/form/div/a')[0].text
                print('='*40,pageA,'='*40)
                pageCount = pageCount + 1
            else:  #第二页之后寻找下一页的标志
                pageA = html.xpath('//*[@id="pagelist"]/form/div/a[1]')[0].text
                pageCount=pageCount+1
                print('='*40,pageA,'='*40)
            if pageCount > max_comment_pages:
                break
        except:
            print('没有下一页')
            break
    print("#"*20,'评论爬取结束，下面开始爬取评论人信息',"#"*20)
    print(len(like_times),len(count),len(date),len(user_url),len(user_name))
    flag=min(len(like_times),len(count),len(date),len(user_url),len(user_name))
    for i in range(flag):
        host_sex,host_location,hostcount,hostfollow,hostfans=findUrl(user_url[i])
        # print('评论',user_name[i], user_url[i] , host_sex, host_location,hostcount, hostfollow, hostfans,count[i],date[i],like_times[i])
        print('在爬取第',i+1, '个人')
        list111 = ['评论',user_name[i], user_url[i] , host_sex, host_location,hostcount, hostfollow, hostfans,count[i],date[i],like_times[i]]
        writer.writerow(list111)
        #time.sleep(random.randint(0, 2))
    csvfile.flush()

def findUrl(hosturl):
    while True:
        try:
            print(hosturl)
            response = requests.get(hosturl, headers=headers_cn)
            html = etree.HTML(response.content, parser=etree.HTMLParser(encoding='utf-8'))
            hostcount=html.xpath('/html/body/div[4]/div/span')[0].text
            hostcount=re.match('(\S\S\S)(\d+)',hostcount).group(2)
            hostfollow=html.xpath('/html/body/div[4]/div/a[1]')[0].text
            hostfollow = re.match('(\S\S\S)(\d+)', hostfollow).group(2)
            hostfans=html.xpath('/html/body/div[4]/div/a[2]')[0].text
            hostfans = re.match('(\S\S\S)(\d+)', hostfans).group(2)
            host_sex_location=html.xpath('/html/body/div[4]/table/tr/td[2]/div/span[1]/text()')
            break
        except:
            print('找人失败')
            time.sleep(random.randint(0, 5))
            pass
    try:
        host_sex_locationA=host_sex_location[0].split('\xa0')
        host_sex_locationA=host_sex_locationA[1].split('/')
        host_sex=host_sex_locationA[0]
        host_location=host_sex_locationA[1].strip()
    except:
        host_sex_locationA=host_sex_location[1].split('\xa0')
        host_sex_locationA = host_sex_locationA[1].split('/')
        host_sex = host_sex_locationA[0]
        host_location = host_sex_locationA[1].strip()
    time.sleep(random.randint(0, 2))
    # print('微博信息:','url:', hosturl, '性别:',host_sex, '地区：',host_location,'微博数:', hostcount, '关注数:',hostfollow,'粉丝数:', hostfans)
    return host_sex,host_location,hostcount,hostfollow,hostfans

if __name__=='__main__':
    topic = '测试话题'
    url = baseUrl.format(topic)
    print(url)
    writer.writerow(['类别', '用户名', '用户链接', '性别', '地区', '微博数', '关注数', '粉丝数', '评论内容', '评论时间', '点赞次数'])
    getTopic(url)  #去话题页获取微博
