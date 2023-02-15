"""
Author: Randal JIn
Function: get net asset value of Jinxin No.1 positions
Source: Eastmoney, Wind, Chinabond
"""

import pandas as pd
import os
import datetime
import random
import time
import requests
from JinxinNo1.params import user_agents

# 1、获取产品代码
os.chdir('D:/Raychill Capital/Inboard/JinxinNo1')
df = pd.read_excel('./港曾-晋奕定投计划1号.xlsx', sheet_name='晋信私募1号日报')
df.dropna(how='all', axis=0, inplace=True)
df.dropna(how='all', axis=1, inplace=True)
df.reset_index(inplace=True, drop=True)

port_loc = df[df.iloc[:, 0] == '基金持仓'].index[0]
port_list = df.iloc[port_loc+1:df.shape[0]+1, 0:2]
port_list.reset_index(inplace=True, drop=True)
port_list.columns = ['产品简称', '产品代码']
port_list.产品代码 = port_list.产品代码.apply(lambda x: x.replace('.OF', ''))

# 2、获取基金净值

result = pd.DataFrame()
for i in range(0, port_list.shape[0]):
    header = random.choice(user_agents)
    name = port_list.产品简称[i]
    code = port_list.产品代码[i]
    url = 'http://fund.eastmoney.com/'+code+'.html'
    if name == '长城收益宝货币B':
        fv = pd.read_html(url)[5]
        # Convert str date to datetime date
        fv['日期'] = [datetime.datetime.date(pd.to_datetime(d)) for d in fv['日期']]
    else:
        fv = pd.read_html(url)[7]
        # Add a year prefix to the date
        fv['日期'] = [datetime.datetime.date(pd.to_datetime('2022-'+d)) for d in fv['日期']]
    fv.insert(0, '产品名称', name)
    fv.sort_values(['日期'], ascending=True, inplace=True)
    result = pd.concat([result, fv], axis=0)
    print('Data obtained: '+name)
    time.sleep(2 * random.random())


# 3、获得 wind全A 指数
header = random.choice(user_agents)
url = 'https://wx.wind.com.cn/indexofficialwebsite/indexprice?indexid=881001.WI&lan=cn'
response = requests.get(url, headers={'user-agent': header})
text = response.json()
trading_data = text['Result']['List']
trading_data_df = pd.DataFrame(trading_data)
# 获取数据的交易时间是 13 位时间戳
# 格式转换顺序：13位时间戳 -> 整数 -> 10位时间戳 -> 结构化时间 -> 字符串 -> datetime.datetime.date
timeArray = trading_data_df['tradeDate'].apply(int)
timeArray = timeArray.to_list()
timeArray = [time.localtime(t/1000) for t in timeArray]
timeArray = [datetime.date(t.tm_year, t.tm_mon, t.tm_mday) for t in timeArray]
trading_data_df['tradeDate'] = timeArray
print('Data obtained: 万得全A指数')
# 将wind全A数据和净值数据格式对齐
windA = trading_data_df[['tradeDate', 'close']].copy()
windA.columns = ['日期', '单位净值']
windA.insert(0, '产品名称', 'wind全A指数')
windA.insert(3, '累计净值', windA['单位净值'])
windA.insert(4, '日增长率', windA['单位净值'].diff(1)/windA['单位净值'])
windA['日增长率'] = windA['日增长率'].apply(lambda x: "%.2f%%" % (x * 100))


# 4、获取中债-新综合指数
header = random.choice(user_agents)
url = 'https://yield.chinabond.com.cn/cbweb-mn/indices/singleIndexQuery?' \
      'indexid=8a8b2ca0332abed20134ea76d8885831&&qxlxt=00&&zslxt=CFZS&&lx=1&&locale='

"""
熟悉的 jQuery ajax 数据查询
看了一遍源代码，似乎没有用到什么特别的加密，不涉及随机数之类的
最多是 indexid 用 md5 加密了一下，虽然没看到这一步是在哪里完成的
加密前的 indexid 其实就是 checked treeNode，我推测是网页左侧被勾选的指数，在树状目录结构中的编号
刷新了两次页面，这个 url 并没有发生改变，这意味着这个 url 是可以长期使用的
每次都可以 post 到全部历史数据，中债网确实特别友好
"""

response = requests.post(url, headers={'user-agent': header})
data = response.json()
CFZS = data['CFZS_00']
# 格式转换顺序：13位时间戳 -> 整数 -> 10位时间戳 -> 结构化时间 -> 字符串 -> datetime.datetime.date
timeArray = list(CFZS.keys())
timeArray = [int(t) for t in timeArray]
timeArray = [time.localtime(t/1000) for t in timeArray]
timeArray = [datetime.date(t.tm_year, t.tm_mon, t.tm_mday) for t in timeArray]
# 将中债新综合指数和净值数据格式对齐
NAV = list(CFZS.values())
CFZS_df = pd.DataFrame({'日期': timeArray, '单位净值': NAV})
CFZS_df.insert(0, '产品名称', '中债新综合指数')
CFZS_df.insert(3, '累计净值', CFZS_df['单位净值'])
CFZS_df.insert(4, '日增长率', CFZS_df['单位净值'].diff(1)/CFZS_df['单位净值'])
CFZS_df['日增长率'] = CFZS_df['日增长率'].apply(lambda x: "%.2f%%" % (x * 100))
print('Data obtained: 中债新综合指数')
# 截取最近一月的数据（如果想要完整数据，就把下面两行注释掉）
prior_1m = datetime.datetime.today() - datetime.timedelta(30)
CFZS_df = CFZS_df.loc[CFZS_df[CFZS_df['日期'] > prior_1m.date()].index]


# 5、纵向合并数据并写入 excel
result = pd.concat([result, windA, CFZS_df], axis=0)
time_str = str(datetime.datetime.today()).split(' ')[0].replace('-', '_')
result.to_excel(f'JinxinNAV {time_str}.xlsx', index=False)



