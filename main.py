import os
import random
import time
import requests
import logging as log
import json
import sys

log.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    level=log.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

root_path = os.path.dirname(os.path.realpath(sys.argv[0]))  # 获取本文件所在目录
# os.chdir(os.path.dirname(__file__))
fileList = os.listdir(root_path)

config = """\
{
    "user_id": "",
    "clazz_course_id": "",
    "total_time": 60,
    "cid_list": [
        ""
    ],
    "token": "",
    "cookie": ""
}"""

if 'config.json' not in fileList:
    log.info('未发现配置文件,即将创建配置文件')
    with open(f'{root_path}{os.path.sep}config.json', 'w', encoding='utf8') as f:
        f.write(config)
    log.info('配置文件创建完成,请到当前文件夹下的config.py进行配置后重启程序,程序将在5秒后退出')
    time.sleep(5)
    exit()
else:
    with open(f'{root_path}{os.path.sep}config.json', 'r', encoding='utf8') as f:
        config = json.loads(f.read())
    if config['user_id'] == '' or config['clazz_course_id'] == '' or config['total_time'] == '' or config['cid_list'] == [] or config['token'] == '' or config['cookie'] == '':
        log.error('请将配置文件填写完成,程序将在5秒后退出')
        time.sleep(5)
        exit()

class YunClass(object):
    def __init__(self, user_id, clazz_course_id, cid, token, cookie):
        self.user_id = user_id
        self.clazz_course_id = self.cc_id = clazz_course_id
        self.act_id = self.id = cid
        self.token = token
        self.cookie = cookie
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language':'zh-CN,zh;q=0.9,en-CN;q=0.8,en;q=0.7,ja-CN;q=0.6,ja;q=0.5',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': self.cookie,
            'Host': 'www.mosoteach.cn',
            'Origin': 'https://www.mosoteach.cn',
            'Pragma': 'no-cache',
            'Referer': 'https://www.mosoteach.cn/web/index.php?c=interaction_quiz&m=reply&clazz_course_id={}&id={}&order_item=group'.format(self.clazz_course_id,self.id),
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': "Windows",
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'X-token': self.token
        }

        self.resultDict = {}
        self.submitList = []

    # 获取答案解析
    def person_result(self):
        log.info('开始获取答案')
        url = 'https://www.mosoteach.cn/web/index.php?c=interaction_quiz&m=person_result'
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'cc_id': self.cc_id,
        }
        res = requests.post(url, data=data,headers=self.headers)
        log.info(res.status_code)
        return res

    # 获取作答题目
    def start_quiz(self):
        log.info('开始获取作答题目')
        url = 'https://www.mosoteach.cn/web/index.php?c=interaction_quiz&m=start_quiz'
        data = {
            'act_id':self.act_id,
            'cc_id': self.cc_id
        }
        r = requests.post(url,data=data,headers=self.headers).json()
        quiz_topic_list = r['quiz_topic_list']
        self.start_enter_id = r['id']
        log.info('总共有{}道题需作答'.format(len(quiz_topic_list)))

        self.submitdata = {
            'start_enter_id': self.start_enter_id,
            "id": self.id,
            "clazz_course_id": self.clazz_course_id,
        }
        for n, item in enumerate(quiz_topic_list):
            # key = urllib.parse.quote('data[{}][topicId]'.format(n))
            key = 'data[{}][topicId]'.format(n)
            value = item['topic_id']
            self.submitdata[key] = value

            # key = urllib.parse.quote('data[{}][type]'.format(n))
            key = 'data[{}][type]'.format(n)
            value = item['type']
            self.submitdata[key] = value

            # 判断题要处理下
            if item['type'] == 'TF':
                key = 'data[{}][tfAnswer]'.format(n)
                # dict.get用于交白卷
                value = self.resultDict.get(item['topic_id'], "")
                self.submitdata[key] = value
                continue
            
            # 单选多选答案均为列表, 如果交白卷将不存在下面的data[n][answers][m]参数
            answers = self.resultDict.get(item['topic_id'], [])

            for m, answer in enumerate(answers):
                # key = urllib.parse.quote('data[{}][answers][{}]'.format(n, m))
                key = 'data[{}][answers][{}]'.format(n, m)
                value = answer
                self.submitdata[key] = value
        # log.info(self.submitdata)
        log.info('作答完成')

    # 提交答案
    def save_answer(self):
        url = 'https://www.mosoteach.cn/web/index.php?c=interaction_quiz&m=save_answer'
        # log.info(self.submitdata)
        r = requests.post(url,data=self.submitdata,headers=self.headers)
        jsx = r.json()
        try:
            # log.info(r.text)
            log.info('本次成绩: {}, 最好成绩: {}'.format(jsx['score']['thisTimeScore'], jsx['score']['bestScore']))
        except:
            log.error(r, exc_info=True)

    # 获取排名
    def get_quiz_ranking(self):
        url = 'https://www.mosoteach.cn/web/index.php?c=interaction_quiz&m=get_quiz_ranking'
        data = {
            'id': self.id,
            'ccId': self.cc_id
        }
        r = requests.post(url,data=data,headers=self.headers).json()
        
        activity = r['activity']
        members = activity['members']
        for member in members:
            if member['user_id'] == self.user_id:
                try:
                    log.info('当前排名: {}'.format(member['ranking']))
                    log.info('分数: {}/{}'.format(member['score'], activity['topic_total_score']))
                    break
                except:
                    log.error(r, exc_info=True)
                    
if __name__ == '__main__':
    try:
        sleep_time = int(config['total_time'])
    except ValueError:
        log.error('时间需要为纯数字哦,暂时为你设置8分钟咯')
        sleep_time = 480
    for cid in config['cid_list']:
        yc = YunClass(config['user_id'], config['clazz_course_id'], cid, config['token'], config['cookie'])
        res = yc.person_result()
        try:
            jsx=res.json()
            if jsx['result_code'] == 0:
                topics = jsx['activity']['topics']
            # 这个情况是没公布答案的, 需要先跑一遍交卷流程
            elif jsx['result_code'] == "err.act.notViewResult":
                log.info(jsx['result_msg'])
                log.info('准备进行作答以获取答案')
                yc.start_quiz()
                rst = random.randint(5, 10)
                log.info(f'将在 {rst}s 后交卷')
                time.sleep(rst)
                yc.save_answer()

                log.info('再次获取答案')
                res = yc.person_result()
                jsx=res.json()
                if jsx['result_code'] != 0:
                    log.error(jsx['result_msg'])
                    log.info('跳过该题')
                    continue
                topics = jsx['activity']['topics']
        except:
            log.error('获取答案失败, 跳过该题', jsx, exc_info=True)
            continue
        for topic in topics:
            # 判断题
            if topic['type'] == 'TF':
                yc.resultDict[topic['topic_id']] = topic['tf_answer']
            # 单选多选题
            else:
                yc.resultDict[topic['topic_id']] = topic['answers']
        log.info('答案获取完成,总共有{}道题被记录'.format(len(yc.resultDict)))
        yc.start_quiz()
        asleep_time = sleep_time + random.randint(1, 60)
        log.info('将在{}s后交卷'.format(asleep_time+1))
        time.sleep(asleep_time)
        yc.save_answer()
        yc.get_quiz_ranking()
        del yc
    input('按任意键继续...')
