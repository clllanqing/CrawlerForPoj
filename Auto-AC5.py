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

def isWindows():
    if 'Windows' in platform.system():
        return True
    else:
        return False

def sprint(s):
    if isWindows():
        s=s.encode('gbk')
    print s

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

def cpp_clean(cpp):
    dec=r'<pre [^>]*>(.*)<[^>]*/pre>'
    redec=re.compile(dec, re.S|re.I|re.M)
    ls=re.findall(redec,cpp)
    if len(ls)>0:
        return ls[0]
    else:
        return cpp

@timelimited(60)
def get_cpp_from_link(url):
#     print url
    bsobj=BeautifulSoup(get_page_source(url),'lxml')
    cpp_list=[]
    try:
        cpp_li=bsobj.findAll('pre',{'class':'cpp','name':'code'})
        for i in cpp_li:
            cpp=i.get_text()
            if 'include' in cpp:
                cpp_list.append(cpp_clean(cpp))
                sprint(u'[*] 获取到一个新的CPP文件……')
            if len(cpp_list)>5:
                break
        sprint(u'%s %d %s' %( u'[*] 共获取',len(cpp_list),u'个CPP……'))
    except AttributeError as e:
        sprint(u'[*] 获取CPP内容出错，正在获取下一条……')
#     print '[*] 获取完成……'
    return cpp_list

@timelimited(50)
def login_hdu(driver):
    sprint(u'[*] 检查登录状态……')
    driver.get('http://acm.hdu.edu.cn/')
    dec=r'1404091012'
    redec=re.compile(dec, re.S|re.I|re.M)
    lis=re.findall(redec,driver.page_source)
    if len(lis)!=0:
        sprint (u'[*] 已登录……')
        return driver
    username=driver.find_element_by_name('username')
    username.send_keys('1404091012')
    pwd=driver.find_element_by_name('userpass')
    pwd.send_keys('87zhanshen')
    driver.find_element_by_name('login').click()
    driver.refresh()
    driver.get_screenshot_as_file('hdulogin.png')
    sprint (u'[*] 登陆成功……')
    return driver    

@timelimited(30)
def cpp_submit(id,cpp,driver):
    driver.get('http://acm.hdu.edu.cn/submit.php?pid='+str(id))
    try:
        sprint (u'%s %d' % (u'[*] 代码长度：',len(cpp)))
        driver.find_element_by_name('usercode').send_keys(cpp)
        driver.find_element_by_xpath('/html/body/table/tbody/tr[4]/td/form/table/tbody/tr[6]/td/input[1]').click()
        driver.refresh()
    except Exception as e:
        sprint(u'%s' % e.message)
        sprint (u'Error')
    s(6)

          
def write_html(page_source,url):
    with open(url,'w') as f:
        f.write(page_source)



@timelimited(40)
def find_anser_link(id):
    sprint( u'[*] 正在获取链接……')
    list=[]
    driver=get_headers_driver()
    try:
        driver.get("http://so.csdn.net/so/search/s.do?q=&t=codes_snippet&o=&s=&l=null")
    except Exception,e:
        print e
        driver.get_screenshot_as_png('03.png')
        exit(0)
    elem = driver.find_element_by_id('q1')
    elem.send_keys('hdu'+str(id))
    elem.send_keys(Keys.ENTER)
    driver.refresh()
    bsobj=BeautifulSoup(driver.page_source,'lxml')
    dl_list=bsobj.findAll('dl',{'class':'search-list'})
    sprint(u'%s %d' % (u'[*] 共获取链接数：',len(dl_list)))
    for dl in dl_list:
        a=dl.find('dt').find('span',{'class':'csdn-tracking-statistics','data-mod':'popu_178'}).find('a')
        tx=a.get_text()
        if ('hdu' in tx) or ('HDU' in tx) or ('Hdu' in tx):
            if str(id) in tx:
                list.append(a.get('href'))
    driver.quit()
    sprint(u'%s %d %s' % (u'[*] 筛选完成,共',len(list),u'条有效链接……'))
    return list

@timelimited(20)
def judge_number(id):
    sprint(u'%s %d %s' % (u'[*] 判断题目hdu',id,u'是否存在……'))
#     driver=get_headers_driver()
#     driver.get('http://acm.hdu.edu.cn/showproblem.php?pid='+str(id))
    page_source=get_page_source('http://acm.hdu.edu.cn/showproblem.php?pid='+str(id))
    bsobj=BeautifulSoup(page_source,'lxml')
    h1=bsobj.find('h1').get_text()
    if h1=='System Message':
        return False
    else:
        return True

@timelimited(30)
def isAC(id,driver,cnt):
    try:
        driver.get('http://acm.hdu.edu.cn/status.php?first=&pid='+str(id)+'&user=1404092007&lang=0&status=0')   
        sta=driver.find_element_by_xpath('//*[@id="fixed_table"]/table/tbody/tr[2]/td[3]/font') 
        while sta.text=='Queuing' or sta.text=='Compiling' or sta.text=='Running':
            sprint(u'[*] 队列中……')
            s(3)
            driver.refresh()
            sta=driver.find_element_by_xpath('//*[@id="fixed_table"]/table/tbody/tr[2]/td[3]/font') 
        if sta.text=='Accepted':
            return [True,0]
        else:
            sprint(u'%s %s' % (u'[*] 未通过……',sta.text))
            return [False,0]
    except Exception, e:
        sprint(u'%s %d' % (u'[*] 找不到Judge结果，正在重试……',cnt))
        s(3)
        if cnt>=2:
            return [False,1]
        return isAC(id, driver,cnt+1)

def get_idmin():
    idmin=1000
    try:
        with open('idmin.txt','r') as f:
            idmin=int(f.read())+1
    except Exception,e:
        sprint(u'%s' % e.message)
        sprint(u'[*] 从起始位置开始……')
    sprint(u'%s %d %s' % (u'[*] 从hdu',idmin,u'开始'))
    return idmin
       
def set_idmin(id):
    with open('idmin.txt','w') as f:
        f.write(str(id))
          
def restart_pro():
    sprint(u'[*] 遇到故障，正在重启……')
    python = sys.executable
    os.execl(python, python, * sys.argv)
    
def main():
    print '\n'
    sprint(u'****Warning : 本程序仅供娱乐，请适量使用并添加延迟，不要给HDU服务器造成压力****')
    sprint(u'****Warning : 本程序仅供娱乐，请适量使用并添加延迟，不要给HDU服务器造成压力****')
    sprint(u'****Warning : 本程序仅供娱乐，请适量使用并添加延迟，不要给HDU服务器造成压力****')
    sprint(u'(重要的话说三遍)')
#     s(3)
    total_cnt=0
    ac_cnt=0
    jg_tm=45
    bg_tm=time.time()
    restart_flag=0
    sprint( u'[*] 启动程序……')
    idmin=get_idmin()
    idmax=6015
    sprint( u'[*] 登录账号……')
    login_cnt=1
    while True:
        try:
            driver=get_headers_driver()
            driver=login_hdu(driver)
            break
        except Exception,e:
            sprint(u'%s' % e.message)
            sprint(u'%s %d' % (u'[*] 登录超时，正在重试',login_cnt))
            login_cnt+=1
            if login_cnt>=5:
                break
    ss=set([])
    for id in range(idmin,idmax):
        print '\n\n'
        ss.clear()
        stime=time.time()
        AC_flag=False
        ID_flag=True
        SUB_flag=False
        print time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        judge_test_cnt=1
        while True:
            try:
                if judge_number(id):
                    sprint(u'%s %d %s' % (u'[*] 正在处理hdu',id,u'……'))
                    find_test_cnt=1
                    while True:
                        try:
                            link_list=find_anser_link(id)
                            urlcnt=1
                            for url in link_list:
                                sprint(u'%s %d %s %d %s' % (u'[*] 正在处理hdu',id,u'的第',urlcnt,u'个链接……'))
                                urlcnt+=1
                                get_cpp_test_cnt=1
                                while True:
                                    try:
                                        cpp_list=get_cpp_from_link(url)
                                        cppcnt=1
                                        for cpp in cpp_list:
                                            if cpp in ss:
                                                sprint( u'[*] 当前CPP已进行过尝试……')
                                                continue
                                            else:
                                                ss.add(cpp)
                                            driver=login_hdu(driver)
                                            sprint(u'%s %d %s' % (u'[*] 正在尝试第',cppcnt,u'个CPP……'))
                                            cppcnt+=1
                                            submit_test_cnt=1
                                            while True:
                                                try:
                                                    cpp_submit(id, cpp.replace('\t',"    "), driver)
                                                    SUB_flag=True
                                                    ac_re=isAC(id, driver, 1)
                                                    if ac_re[0]:
                                                        AC_flag=True
                                                        sprint(u'%s %d %s' % (u'[*] hdu',id,u'已成功AC!'))
                                                    if ac_re[1]==0:
                                                        restart_flag=0
                                                    else:
                                                        restart_flag+=1
                                                    if restart_flag>3:
                                                        set_idmin(max(id,1000))
                                                        restart_pro()
                                                    break
                                                except Exception,e:
                                                    sprint(u'%s %d' % (u'[*] 提交CPP超时，正在重试……',submit_test_cnt))
                                                submit_test_cnt+=1
                                                if submit_test_cnt>=3:
                                                    break
                                            if restart_flag>3:
                                                set_idmin(max(id,1000))
                                                restart_pro()
                                            if AC_flag:
                                                break    
                                        break
                                    except Exception,e:
                                        sprint(u'%s' % e.message)
                                        sprint(u'%s %d' % (u'[*] 获取CPP超时，正在重试……',get_cpp_test_cnt))
                                    get_cpp_test_cnt+=1
                                    if get_cpp_test_cnt>=3:
                                        break
                                if restart_flag>3:
                                    set_idmin(max(id,1000))
                                    restart_pro()
                                if AC_flag:
                                    break
                            break
                        except Exception,e:
                            sprint(u'%s' % e.message)
                            sprint(u'%s %d' % (u'[*] 获取题解链接超时，正在重试……',find_test_cnt))
                        find_test_cnt+=1
                        if restart_flag>3:
                            set_idmin(max(id,1000))
                            restart_pro()
                        if find_test_cnt>=5:
                            break        
                else:
                    sprint(u'%s %d %s' % (u'[*] 题目hdu',id,u'不存在,跳过……'))
                    ID_flag=False
                break
            except Exception,e:
                sprint(u'%s %d' % (u'[*] 判断题号超时，正在重试……',judge_test_cnt))
            judge_test_cnt+=1
            if judge_test_cnt>=5:
                break
        if restart_flag>3:
            set_idmin(max(id,1000))
            restart_pro()
        set_idmin(id)
        etime=time.time()
        jg=etime-stime
        if not ID_flag:
            continue
        if AC_flag:
            ac_cnt+=1
        total_cnt+=1
        sprint(u'%s %d %s %d' % (u'[*] 当前  AC / TOTAL :',ac_cnt,u'/',total_cnt))
        sprint(u'%s %.2f %s' % (u'[*] AC率 :',(1.0*ac_cnt*100/total_cnt),u'%'))
        sprint(u'%s %.2f h' % (u'[*] 总耗时  :',(1.0*(etime-bg_tm)/60/60)))
        if not SUB_flag:
            continue
        if jg<jg_tm:
            sprint(u'%s %.2f %s' % (u'[*] 速度较快，暂停',(jg_tm-jg),u'秒'))
            s(jg_tm-jg)
        
        
def test():
    try:
        page_source=get_page_source('http://acm.hdu.edu.cn/userstatus.php?user=1404092007')
        bsobj=BeautifulSoup(page_source,'lxml')
        ac_a_l=bsobj.find('p',{'align':'left'}).findAll('a')
        print len(ac_a_l)
        for a in ac_a_l:
            print a.get_text()
    except Exception,e:
        sprint(e.message)
        
if __name__ == "__main__":
    main()
# test()