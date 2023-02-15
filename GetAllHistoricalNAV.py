import re
import requests
import random
import time
import datetime
import pandas as pd
from bs4 import BeautifulSoup
from JinxinNo1.params import user_agents


def choose_user_agent():
    """
    Randomly choose a User Agent before visiting the website
    """
    return random.choice(user_agents)


def get_start_date(fund_id:str):
    """
    To automatically search for the start date before getting all historical NAV
    """
    search_url = 'http://fund.eastmoney.com/' + fund_id + '.html?spm=search'
    response = requests.get(search_url, headers={'user-agent': choose_user_agent()})
    text = response.content.decode('utf-8')
    start_date = re.findall('<td><span class="letterSpace01">成 立 日</span>：(.*?)</td>', text)
    "Return -1 if nothing found"
    if not start_date:
        return -1
    else:
        return start_date[0]


def get_all_historical_value(fund_id: str, start_date: str):
    """
    start_date: str, format:  "2019-01-02"
    end_date: str, format:  "2019-01-02", default=today - 1
    """
    # per is the number of values in each page of the JQuery (default max=20)
    per = 20
    end_date = (datetime.datetime.today()-datetime.timedelta(1)).date()
    end_date = str(end_date)

    # Test to find how many pages are there
    nav_url = f'http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz' \
          f'&code={fund_id}&page=1&sdate={start_date}&edate={end_date}&per={per}'
    response = requests.get(nav_url, headers={'user-agent': choose_user_agent()})
    text = response.text
    max_pages = int(re.findall('pages:(.*?),', text)[0])

    NAV = []
    for page in range(1, max_pages+1):
        # page is the number of pages out of the JQuery
        nav_url = f'http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz' \
              f'&code={fund_id}&page={page}&sdate={start_date}&edate={end_date}&per={per}'
        response = requests.get(nav_url, headers={'user-agent': choose_user_agent()})
        text = response.text
        soup = BeautifulSoup(text, 'lxml')
        table = soup.find('table')

        one_page_NAV = []
        for tr in table.findAll('tr'):
            row = []
            for td in tr.findAll('td'):
                row.append(td.getText())
            # Skip empty row
            if not row:
                continue
            else:
                one_page_NAV.append(row)

        NAV.extend(one_page_NAV)
        unit_pages = max_pages/20
        process = int(page/unit_pages)
        print("\r{0} Loading: {1}{2}%".format(fund_id, "■"*process, 5*process), end="")
        # Sleep for a random time after visiting a website
        time.sleep(2*random.random())

    NAV = pd.DataFrame(NAV, columns=['净值日期', '单位净值', '累计净值', '日收益率', '申购状态', '赎回状态', '分红送配'])
    return NAV


if __name__ == '__main__':
    fund_id = '011174'
    start_date = get_start_date(fund_id)
    NAV = get_all_historical_value(fund_id, start_date)
    NAV.to_excel(f'{fund_id}.xlsx', index=False)


