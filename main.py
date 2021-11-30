import json
import pathlib
import time

import requests
import re
import configparser

# from aliyunsdkcore.request import CommonRequest
# from aliyunsdkcore.client import AcsClient
# from aliyunsdkcore.auth.credentials import AccessKeyCredential
# from aliyunsdkalidns.request.v20150109.DescribeDomainRecordsRequest import DescribeDomainRecordsRequest

import send_email
from logger import log


def now_time():
    return time.strftime('%Y-%m-%d %H:%M:%S')


# 查询记录
def check_ip():
    url = 'http://checkip.dyndns.com/'
    html_data = requests.get(url=url).text
    ip_data = re.findall('Address: (.*?)</body>', html_data)
    if ip_data:
        log.info(f'查询IP成功, 当前 {ip_data}， （by {url}）')
        return ip_data[0]
    else:
        raise Exception(f'查询IP失败！ {html_data}')


class AliUpdater:
    def __init__(self, update_record, access_key=None, access_secret=None):
        if not update_record:
            raise Exception('未设置 update_record')
        self.runner_name = 'aliyun'
        self.update_record = update_record
        self.credentials = AccessKeyCredential(access_key, access_secret)
        self.client = AcsClient(region_id='cn-chengdu', credential=self.credentials)

    def check_records(self, name, ip):
        request = DescribeDomainRecordsRequest()
        request.set_accept_format('json')
        request.set_DomainName("ymccc.xin")
        response = self.client.do_action_with_exception(request)
        json_res = json.loads(response)
        for item in json_res['DomainRecords']['Record']:
            if item['RR'] + '.' + item['DomainName'] == name and item['Type'] == 'A':
                if item['Value'] != ip:
                    return item['RecordId'], item['Value']
                else:
                    return None, None
        log.info(f'未找到记录 {name}')

    def set_records(self, record_id, name, ip):
        request = CommonRequest()
        request.set_accept_format('json')
        request.set_domain('alidns.cn-beijing.aliyuncs.com')
        request.set_method('POST')
        request.set_protocol_type('https')  # https | http
        request.set_version('2015-01-09')
        request.set_action_name('UpdateDomainRecord')
        request.add_query_param('RecordId', record_id)  # record_item['RecordId']
        request.add_query_param('RR', name)
        request.add_query_param('Type', "A")
        request.add_query_param('Value', ip)

        response = self.client.do_action_with_exception(request)
        json_res = json.loads(response)
        return json_res

    def update(self, name, ip):
        record_id, old_ip = self.check_records(name, ip)
        if record_id:
            self.set_records(record_id=record_id, name=name, ip=ip)
            log.info(f'更新成功 {name} ---> {ip}  （原 {old_ip}）')
            send_email.send(f'更新成功 {name} ---> {ip}  （原 {old_ip}）')
        else:
            pass
            # log.info(f'记录正确,无需修改 {name} ---> {ip}')

    def run(self):
        log.info(f'-----【{self.runner_name}】 开始执行 -----')
        try:
            now_ip = check_ip()
            self.update(self.update_record, now_ip)
        except Exception as e:
            log.error(f'更新失败 {e}')


class CFUpdater(AliUpdater):
    def __init__(self, update_record, email, api_key, zone_id):
        super(CFUpdater, self).__init__(update_record)
        self.runner_name = 'cloudflare'
        self.email = email
        self.api_key = api_key
        self.zone_id = zone_id

    def check_records(self, name, ip):
        headers = {
            'X-Auth-Email': self.email,
            'X-Auth-Key': self.api_key,
            'Content-Type': 'application/json',
        }
        data = {
            'type': 'A',
        }
        response = requests.get(f'https://api.cloudflare.com/client/v4/zones/{self.zone_id}/dns_records',
                                headers=headers, params=data, timeout=20)
        records = response.json()
        for item in records['result']:
            if item['name'] == name and item['type'] == 'A':
                if item['content'] != ip:
                    return item['id'], item['content']
                else:
                    return None, None
        log.info(f'未找到记录 {name}')
        return None

    def set_records(self, record_id, name, ip):
        data = {
            "type": "A",
            "name": name,
            "content": ip,
            "ttl": 600,
            "proxied": False
        }
        headers = {
            'X-Auth-Email': self.email,
            'X-Auth-Key': self.api_key,
            'Content-Type': 'application/json',
        }
        response = requests.put(
            f'https://api.cloudflare.com/client/v4/zones/{self.zone_id}/dns_records/{record_id}',
            headers=headers, json=data, timeout=20)
        return response.json()


if __name__ == '__main__':
    config_path = 'config'

    conf = configparser.ConfigParser()
    conf.read(pathlib.Path().cwd() / config_path)
    record = conf.get('SET', 'update_record')
    check_sleep = conf.getint('SET', 'sleep_time')

    if conf.get('SET', 'client_type') == 'CF':
        cf_email = conf.get('CF', 'email')
        cf_api_key = conf.get('CF', 'api_key')
        cf_zone_id = conf.get('CF', 'zone_id')
        set_client = CFUpdater(record, cf_email, cf_api_key, cf_zone_id)
    else:
        ali_key = conf.get('Ali', 'access_key')
        ali_secret = conf.get('Ali', 'access_key_secret')
        set_client = AliUpdater(record, ali_key, ali_secret)
    while True:
        set_client.run()
        time.sleep(check_sleep)
