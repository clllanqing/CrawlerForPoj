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

@timelimited(60)
def Print(s):
        print s
        with open('/root/workspaces/CrawlerForPoj/src/rizhi.txt','a') as f:
            f.write(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))+'    '+s+'\n')
            f.close()

@timelimited(60)
def restart_pro():
    Print ('[*] 遇到故障，正在重启…..…')
    python = sys.executable
    os.execl(python, python, * sys.argv)
    
@timelimited(60)   
def s(t):
    time.sleep(t)
    


@timelimited(60)
def GetIdMin():
    if os.path.exists('/root/workspaces/CrawlerForPoj/src/Poj_IdMin.txt'):
        with open('/root/workspaces/CrawlerForPoj/src/Poj_IdMin.txt','r') as f:
            if os.path.getsize('/root/workspaces/CrawlerForPoj/src/Poj_IdMin.txt')==0 :
                idmin=1000
            else:
                idmin=int(f.read())+1
    else :
        idmin=1000
    return idmin

@timelimited(60)
def GetHeaderDriver():
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
 
@timelimited(60)
def LoginPoj(UserName,UserPasswd):
    driver=GetHeaderDriver()
    driver.get('http://www.poj.org/')
    driver.find_element_by_name('user_id1').send_keys(UserName)
    driver.find_element_by_name('password1').send_keys(UserPasswd)
    driver.find_element_by_xpath('/html/body/table[1]/tbody/tr[3]/td[5]/form/input[1]').click()
    driver.refresh()
    return driver

@timelimited(60)
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

@timelimited(60)
def JudgeIdExist(id):
    s(5)
    Print('判断'+str(id)+'题是否存在...')
    url='http://poj.org/problem?id='+id
    html=get_page_source(url)
    soup=BeautifulSoup(html,'lxml')
    list=soup.findAll('p', {'class':'pst'},limit=1)
    if list==None :
	s(10)
	return False
    if(len(list)==1):
         Print(str(id)+'题目存在')
         return True
    else:
        Print(str(id)+'题目不存在')
        return False
    
@timelimited(100)   
def FindUrlList(id):
    Print('开始查找'+str(id)+'题url列表')
    driver=GetHeaderDriver()
    urllist=[]
    driver.get("http://so.csdn.net/so/search/s.do?q=&t=codes_snippet&o=&s=&l=null")
    driver.find_element_by_xpath('//*[@id="q1"]').send_keys('poj '+str(id))
    driver.find_element_by_xpath('//*[@id="q1"]').send_keys(Keys.ENTER)
    soup=BeautifulSoup(driver.page_source,'lxml')
    list=soup.findAll('dl',{'class':'search-list'})
    for lis in list :
        urlc=lis.find('dt').find('span',{'class':'csdn-tracking-statistics','data-mod':'popu_178'}).find('a').get('href')
        emlist=lis.find('dt').find('span',{'class':'csdn-tracking-statistics','data-mod':'popu_178'}).find('a').find('em')
        title_text = lis.find('dt').find('span',{'class':'csdn-tracking-statistics','data-mod':'popu_178'}).find('a').get_text()
        pojstr=['POJ '+id , 'poj '+id , 'POJ_'+id , 'poj_'+id , 'poj'+id , 'POJ'+id]
        for pojst in pojstr:
            if pojst in title_text:
                urllist.append(urlc)
                break;
        if len(urllist)>10:break
    Print(str(id)+'题共找到'+str(len(urllist))+'条链接')
    driver.quit()
    return urllist
 
@timelimited(60)       
def FindCppList(url):
    Print('开始查找链接 '+url+' 列表中的所有cpp')
    cpplist=[]
    soup=BeautifulSoup(get_page_source(url),'lxml')
    list=soup.findAll('pre',{'class':'cpp','name':'code'})
    if list==None : return cpplist
    for i in list:
        cpp=i.get_text()
        if '#include' in cpp:
            cpplist.append(cpp)
        if len(cpplist)>5 :break
    Print('这条链接共找到'+str(len(cpplist))+'个cpp')
    return cpplist
@timelimited(60) 
def CppSubmit(driver,id,cpp,url,index):
    Print('开始提交这条链接  '+url+'  的第+'+str(index)+'个cpp')
    driver.get("http://poj.org/submit?problem_id="+id)
    driver.find_element_by_xpath('/html/body/table[2]/tbody/tr/td/form/div/select').find_elements_by_tag_name("option")[0].click()  
    ele=driver.find_element_by_name('source')
    ele.send_keys('#include<stdio.h>\n#include<math.h>\n#include<string.h>\n')
    ele.send_keys(cpp)
    driver.find_element_by_name('submit').click()
    driver.refresh()
    
@timelimited(60) 
def IsAc(id,UserName):
    s(5)
    Print('判断是否通过')
    driver=GetHeaderDriver()
    driver.get('http://poj.org/status?problem_id='+str(id)+'&user_id='+UserName+'&result=&language=')
    driver.refresh()
    driver.get_screenshot_as_file('IsAc.png')
    sta=driver.find_element_by_xpath('/html/body/table[2]/tbody/tr[2]/td[4]')
    while sta.text=='Queuing' or sta.text=='Compiling' or sta.text=='Running & Judging':
        Print('队列等待中...')
        s(2)
        driver.refresh()
        sta=driver.find_element_by_xpath('/html/body/table[2]/tbody/tr[2]/td[4]')
    if sta.text=='Accepted':
        Print('结果为'+str(sta.text))
        return True
    else:
         Print('结果为'+str(sta.text))
         return False

@timelimited(1800)  
def main():
    Print ('start crawler_poj......')
    idmax=6000
    idmin=GetIdMin()
    UserName='caolulu_test1'
    UserPasswd='caolulu258'
    ac=0.0
    wa=0.0
    AcProbability=0
    Print('访问poj网页.....')
    driver=LoginPoj(UserName,UserPasswd)
    Print("登录成功!  开始爬虫!")
    for id in range(idmin,idmax):
        try:
            Print('**********开始处理'+str(id)+'题**************')
            if ac!=0:Print('目前通过率: '+str(ac/(wa+ac)*100)+'%')
            else:Print('目前通过率: 0%')
            acflag=False
            if JudgeIdExist(str(id)):
                urllist=FindUrlList(str(id))
                for url in urllist:
                    try:
                        if(acflag==True): break
                        cpplist=FindCppList(str(url))
                        for i in range(len(cpplist)):
                            try:
                                cpp=cpplist[i]
                                if(acflag==True): break
                                driver=LoginPoj(UserName, UserPasswd)
                                s(10)
                                CppSubmit(driver,str(id),cpp.replace('\t','    '),url,i)
                                acflag=IsAc(str(id),UserName)
                                if acflag:
                                    ac+=1
                                    with open('/root/workspaces/CrawlerForPoj/src/Poj_IdMin.txt','w') as f:
                                        f.write(str(id))
                                        f.close()
                                else:wa+=1
                            except Exception,e:
                                Print('find error:'+str(e))
                    except Exception,e:
                        Print('find error:'+str(e))
        except Exception,e:
            Print('find error:'+str(e))
    
if __name__ == "__main__":
    try:
        main()
    except Exception,e:
        Print('??????')
        restart_pro()    
    
