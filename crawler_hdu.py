#coding=utf-8
import urllib,urllib2
import lxml
from selenium import webdriver  
from bs4 import BeautifulSoup
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import re
import time
import sys
from threading import Thread
from selenium.common.exceptions import TimeoutException
from wheel.signatures.djbec import double
from selenium.webdriver.common.keys import Keys
import os
import platform

class TimeoutException(Exception):
    pass
ThreadStop = Thread._Thread__stop#获取私有函数

def timelimited(timeout):
    def decorator(function):
        def decorator2(*args,**kwargs):
            class TimeLimited(Thread):
                def __init__(self,_error= None,):
                    Thread.__init__(self)
                    self._error =  _error
                    
                def run(self):
                    try:
                        self.result = function(*args,**kwargs)
                    except Exception,e:
                        self._error =e

                def _stop(self):
                    if self.isAlive():
                        ThreadStop(self)

            t = TimeLimited()
            t.start()
            t.join(timeout)
     
            if isinstance(t._error,TimeoutException):
                t._stop()
                raise TimeoutException('timeout for %s' % (repr(function)))

            if t.isAlive():
                t._stop()
                raise TimeoutException('timeout for %s' % (repr(function)))

            if t._error is None:
                return t.result

        return decorator2
    return decorator


def s(t):
    time.sleep(t)
def get_idmin():
    idmin=1000
    try:
        with open('idmin.txt','r') as f:
            idmin=int(f.read())+1
    except Exception,e:
        file=open('idmin.txt','w')
        file.close()
        print "从1000开始 并创建了本地文件idmin.txt"
        idmim=1000
    return idmim
            
            
def get_headers_driver():
    desired_capabilities= DesiredCapabilities.PHANTOMJS.copy()
    headers = {'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.8',
    'Cache-Control': 'max-age=0',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36',#这种修改 UA 也有效
    'Connection': 'keep-alive',
    'Referer':'http://www.baidu.com/'
    }
    for key, value in headers.iteritems():
        desired_capabilities['phantomjs.page.customHeaders.{}'.format(key)] = value
    desired_capabilities['phantomjs.page.customHeaders.User-Agent'] ='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
    driver= webdriver.PhantomJS(desired_capabilities=desired_capabilities, service_args=['--load-images=no'])
    return driver    


@timelimited(50)
def login_hdu(driver):
    print "检查登录状态"
    driver.get("http://acm.hdu.edu.cn/")
    user_name='1404012017'
    user_pass='caolulu258'
    redec=re.compile(user_name,re.S|re.I|re.M)
    list=re.findall(redec, driver.page_source)  ###############################3
    if len(list)!=0:
        print "已经登录了!"
        return driver
    driver.find_element_by_name("username").send_keys(user_name)
    driver.find_element_by_name("userpass").send_keys(user_pass)
    driver.find_element_by_name("login").click()
    driver.refresh()
    print "登录成功"
    driver.get_screenshot_as_file("jietu/登录成功.png")
    return driver

@timelimited(30)
def get_page_source(url):
    headers = {'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.8',
        'Cache-Control': 'max-age=0',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36',#这种修改 UA 也有效
        'Connection': 'keep-alive',
        'Referer':'http://www.baidu.com/'
        }
    data = None
    req = urllib2.Request(url, data, headers)
    response = urllib2.urlopen(req)
    page_source=response.read()
    return page_source
    

@timelimited(30)
def judge_number(id):
    page_source=get_page_source('http://acm.hdu.edu.cn/showproblem.php?pid='+str(id))
    bs0bj=BeautifulSoup(page_source,'lxml')
    h1=bs0bj.find('h1').get_text()
    if h1=='System Message':
        return False
    else:
        return True
    
    
@timelimited(30)
def find_answer_link(id):
    print("正在id获取链接...")
    list=[]
    driver=get_headers_driver()
    try:
        driver.get("http://so.csdn.net/so/search/s.do?q=&t=codes_snippet&o=&s=&l=null")
    except Exception,e:
        driver.get_screenshot_as_png('抓取CSDN错误.png')
    elem = driver.find_element_by_id('q1')
    elem.send_keys('hdu'+str(id))
    elem.send_keys(Keys.ENTER)
    driver.refresh()
    bsobj=BeautifulSoup(driver.page_source,'lxml')
    dl_list=bsobj.findAll('dl',{'class':'search-list'})
    print "获取链接",len(list)
    for dl in dl_list:
        a=dl.find('dt').find('span',{'class':'csdn-tracking-statistics','data-mod':'popu_178'}).find('a')
        tx=a.get_text()
        if ('hdu' in tx) or ('HDU' in tx) or ('Hdu' in tx):
            if str(id) in tx:
                list.append(a.get('href'))
    driver.quit()
    print "有效链接",len(list),'条'
    return list

@timelimited(60)
def get_cpp_from_link(url):
    bs0bj=BeautifulSoup(get_page_source(url),'lxml')
    cpp_list=[]
    try:
        cpp_li=bs0bj.findAll('pre',{'class':'cpp','name':'code'})
        for i in cpp_li:
            cpp=i.get_text()
            if 'include' in cpp:
                cpp_list.append(cpp)
                print '获取到一个新的CPP文件……'
            if len(cpp_list)>5:
                break
        print '共获取',len(cpp_list),'个cpp'
    except AttributeError as e:
        print' 获取CPP内容出错，正在获取下一条……'
    return cpp_list



@timelimited(30)
def cpp_submit(id,cpp,driver):
    driver.get('http://acm.hdu.edu.cn/submit.php?pid='+str(id))
    try:
        print '代码长度：',len(cpp)
        driver.find_element_by_name('usercode').send_keys(cpp)
        driver.find_element_by_xpath('/html/body/table/tbody/tr[4]/td/form/table/tbody/tr[6]/td/input[1]').click()
        driver.refresh()
        print '提交成功'
    except Exception as e:
        print '提交cpp  error'
    s(6)
   
   
@timelimited(30)
def isAc(id,driver,cnt):
    try:
        driver.get('http://acm.hdu.edu.cn/status.php?first=&pid='+str(id)+'&user=1404092007&lang=0&status=0')   
        sta=driver.find_element_by_xpath('//*[@id="fixed_table"]/table/tbody/tr[2]/td[3]/font') 
        while sta.text=='Queuing' or sta.text=='Compiling' or sta.text=='Running':
            s(3)
            driver.refresh()
            sta=driver.find_element_by_xpath('//*[@id="fixed_table"]/table/tbody/tr[2]/td[3]/font') 
        if sta.text=='Accepted':
            return True
        else:
            print '未通过'
            return False
    except Exception, e:
        print '找不到Judge结果，正在重试……'
        s(3)
        return False

def main():
    print '\n'
    print "this is crawler for hdu"
    
    print "启动程序...."
    
    idmin=get_idmin()  
    idmax=6015
  
    print "开始登录账号..."
    
    driver=get_headers_driver()
    driver=login_hdu(driver)
    
    ss=set()
    for id in range(idmin,idmax):
            print '开始处理' ,id,'题'
            ss.clear()
            ac_flag=False
            if judge_number(id):
                print "id 题 存在..."
                link_list=find_answer_link(id)
                urlcnt=1
                for url in link_list:
                    if ac_flag==True: break
                    try:
                        if url==5:break
                        urlcnt+=1
                        cpp_list=get_cpp_from_link(url)
                        cppcnt=1
                        for cpp in cpp_list: 
                            if ac_flag==True: break
                            try:   
                                if cppcnt == 5:  break
                                cppcnt+=1
                                print '处理',id,'题  第',urlcnt,'链接  第’,cppcnt cpp代码'
                                get_cpp_test_cnt=1
                                if cpp in ss:
                                    print "尝试过了"
                                    continue
                                else :
                                    ss.add(cpp)
                                driver=login_hdu(driver)
                                cpp_submit(id,cpp.replace('\t','    '),driver)
                                sub_flag=True
                                if isAc(id,driver,1) :
                                    print id,"题目已经AC！！！"
                                    ac_flag=True
                            except Exception as e:
                                print 'cuowu'
                    except Exception as e:
                            print 'cuowu'
        except Exception as e:
                            print 'cuowu'                    
    
             
                        
                    
        