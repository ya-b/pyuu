import os
import requests
import time
import hashlib
import json

from utils import rmfile, hash_torrent
from verify import verify
from urllib.parse import unquote


class Pyuu:
    def __init__(self, token):
        self.apis = {
            'App.Api.Hash': 'http://api.iyuu.cn/index.php?s=App.Api.Hash',  # 查询辅种
            'App.Api.GetSign': 'http://api.iyuu.cn/index.php?s=App.Api.GetSign',
            'App.Api.GetTorrentInfo': 'http://api.iyuu.cn/index.php?s=App.Api.GetTorrentInfo'
        }
        self.token = token
        self.sign_map = {
            'pthome': {},
            'hdhome': {},
            'hdai': {},
            'ourbits': {},
            'hddolby': {},
            'chdbits': {},
        }
        self.cached = './db/cached.txt'

    def request_hashs(self, *clients):
        filter = []
        hashs = []
        for client in clients:
            resp = client.torrents_info()
            for item in resp:
                if item['progress'] < 1:
                    continue
                k = f"{item['save_path']}/{item['name']}@{item['total_size']}"
                # if k in filter:
                # continue
                filter.append(k)
                hashs.append(item['hash'])
        return hashs

    def filter(self, datas, *clients):
        exists = []
        result = []
        for client in clients:
            exists.extend([x['hash'] for x in client.torrents_info()])
        for data in datas:
            temp = []
            for info in data['torrent']:
                if info['info_hash'] not in exists:
                    temp.append(info)
            if (len(temp) > 0):
                result.append({'hash': data['hash'], 'torrent': temp})
        return result

    def filter_site(self, datas, site_ids):
        result = []
        for data in datas:
            temp = []
            for info in data['torrent']:
                if info['sid'] in site_ids:
                    temp.append(info)
            if (len(temp) > 0):
                result.append({'hash': data['hash'], 'torrent': temp})
        return result

    def split_list(self, list, length):
        return [list[i:i + length] for i in range(0, len(list), length)]

    def load_cache(self):
        ch = []
        try:
            with open(self.cached, 'r', encoding='utf-8') as file:
                ch = file.readlines()
        except IOError:
            print("Error: 没有找到文件或读取文件失败")
        return ch

    def append_cache(self, line):
        try:
            with open(self.cached, 'a', encoding='utf-8') as file:
                file.writelines([line])
        except IOError:
            print("Error: 没有找到文件或读取文件失败")

    def filter_cached(self, datas):
        ex = self.load_cache()
        result = []
        for data in datas:
            temp = []
            for info in data['torrent']:
                key = f"{info['sid']}@{info['torrent_id']}\n"
                if key not in ex:
                    temp.append(info)
                    ex.append(key)
            if (len(temp) > 0):
                result.append({'hash': data['hash'], 'torrent': temp})
        return result

    def query(self, hashs):
        arr = []
        hashs.sort()
        progress = 0
        for torrent_hashs in self.split_list(hashs, 500):
            hash = json.dumps(torrent_hashs, separators=(',', ':'))
            data = {
                'sign': self.token,
                'version': 'pyuuV0.0.1',
                'timestamp': int(time.time()),
                'hash': hash,
                'sha1': hashlib.sha1(hash.encode("utf-8")).hexdigest()
            }
            resp = requests.post(self.apis['App.Api.Hash'], data=data)
            arr.extend(resp.json()['data'])
            progress += len(torrent_hashs)
            print(f'请求服务器: {progress} / {len(hashs)}')
        return arr

    def query_site(self, hashs):
        arr = []
        hashs.sort()
        progress = 0
        for torrent_hashs in self.split_list(hashs, 100):
            hash = json.dumps(torrent_hashs, separators=(',', ':'))
            data = {
                'sign': self.token,
                'hash': hash
            }
            resp = requests.post(
                self.apis['App.Api.GetTorrentInfo'], data=data)
            arr.extend(resp.json()['data'])
            progress += len(torrent_hashs)
            print(f'请求服务器: {progress} / {len(hashs)}')
        return arr

    def get_sign(self, site, uid):
        if site not in self.sign_map:
            return ''
        if 'time' not in self.sign_map[site] or self.sign_map[site]['time'] + self.sign_map[site]['expire'] < int(time.time()):
            data = {
                'sign': self.token,
                'version': 'pyuuV0.0.1',
                'site': site,
                'uid': uid
            }
            resp = requests.get(self.apis['App.Api.GetSign'], params=data)
            if resp.status_code == 200:
                self.sign_map[site] = resp.json()['data']
        return self.sign_map[site]['signString'] if 'signString' in self.sign_map[site] else ''

    def get_urls(self, datas, sites, user_sites):
        site_map = {}
        for k, v in sites.items():
            site_map[v['id']] = v
        for data in datas:
            for info in data['torrent']:
                if 'sid' not in info:
                    continue
                site = site_map[info['sid']]
                details = (site['details'] if 'details' in site else 'details.php?id={}').format(
                    info['torrent_id'])
                info['details'] = f"https://{site['base_url']}/{details}"
                site_conf = user_sites[site['site']]
                page = site['download_page'].format(info['torrent_id'], passkey=site_conf.get('passkey'), uid=site_conf.get('id'), hash=site_conf.get(
                    'downHash'), cuhash=site_conf.get('downHash'), authkey=site_conf.get('authkey'), torrent_pass=site_conf.get('torrent_pass'))
                page += f"&https={site_conf.get('is_https', 1)}"
                sign = self.get_sign(site['site'], site_conf.get('id'))
                info['url'] = f"https://{site['base_url']}/{page}" + \
                    (f'&{sign}' if sign else '')
                info['site'] = site['site']
        return datas

    def dl_torrents(self, url, dir=os.path.join(os.path.expanduser('~'), 'Downloads')):
        if not url or 'skyey2.com' in url or 'skyeysnow.com' in url:
            return None
        try:
            print('dl ' + url)
            resp = requests.get(url, allow_redirects=True, timeout=5)
            if 'application/x-bittorrent' not in resp.headers['content-type']:
                return None
            filename = url
            if 'Content-Disposition' in resp.headers and resp.headers['Content-Disposition']:
                disposition_split = resp.headers['Content-Disposition'].split(
                    ';')
                if len(disposition_split) > 1:
                    if disposition_split[1].strip().lower().startswith('filename='):
                        file_name = disposition_split[1].split('=')
                        if len(file_name) > 1:
                            filename = unquote(file_name[1]).replace('"', '')
            if not os.path.exists(dir):
                os.makedirs(dir)
            if not filename.endswith('.torrent'):
                filename = filename + '.torrent'
            path = os.path.join(dir, f'{time.time()}{filename}')
            with open(path, "wb") as fl:
                fl.write(resp.content)
            return path
        except:
            return None

    def auto_reseed(self, client_from, client_to, sites, user_sites, accept_site_ids=None):
        temp_dir = './temp/'
        rmfile(temp_dir)
        if not accept_site_ids:
            accept_site_ids = [v['id'] for k, v in sites.items()]
        hashs = []
        hashs = self.request_hashs(client_from)
        result = self.query(hashs)
        result = self.filter(result, client_to)
        result = self.filter_site(result, accept_site_ids)
        result = self.filter_cached(result)
        result = self.get_urls(result, sites, user_sites)
        froms = {x['hash']: x for x in client_from.torrents_info()}
        t_files = []
        limit_count = {}
        for data in result:
            limit_sleep = 0
            for info in data['torrent']:
                site_conf = user_sites[info['site']]
                if 'limitRule' in site_conf:
                    if 'sleep' in site_conf['limitRule']:
                        limit_sleep = max(
                            int(site_conf['limitRule']['sleep']), limit_sleep)
                    if 'count' in site_conf['limitRule'] and int(site_conf['limitRule']['count']) < limit_count.get(info['sid'], 0):
                        continue
                f = self.dl_torrents(info['url'], temp_dir)
                if f:
                    t_files.append((f, froms[data['hash']]['save_path']))
                    limit_count.setdefault(
                        info['sid'], limit_count.get(info['sid'], 0) + 1)
                else:
                    print(f"download error: {info['details']}")
                self.append_cache(f"{info['sid']}@{info['torrent_id']}\n")
            if limit_sleep:
                time.sleep(limit_sleep)
        for t_file, save_path in t_files:
            try:
                if verify.verify_torrent(t_file, save_path):
                    client_to.torrents_add_file(
                        t_file, save_path=save_path, is_paused=True, is_skip_checking=True)
                else:
                    print(f'校验失败: {t_file}')
            except:
                print(f"添加种子失败: {t_file}")

    def auto_reseed_dir(self, files, save_path, client):
        hashs = [x['hash'] for x in client.torrents_info()]
        for torrent in files:
            if hash_torrent(torrent) in hashs:
                continue
            if verify.verify_torrent(torrent, save_path):
                client.torrents_add_file(torrent, save_path=save_path, is_paused=True, is_skip_checking=True)
            else:
                print('校验失败:' + torrent)