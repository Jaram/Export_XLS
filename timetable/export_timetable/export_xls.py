# -*- coding:utf-8 -*-
import json
import base64
import logging
import math
import random
import requests
import rsa
import os
from bs4 import BeautifulSoup
from urllib import quote


class TimeTable(object):
    def __init__(self, log_level=logging.INFO):
        logging_format = '%(asctime)-15s %(message)s'
        logging.basicConfig(format=logging_format)
        self.logger = logging.getLogger('timetable_logger')
        self.logger.setLevel(log_level)
        self.is_login = False

        self.CHALLENGE_URL = 'https://portal.hanyang.ac.kr/sugang/findPkiChallenges.do'
        self.PUBLIC_URL = 'https://portal.hanyang.ac.kr/sugang/publicTk.do'
        self.SUGANG_URL = 'https://portal.hanyang.ac.kr/sugang/sulg.do'
        self.LOGIN_URL = 'https://portal.hanyang.ac.kr/sugang/lgnps.do'
        self.TIME_TABLE_URL = 'https://portal.hanyang.ac.kr/sugang/SuscAct/findSincheongGwamokSiganpyo.do'


    def login(self, ID, PW):
        """
        login procedure. it doesn't return True or False. but it will print any message.
        :param ID: required login. your id.
        :param PW: your pw.
        """
        self.session = requests.Session()
        req = self.session.get(self.SUGANG_URL)
        cookies = dict(WMONID=req.cookies['WMONID'], SUGANG_JSESSIONID=req.cookies['SUGANG_JSESSIONID'],
                       ipSecGb=base64.b64encode('1'), NetFunnel_ID='', loginUserId=base64.b64encode(ID))
        headers = {'Content-Type': 'application/json+sua; charset=utf-8'}

        req = self.session.post(self.CHALLENGE_URL, headers=headers)
        secret = json.loads(req.text)
        challenge = secret['challeng'][0]['value']
        keyNm = 'sso_00{0}'.format(random.randint(1, 3))
        publicTk_data = dict(keyNm=keyNm, encStr=ID)

        req = self.session.post(self.PUBLIC_URL, headers=headers, data=json.dumps(publicTk_data))
        public = json.loads(req.text)

        public_key_n = int(public['key'][0]['value'], 16)
        public_key_e = 65537
        self.PUBLIC_KEY = rsa.key.PublicKey(public_key_n, public_key_e)

        hashed_id = self.rsa_enc(ID, self.PUBLIC_KEY)
        hashed_pw = self.rsa_enc(PW, self.PUBLIC_KEY)

        login_data = dict(challenge=challenge, ipSecGb=1, keyNm=keyNm, loginGb=1, userId=hashed_id,
                          password=hashed_pw, signeddata='', symm_enckey='', systemGb='SUGANG',
                          returl='https://portal.hanyang.ac.kr/sugang/slgns.do?locale=ko')

        headers.pop('Content-Type')

        self.session.post(self.LOGIN_URL, headers=headers, data=login_data)
        cookies['_SSO_Global_Logout_url'] = ''

        req = self.session.get("https://portal.hanyang.ac.kr/sugang/sulg.do")
        soup = BeautifulSoup(req.text)
        self.STUDENT_ID = soup.find_all('span')[1].text.strip()

        if 'logoutLink2' in req.text:
            self.is_login = True
            self.logger.info('Login Completed')

    def rsa_enc(self, data, public_key):
        """
        encrypt by rsa. it was inspired by haegun Jeong.

        :param data: any encrypt data
        :param public_key: rsa.key.public_key
        """
        base64_encoded = base64.b64encode(data)
        length = len(base64_encoded)
        splitcnt = int(math.ceil(float(length) / 50))
        enc_final = ''

        for i in range(splitcnt):
            pos = i * 50
            end_pos = length if i == splitcnt - 1 else pos + 50
            enc_final += (rsa.encrypt(base64_encoded[pos:end_pos], public_key)).encode('hex')

        return enc_final


    def export(self, sosok_cd="Y0000383", 
               year="2014", jojik_cd="Y0000316"):
        if not self.is_login:
            raise TimetableError("Check your login")

        headers = {'Content-Type': 'application/json+sua; charset=utf-8'}
        data = dict(strHakbun=self.STUDENT_ID,
                    strJojikGbCd=jojik_cd,
                    strSosokCd=sosok_cd,
                    strSuupTerm="10",
                    strSuupYear=year)
        req = self.session.post(self.TIME_TABLE_URL, data=json.dumps(data), headers=headers)
        table_data = req.json()['DS_SUUPSC10TTM01'][0]['list']
        key_data = req.json()['DS_SUUPSC10TTM01'][0]['columnName']

        return dict(table_data=table_data, key_data=key_data)


class TimetableError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)
