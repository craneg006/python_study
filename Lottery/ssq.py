# !/usr/local/bin/python3
# _*_ coding:utf-8 _*_

import requests
import bs4
from numpy.core import unicode
import mysql.connector


class SsqItem(object):
    def __init__(self, date, period, win_balls, sales, first_prize,
                 first_prize_region, snd_prize):
        # date of win
        self.date = date
        # period num
        self.period = period
        # five red ball and 1 blue ball
        self.win_balls = win_balls
        # sale of this period
        if sales is '':
            self.sales = 0
        else:
            self.sales = sales
        # 1st prize account
        if first_prize is '':
            self.first_prize = 0
        else:
            self.first_prize = first_prize
        self.first_prize_region = first_prize_region
        # 2nd prize account
        if snd_prize is '':
            self.snd_prize = 0
        else:
            self.snd_prize = snd_prize

    def print_value(self):
        print("====================")
        print("date: " + self.date)
        print("period: " + self.period)
        print("win_balls: ", end='')
        for ball in self.win_balls:
            print(ball, end=' ')
        print()
        print("sales: " + self.sales)
        print("first_prize: " + self.first_prize)
        print("first_prize_region: " + self.first_prize_region)
        print("snd_prize: " + self.snd_prize)
        print("====================")

    def string(self):
        return str(self.date) + " " + str(self.period) + " " + str(
            self.win_balls) + " " + str(self.sales) + " " + str(
            self.first_prize) + " " + str(self.first_prize_region) + " " + \
               str(self.snd_prize)


class SsqParse(object):
    def __init__(self, base_url, user: str, pwd: str, db: str, tb: str):
        self.base_url = base_url
        self.ssq_items = []
        self.user = user
        self.pwd = pwd
        self.db = db
        self.tb = tb
        self.latest_period = 0
        self.__get_latest_period()

    def __get_latest_period(self):
        conn = mysql.connector.connect(user=self.user, password=self.pwd,
                                       database=self.db)
        cursor = conn.cursor()
        try:
            cursor.execute("select Max(ssq_period) from " + self.tb)
            result = cursor.fetchall()
            for row in result:
                self.latest_period = int(row[0])
        except Exception as e:
            self.latest_period = 0
            print("execute error: %s" % e)
        finally:
            cursor.close()
            conn.close()

    def parse_winning_pages(self, pages_count=0):
        # parse 1st page
        page = self._fetch_winning_page(self.base_url + "list.html")
        total_page, total_items, current_page = self._parse_winning_page(page)
        print("total_page: %d, total_items: %d, current_page: %d" % (
            total_page, total_items, current_page))
        # parse all pages left
        if pages_count < total_page and pages_count != 0:
            total_page = pages_count
        while current_page < total_page:
            page = self._fetch_winning_page(self.base_url + str("list_") + str(
                current_page + 1) + str(".html"))
            total_page, total_items, current_page = self._parse_winning_page(
                page)

    def save_winning_file(self, file_name):
        print("ssq_items num: %d" % len(self.ssq_items))
        with open(file_name, "w") as f:
            for item in self.ssq_items:
                f.write(item.string())
                f.write("\n")

    def print_items(self):
        for item in self.ssq_items:
            print(item.string())
            print()

    def save_winning_mysql(self):
        conn = mysql.connector.connect(user=self.user, password=self.pwd,
                                       database=self.db)
        cursor = conn.cursor()
        sql = 'insert into ' + self.tb + '(ssq_period, ssq_ball, ssq_date, ' \
                                         'ssq_sales, ssq_1st, ssq_1st_region,' \
                                         ' ssq_2nd) values (%s, %s, %s, %s,' \
                                         ' %s, %s, %s)'
        tuple_list = []
        for item in self.ssq_items:
            tuple_list.append(tuple((item.period, item.win_balls, item.date,
                                     item.sales, item.first_prize,
                                     item.first_prize_region, item.snd_prize)))
        try:
            cursor.executemany(sql, tuple_list)
            conn.commit()
        except Exception as e:
            conn.rollback()
            print("executemany error: %s：%s" % (sql, e))
        cursor.close()
        conn.close()

    @staticmethod
    def _fetch_winning_page(web_address):
        request_header = {'user-agent': "Mozilla/5.0 (X11; Linux x86_64)"
                                        " AppleWebKit/537.36 (KHTML, "
                                        "like Gecko) Chrome/63.0.3239.132"
                                        " Safari/537.36"}
        res = requests.get(web_address, headers=request_header)
        if res.status_code == requests.codes.ok:
            return res.text
        else:
            res.raise_for_status()
            return None

    def _parse_winning_page(self, html_content):
        soup = bs4.BeautifulSoup(html_content, 'html.parser')
        # td tag...
        td_tag = soup.find_all("td")
        for index in range(0, len(td_tag) - 1, 7):
            date = str(unicode(td_tag[index].string))
            period = str(unicode(td_tag[index + 1].string))
            ball_tag = td_tag[index + 2]
            ball_value = str()
            for string in ball_tag.stripped_strings:
                ball_value += (str(unicode(string))) + ' '
            ball_value = ball_value.strip()
            sales = str(unicode(td_tag[index + 3].string)).strip().replace(
                ',', '')
            first_prize = str(unicode(td_tag[index + 4].contents[
                                          0].string)).strip()
            first_prize_region = ''
            if len(td_tag[index + 4].contents) >= 2:
                first_prize_region = str(unicode(
                    td_tag[index + 4].contents[1].string)).strip().replace('(',
                                                                           '') \
                    .replace(')', '').replace('.', '')
            snd_prize = str(
                unicode(td_tag[index + 5].contents[0].string)).strip()
            if int(period) <= self.latest_period:
                return 0, 0, 0
            else:
                self.ssq_items.append(SsqItem(date, period, ball_value, sales,
                                              first_prize, first_prize_region,
                                              snd_prize))
        final_tag = td_tag[len(td_tag) - 1]
        final_strong_tag = final_tag.find_all('strong')
        total_page = int(unicode(final_strong_tag[0].string))
        total_items = int(unicode(final_strong_tag[1].string))
        current_page = int(unicode(final_strong_tag[len(final_strong_tag) - 1]
                                   .string))
        return total_page, total_items, current_page


if __name__ == '__main__':
    url = "http://kaijiang.zhcw.com/zhcw/html/ssq/"
    parser = SsqParse(url, 'root', 'admin123', 'ssq', 'ssq_winning')
    parser.parse_winning_pages()
    parser.print_items()
    parser.save_winning_mysql()
