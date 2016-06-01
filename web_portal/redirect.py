'''
Author: Guanyu Gao
Email: guanyugao@gmail.com
Description:
Web protal for submitting transcoding task and querying task progress.
The users can access via RESTful API.
'''

import os
import web
import json
import subprocess
from random import Random

urls = (
    '/', 'home',
    '/get_progress',         'get_progress',
    '/rest_submit_file',     'rest_submit_file',
    '/rest_submit_url',      'rest_submit_url',
    '/rest_get_progress',    'rest_get_progress',
    '/get_result',           'get_result',
    '/get_tgt_files',        'get_tgt_files'
    )

work_path = '/data/4/tmp/'
cln_path  = '/var/www/Morph/cli_submit.py'
qry_path  = '/var/www/Morph/cli_query.py'

'''
generate a random key for the task
'''
def gen_key(randomlength = 8):
    str     = ''
    chars   = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    length  = len(chars) - 1
    random  = Random()
    for i in range(randomlength):
        str += chars[random.randint(0, length)]
    return str

'''
start a transcoding operation
'''
def start_transcoding(file_name, key, res):
    cmd = "python " + cln_path + " -l " + file_name + " -t " + key + " -s " + res
    web.debug(cmd)
    os.chdir('/var/www/Morph/')
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = p.communicate()
    ret = p.returncode
    web.debug(stdout)
    web.debug(stderr)
    return ret

'''
save the uploaded video file
'''
def save_file(upload_file, key):
    file_name = upload_file['video_file'].filename
    _, ext = os.path.splitext(file_name)
    file_name = os.path.join(work_path, key + ext)
    f = open(file_name, "wb")
    f.write(upload_file['video_file'].value)
    f.close()
    return file_name

'''
The restful API interface for submitting a video file
'''
class rest_submit_file:
    def POST(self):
        upload_file = web.input(video_file = {}, target_resolution = None, priority = None)
        key = gen_key()
        res = upload_file['target_resolution']
        file_name = save_file(upload_file, key)
        ret = start_transcoding(file_name, key, res)
        ret = json.dumps({"key": key, "ret": ret})
        return ret

class rest_submit_url:
    def POST(self):
        new_task = web.input(url = None, target_resolution = None, priority = None)
        url = new_task['url']
        res = new_task['target_resolution']

        key = gen_key()
        cmd = "python " + cln_path + " -u " + url + " -t " + key + " -s " + res
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = p.communicate()
        ret = p.returncode
        ret = json.dumps({"key": key, "ret": 0})

        return ret


class rest_get_progress:
    def POST(self):
        s = web.input(key = None)
        os.chdir('/var/www/Morph/')
        cmd = "python " + qry_path + " -k " + str(s.key)
        web.debug(cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = p.communicate()
        prg = p.returncode
        ret = json.dumps({"key": str(s.key), "ret": str(prg)})
        return ret

'''
Get the transcoding progress
'''
class get_progress:
    def POST(self):
        data = web.data()
        web.debug(data)
        (_, key) = data.split('=')
        os.chdir('/var/www/Morph/')
        cmd = "python " + qry_path + " -k " + key
        web.debug(cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = p.communicate()
        prg = p.returncode
        web.debug(stdout)
        return str(prg)

'''
The home page for the Demo
'''
class home:
    def GET(self):
        with open('/var/www/Morph/web_portal/home.html', 'r') as homepage:
            data = homepage.read()
            return data

    def POST(self):
        x = web.input(video_file={}, p_240=None, p_360=None,\
                p_480=None, p_720=None)
        key = gen_key()
        file_name = save_file(x, key) 
        res = ''
        if x['p_240'] == '240':
            res += '426x240 '
        if x['p_360'] == '360':
            res += '640x360 '
        if x['p_480'] == '480':
            res += '854x480 '
        if x['p_720'] == '720':
            res += '1280x720 '
        ret = start_transcoding(file_name, key, res)
        state = ''
        if ret == 0:
            state = 'successful'
        else:
            state = 'failed'
        other_page = "get_result?" + "key=" + key + "&" + \
                     "res=" + res + '&' + \
                     "state=" + state
        raise web.seeother(other_page)

class get_result:
    def GET(self):
        data = web.input(res=None, state=None, key=None)
        web.debug(data)
        render = web.template.frender('/var/www/Morph/web_portal/result.html')
        return render(data.key, data.state, data.res) 

class get_tgt_files:
    def POST(self):
        data = web.data()
        web.debug(data)
        (_, key) = data.split('=')
        os.chdir('/var/www/Morph/')
        cmd = "python " + qry_path + " -k " + key
        web.debug(cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = p.communicate()
        web.debug(stdout)
        prg = p.returncode
        if prg == 100:
            f = stdout.split('\'')
            ret = 'Transcoded video files:' + '<br>'
            for i in f:
                if i.find('Morph') < 0:
                    continue
                ret += i.replace('/var/www', 'http://155.69.146.43') + '<br>'
            web.debug(ret)
            return ret
        if prg != 100:
            return ""

'''
the main program for wsgi
'''
application = web.application(urls, globals()).wsgifunc()


