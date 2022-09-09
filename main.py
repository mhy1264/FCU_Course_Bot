import os
import time
import requests
import configparser
from bs4 import BeautifulSoup as bs
import ddddocr
import re
import time

class Bot:
    def __init__(self,acc,pwd,DT):
        
        # for requests 
        self.baseUrl="https://course.fcu.edu.tw/"
        self.LoginUrl="{}Login.aspx".format(self.baseUrl)
        self.captchaUrl="{}validateCode.aspx".format(self.baseUrl)
        self.selectUrl = ""
        self.sess = requests.session()
        self.sess.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'
        
        #delay time 
        self.delayTime = DT

        # login information
        self.acc= acc
        self.pwd = pwd

        # for picture recognize 
        self.ocr = ddddocr.DdddOcr()

        #course data 
        self.course = []
        self.loginPayLoad = {
            "__EVENTTARGET": "ctl00$Login1$LoginButton",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "__VIEWSTATE": '',
            "__VIEWSTATEGENERATOR": '',
            "__VIEWSTATEENCRYPTED":"", 
            "__EVENTVALIDATION": '',
            "ctl00$Login1$RadioButtonList1": "zh-tw",
            "ctl00$Login1$UserName": self.acc, 
            "ctl00$Login1$Password": self.pwd,
            "ctl00$Login1$vcode": '',
            "ctl00$temp": '',
        }
        self.selPayLoad={}

    def log(self, msg):
        print(time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime()), msg)
        
    def getCaptcha(self):
        with self.sess.get(self.captchaUrl, stream= True) as captchaHtml:
            with open('captcha.png', 'wb') as img:
                img.write(captchaHtml.content)

        with open('captcha.png', 'rb') as f:
            img_bytes = f.read()
        
        return self.ocr.classification(img_bytes)

    def login(self):

        self.sess.cookies.clear()
        loginHtml = self.sess.get(self.LoginUrl)
        
        parser = bs(loginHtml.text, 'lxml')
        captcha = self.getCaptcha()

        self.loginPayLoad["__VIEWSTATE"]=parser.select("#__VIEWSTATE")[0]['value'],
        self.loginPayLoad["__VIEWSTATEGENERATOR"]=parser.select("#__VIEWSTATEGENERATOR")[0]['value'],
        self.loginPayLoad["__EVENTVALIDATION"]=parser.select("#__EVENTVALIDATION")[0]['value'],
        self.loginPayLoad["ctl00$Login1$vcode"]= captcha,

        #get select course temp URL
        result = self.sess.post(self.LoginUrl, data= self.loginPayLoad,allow_redirects=False) 

        if("帳號或密碼錯誤" in result.text):
          print ("帳號密碼錯誤")
          exit()
        else:
          self.selectUrl = result.headers['Location']
          result = self.sess.get(self.selectUrl)
          while ("Idle time" not in result.text):
              if ("目前不是開放時間" in result.text):
                  self.log("目前不是開放時間")
                  exit()
              else :
                self.log("Login Error, Try Again")  

        self.log("Login Success")
        
        return result.text

    def getInterest(self,web):
        results = re.findall("ctl00\$MainContent\$TabContainer1\$tabSelected\$gvWishList\$ctl\d{0,2}\$btnAdd",web)

        for result in results:
            if (result not in self.course):
                self.course.append(result)

        self.log(self.course)

    def sel(self):

      # get aspnet element 
      selectHttp = self.sess.get(self.selectUrl)

      parser = bs(selectHttp.text, 'lxml')

      self.selPayLoad = {
          "ctl00_ToolkitScriptManager1_HiddenField":"", 
          "ctl00_MainContent_TabContainer1_ClientState": '{"ActiveTabIndex":2,"TabState":[true,true,true]}',
          "__EVENTTARGET": '',
          '__EVENTARGUMENT': '',
          '__LASTFOCUS': '',
          '__VIEWSTATE':parser.select("#__VIEWSTATE")[0]['value'],
          '__VIEWSTATEGENERATOR': parser.select("#__VIEWSTATEGENERATOR")[0]['value'],
          '__VIEWSTATEENCRYPTED': '',
          '__EVENTVALIDATION':parser.select("#__EVENTVALIDATION")[0]['value'],
          'ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$ddlDegree': 1,
          'ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$ddlDept': '',
          'ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$ddlUnit': '',
          'ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$ddlClass': '',
          'ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$tbSubID': '',
          'ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$ddlWeek': '',
          'ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$ddlPeriod': '',
          'ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$tbCourseName': '',
          'ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$tbTeacherName': '',
          'ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$ddlUseLanguage': '01',
          'ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$ddlSpecificSubjects': 1,
          'ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$cbShowSelected': 'on',
     }

      # seperate url 
      mainReg="https:\/\/service\d{0,4}-sds.fcu.edu.tw\/"
      mainURL = re.findall(mainReg,self.selectUrl)[0]

      queryReg ='guid\S{0,50}tw'
      queryString = re.findall(queryReg,self.selectUrl)[0]

      self.selectUrl="{}AddWithdraw.aspx?{}".format(mainURL,queryString)

      while (len(self.course)):
        for course in self.course:

          # update course payLoad && send request
          self.selPayLoad["__EVENTTARGET"]=course
          selHtml = self.sess.post(self.selectUrl,data=self.selPayLoad)

          if("重新登入" in selHtml.text):
            self.login()
          else:
            # get msg for select result
            parser = bs(selHtml.text,'lxml')
            msg = parser.find(id = "ctl00_MainContent_TabContainer1_tabSelected_lblMsgBlock").text

            self.log(msg)

            if("加選成功" in msg):
              self.course.remove(course)
            time.sleep(self.delayTime)
          
    
if __name__=="__main__":

    configFilename = 'accounts.ini'
    if not os.path.isfile(configFilename):
        with open(configFilename, 'a') as f:
            f.writelines(["[Default]\n", "Account= your account\n", "Password= your password"])
            print('input your username and password in accounts.ini')
            exit()
    # get account info fomr ini config file
    config = configparser.ConfigParser()
    config.read(configFilename)
    Account = config['Default']['Account']
    Password = config['Default']['Password']

    # Time Parameter, sleep n seconds
    delayTime = 5 

    myBot = Bot(Account, Password,delayTime)
    web = myBot.login()
    myBot.getInterest(web)
    myBot.sel()
