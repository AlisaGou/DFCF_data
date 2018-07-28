#! /usr/bin/env python
#  coding = utf-8
#  Author = Alisa
#  爬取东方财富通上证A股和创业板个股股吧帖子

import requests
from lxml import etree
import traceback
from fake_useragent import UserAgent
from pymongo import MongoClient
import pymysql.cursors
import pandas as pd

ip_proxy = list()  # 建立IP代理列表

def get_proxy_ip_from_mysql():
    """从MySQL数据库中获得IP代理"""
    connection = pymysql.connect(host='*******', user='*****', password='*******', db='*****',
                                 charset='******',
                                 cursorclass=pymysql.cursors.DictCursor)   # 连接数据库
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * from lagou WHERE speed > 0 and speed < 4 and vali_count > 0 ORDER BY speed"
            cursor.execute(sql)
            result = cursor.fetchall()  # 结果为找寻全部
            return result

    finally:
        connection.close()

def request_get(url,*args, **kwargs):  # 当函数的参数不确定时，可使用 魔法变量：*args当作容纳多个的list或tuple，**kwargs当作容纳多个键值对的dict.
    """将请求链接包一层，可以统一处理异常，应对一些突发状况，统一上代理"""
    global ip_proxy  # ip_proxy为全局变量，以下程序中的ip_proxy都一致

    retrytime = 0
    while True:
        try:
            if not ip_proxy:  # 若非ip_proxy
                ip_proxy = get_proxy_ip_from_mysql()  # ip_proxy为get_proxy_ip_from_mysql()函数所得
            proxy = ip_proxy.pop()  # 代理使用一次就减少一个，默认移除列表中的最后一个元素

            proxies = {
                'http': 'http://{ip}:{port}'.format(**proxy),
                'https': 'http://{ip}:{port}'.format(**proxy),
            }

            r = requests.get(url, proxies=proxies, timeout=5, *args, **kwargs)

            if r.status_code == 200:
                return r  # 返回值 r
            else:
                retrytime += 1
                print('url:{} retry_time:{}'.format(url, retrytime))

                if retrytime < 10:
                    continue
                elif retrytime > 10:
                    break

        except Exception as e:
            _ = e  # 占位，产生变量但未使用
            # traceback.print_exc()
            retrytime += 1
            print('url:{} retry_time:{}'.format(url, retrytime))

            if retrytime < 10:
                continue
            elif retrytime > 10:
                break

class DongFangCaiFuSpider(object):

    headers = dict()  # 初始化

    def get_guba(self):
        """获取所有的股吧链接"""
        headers = {
            'Cookie': 'st_pvi=07289511176421; emstat_bc_emcount=8269995271467659399; em_hq_fls=js; qgqp_b_id=16bc6c0db9'
                      'e5834747e5244ce183dbf2; HAList=a-sz-300059-%u4E1C%u65B9%u8D22%u5BCC%2Ca-sz-000063-%u4E2D%u5174%u901A%u8BA'
                      'F; ct=EQOdBZdiQKgjLDjjLKpPt2J1wu1bik6OjrvrXcEarEDdVz7TOcEJPll5zcUT8vg0_r9jzABole2ATQ69EUop408CQIuiOeCOtqJC'
                      '-Ib4sD3zhLhyJt9DCT1xKLicsPAjKjo7MXiN4QCZqdwQYMokh7zZdcT9qKan947y8JFfzTs; ut=FobyicMgeV52Ad4fCxim_G3WfDRv5X'
                      'tGWFKS1QF9xEiueMg253yd2gIURXeK3Y0Fk7K2V7nUh5pyUMPty8ZcRCwLQr_CZDw6OOoPJo5mDqz7M15gbGPixJXsKgqLOIjEGatLngak'
                      '9iJZy_G3jW5hCH6rQWkrudbvNx2_tRSG6fIowc-Fz8JTgTiTSyARy5VmH1aoD_voTq5S162ZlvfvSlvLQ-1tXqjzMANMEGndJZ5m9W_d6p'
                      'sQ5uMJSv4A2dKYnOzozp3D9ueJj2qKf1C8YInqydKDCf2A; pi=8116065114287126%3bu8116065114287126%3b%e8%82%a1%e5%8f%'
                      '8bKxq4nV%3bEC%2bz9e14Sjom05tMAtFVCoE3cxK0KDhZ6mR8T9dDRyP%2flZvkdobkvQNUset7aIAWYnAfD0qVfNGFMHZHkckIqVNxZRO'
                      'KEecJdddhlqCKsuN3b0FbQOfPiqeGS7Mi3gZlX66vzUzJFi%2bSVlZGTBA85oFp%2bOTu%2f6fLBBpKdjyz4GqDN1ZQq1I1hBnAS5cJ2Aa'
                      '9gdePRe%2br%3biN%2f8t64k98erR5LNCwM2XK%2fsakeQf2bmHbnMnLRTzuS99XbJJR4LtXHCFS7hijcfwVpPV3u0l1LDXsnb5OaVFNFT'
                      '0e0Vefcepetj4m%2bNw20ddTJLWPndGm1l9J%2bwdW7IkZrNusQOn%2f5QGxreCvpZX47rEcrVrg%3d%3d; uidal=8116065114287126'
                      '%e8%82%a1%e5%8f%8bKxq4nV; sid=114124340; vtpst=|; emstat_ss_emcount=5_1513351193_2439751672',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.'
                          '3239.84 Safari/537.36',
            'Upgrade-Insecure-Requests': '1'
        }  # 对应的headers信息

        # 创建一个股吧列表，包括上证A股和创业板股票
        tab_num = [1, 2]
        url = 'http://guba.eastmoney.com/remenba.aspx?type=1&tab={}'.format(tab_num)  # 访问东方财富网股吧首页
        r = requests.get(url, headers=headers).text
        s = etree.HTML(r)
        stock_num = s.xpath('/html/body/div[5]/div[2]/div[1]/div/ul/li/a/@href')

        urls = list()
        client = MongoClient()
        db = client.dongfangcaifu  # 创建一个dongfangcaifu数据库
        my_set = db.guba_url

        for url in stock_num:  # 获取所有证券市场股票对应的东方财富网的股吧链接
            urls_ = url[6:12]
            urls.append(urls_)
            d = {'stock_num': urls_}
            print(d)

            my_set.insert(d)  # 插入股吧链接数据,如http://guba.eastmoney.com/list,600000.html
            _ = self  # 传为self参数
        return urls  # 返回一个urls股吧列表

    def list_pag(self, url_format: str, stock_code, urls):
        """爬取帖子链接，并抓取详情页"""
        ua = UserAgent()
        self.headers['User-Agent'] = ua.random  # 使用fake-Agent随机生成User-Agent，添加到headers

        page_num = 1

        while True:
            url = url_format.format(page_num)

            r = request_get(url, headers=self.headers)

            if not r:
                print('数据出错 {}'.format(url))
                page_num += 1
                continue
            r = r.text

            try:
                s = etree.HTML(r)
                stock_name = s.xpath('//*[@id="stockname"]/a/text()')  # 股票名称
                stock_code = stock_code
                tiezi_url = s.xpath('//*[@id="articlelistnew"]/div/span[3]/a/@href')  # 帖子链接


                if not tiezi_url:
                    break

                read_vol = s.xpath('//*[@id="articlelistnew"]/div/span[1]/text()')  # 阅读量
                comment_vol = s.xpath('//*[@id="articlelistnew"]/div/span[2]/text()')  # 评论量
                update_time = s.xpath('//*[@id="articlelistnew"]/div/span[6]/text()')  # 帖子更新时间

                for index, url_ in enumerate(tiezi_url, 1):  # 一个索引类型遍历帖子链接

                    if not url_.startswith('/'):
                        continue                                # 跳过本次，break跳过全部

                    urls = 'http://guba.eastmoney.com{}'.format(str(url_))  # 帖子链接

                    self.detail_pag(urls, stock_name[0], stock_code, read_vol[index], comment_vol[index],update_time[index])  # 自动抓取详情页
                    #time.sleep(1)  # 设置爬取网页的时间间隔
                    self.comment_page(tiezi_url)

            except Exception as e:
                _ = e    # 占位，产生变量但未使用
                print(url_format, r)  # 打印报错信息
                traceback.print_exc()
            page_num += 1

    def detail_pag(self, urls, stock_name, stock_code, read_vol, comment_vol, update_time, commentator, comment_time,
                   comment_content,support_num):
        """
        详情页抓取函数
        :param url: 详情页url
        :return:
        """
        headers = {
            'Cookie': 'st_pvi=07289511176421; emstat_bc_emcount=8269995271467659399; em_hq_fls=js; qgqp_b_id=16bc6'
                      'c0db9e5834747e5244ce183dbf2; HAList=a-sz-300059-%u4E1C%u65B9%u8D22%u5BCC%2Ca-sz-000063-%u4E2'
                      'D%u5174%u901A%u8BAF; st_si=62317377700088; EmPaVCodeCo=47ebe00218714631853a7a63f9928ab7; sid=1'
                      '14124340; vtpst=|; ct=ugJ70hWNaio7gPXQTxtTmpLDLh6sdrL8j2rybQIxbDSghfWwbEd_BKHXJriuASTodXFak296K'
                      'Orlfkxzrbu-NT-U8hpjvtKu3mXqgcyCqO5MJltGLp76DVw_L9ucdTq3hYzozM9aRJ0auXb4A70zvYuCRYtRVO8mQImUy0s'
                      'hj-E; ut=FobyicMgeV7MP9QJfNEgf8-r9TbKvL5aHhpxUzw7ocvpUgxAb33dnUCv07IaWIFM2GVZHu0fHIdMv8s1jhp0lS'
                      'WWXjKnSHcQ_Y09rQC1zYUppyOE9wWA5GWXcNRkN0DFEHtiM8VksgjrIAhnWVqslFpiiMOSTgKw9zOeY2sx2OxuZ077q0SGy4'
                      'BCLG9jY9Vr4SsRaLXwAbpavWMsSCGITBDXDv516Bf9hMNgvbVb-BL-8KgHQWxGjuw2-77DqJyNrYop94tGwlCVSCacv2rUUjB'
                      'o8HyR9qCI; pi=8116065114287126%3bu8116065114287126%3bAlisaGou%3bTIVcVA9AyoQiZGOIe5yV36bl5oaXoirEJ'
                      'hVeWh7QdvNf3OVN2%2bVR4FrL3hKFB8V2LzXVwJjzYErPHtx27DTCigSc5OaPon3OvqD%2fMUANcQ2IPRINC7tXrbFotgjh8i'
                      'oEsYHrZCw6qmNB65r2%2bfNM7jjpsAW%2fZvB6g8Au5h1F6UiYyzixg65mZz5rUb2MAHKTbbt%2fRVFW%3bTS8P9EuPHU6wSEH'
                      'TJNZBTrv%2fy0vhBPzopUd783nknn2rMvcMyjUu7btn2dCve6yKiPMf9c97%2b7LwtYeQcZC%2ffU6iRriJy8ojLxn%2bfejWb'
                      'jPNYF4mw06Xmqgp3QYg8WxaFkU7TnozQWGRBkknMHUIM2sHwoyZNQ%3d%3d; uidal=8116065114287126AlisaGou; emstat'
                      '_ss_emcount=24_1513377935_3906866301',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.323'
                          '9.84 Safari/537.36'
        }
        r = request_get(url=urls, headers=headers)   # 访问url列表？headers为上面的三个？怎么引入IP代理？

        if r is None:
            print('数据出错{}'.format(urls))
            return
        r = r.text
        s = etree.HTML(r)

        origin_data = dict()
        publisher = ''.join(s.xpath('//*[@id="zwconttbn"]/strong/a/text()'))  # 抓取 作者
        age = ''.join(s.xpath('//*[@id="zwconttbn"]/span/span[2]/text()'))  # 抓取 吧龄
        influence = ''.join('//*[@id="zwconttbn"]/span/span[1]/text()')  # 抓取 发布者影响力
        time_ = ''.join(s.xpath('//*[@id="zwconttb"]/div[2]/text()'))  # 抓取 时间
        title = ''.join(s.xpath('//*[@id="zwconttbt"]/text()'))  # 抓取 标题
        content = ''.join(s.xpath('//*[@id="zwconbody"]/div/text()'))  # 抓取 正文

        print(stock_code, urls)

        origin_data = {'stock_name': stock_name, 'stock_code': stock_code, 'read_vol': read_vol,
                       'comment_vol': comment_vol, 'publisher': publisher, 'age': age, 'time_': time_,
                       'title': title, 'content': content, 'update_time': update_time, 'influence': influence,
                       'commentator': commentator, 'comment_time': comment_time, 'comment_content':comment_content,
                       'support_num': support_num,}

        # origin_data = [stock_name, stock_code, read_vol,comment_vol, publisher, age, time_, title, content, update_time]
        _ = self

        self.save_data(origin_data)

    def comment_page(self, tiezi_url):
        """详情页抓取评论及评论人"""
        ua = UserAgent()
        self.headers['User-Agent'] = ua.random  # 使用fake-Agent随机生成User-Agent，添加到headers

        page_num = 1

        while True:
            # http://guba.eastmoney.com/news,600000,739093106_{}.html
            urls = tiezi_url.strip('.html')
            url = urls+'_{}'.format(page_num)+ '.html'

            r = request_get(url, headers=self.headers)

            if not r:
                print('数据出错 {}'.format(url))
                page_num += 1
                continue
            r = r.text
            s = etree.HTML(r)

            # 获取评论信息
            commentator = ''.join(s.path('//*[@id*]/div[3]/div/div[1]/span[1]/a/text()')) # id 是变化的？？
            comment_time = ''.join(s.path('//*[@id*]/div[3]/div/div[2]/text()')) # 评论时间
            comment_content = ''.join(s.path('//*[@id*]/div[3]/div/div/text()'))# 评论内容
            support_num = ''.join(s.path('//*[@id*/div[3]/div/div[4]/div[2]/a[1]/span[2]/text()')) # 评论点赞数
            # 获取评论的评论的信息

            self.detail_pag(urls, commentator, comment_time, comment_content,support_num)

    def save_data(self, data):
        """保存数据函数"""
        client = MongoClient()
        db = client.dongfangcaifu  # 创建一个dongfangcaifu数据库
        my_set = db.guba_2018  # 创建股吧集合
        my_set.insert(data)  #插入股吧详情数据
        # df = pd.DataFrame(origin_data, columns=['股票名称', '股票代码', '阅读量', '评论量','作者','吧龄','发布时间','标题','正文'])
        # df.to_excel('tiezi.xlsx', sheet_name='Sheet1')
        _ = self  # 占位符
        _ = data  # 占位符

if __name__ == '__main__':
    """执行入口"""
    #request_get('http://guba.eastmoney.com/remenba.aspx?type=1')
    spider = DongFangCaiFuSpider()  # 生产一个爬虫对象
    guba_url_format_list = spider.get_guba()  # 抓取所有的股吧的样例url

    # http://guba.eastmoney.com/list,603186,99_{}.html 热帖
    for stock_code in guba_url_format_list:  # 遍历
        url_format = 'http://guba.eastmoney.com/list,{},99_'.format(stock_code)+'{}.html'
        spider.list_pag(url_format, stock_code)  # 抓取列表页， 列表页自动抓取详情页

    # http://guba.eastmoney.com/list,002680,1,f_{}.html 新闻
    # http://guba.eastmoney.com/list,002680,2,f_{}.html 研报
    # http://guba.eastmoney.com/list,002680,3,f_{}.html 公告







