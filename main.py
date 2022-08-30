import os
import requests
import configparser
from bs4 import BeautifulSoup
import ddddocr
import re


class Bot:
    def __init__(self,acc,pwd):
        
        # for requests 
        self.baseUrl="https://course.fcu.edu.tw/"
        self.LoginUrl="{}Login.aspx".format(self.baseUrl)
        self.captchaUrl="{}validateCode.aspx".format(self.baseUrl)

        self.sess = requests.session()
        self.sess.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'
        
        # login information
        self.acc= acc
        self.pwd = pwd

        # for picture recognize 
        self.ocr = ddddocr.DdddOcr()

        #course data 
        self.course = []

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
        
        parser = BeautifulSoup(loginHtml.text, 'lxml')
        captcha = self.getCaptcha()

        loginPayLoad = {
            "__EVENTTARGET": "ctl00$Login1$LoginButton",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "__VIEWSTATE": parser.select("#__VIEWSTATE")[0]['value'],
            "__VIEWSTATEGENERATOR": parser.select("#__VIEWSTATEGENERATOR")[0]['value'],
            "__VIEWSTATEENCRYPTED":"", 
            "__EVENTVALIDATION": parser.select("#__EVENTVALIDATION")[0]['value'],
            "ctl00$Login1$RadioButtonList1": "zh-tw",
            "ctl00$Login1$UserName": self.acc, 
            "ctl00$Login1$Password": self.pwd,
            "ctl00$Login1$vcode": captcha,
            "ctl00$temp": '',
        }

        print(loginPayLoad)

        result = self.sess.post(self.LoginUrl, data= loginPayLoad)

        with open("result.html",'a',encoding=result.encoding) as f:
          f.write(result.text)
        
        if("Idle time" in result.text):
          print("登入成功")
        
        return result.text

    def getInterest(self,web):
        self.course = re.findall("ctl00\$MainContent\$TabContainer1\$tabSelected\$gvWishList\$ctl\d{0,2}\$btnAdd",web)
    
    def sel (self):
        

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
    
    myBot = Bot(Account, Password)
    web = myBot.login()
    myBot.getInterest(web)
    myBot.sel()
