import re
import requests

from Pyuu import Pyuu


class Classify:
    def __init__(self, token, client):
        self.pyuu = Pyuu(token)
        if client.config['type'] != 'qBittorrent':
            raise Exception('client is\'t qBittorrent')
        self.client = client
        self.qb = client.client
        self.tag_map = {
            'mv': ['mv', '音乐短片', '演出', 'Music Videos', 'Concert', 'Show LIVE', 'TVMusic'],
            'tv play': ['tv play', '电视剧', 'TV Series', 'TVSeries'],
            'tv shows': ['tv shows', '综艺', 'TVShow'],
            'sport': ['sport', '体育', '運動'],
            'documentaries': ['documentaries', '紀錄', '记录', 'Doc'],
            'game': ['game', '游戏'],
            'software': ['software', '软件'],
            'study': ['study', '学习'],
            'movie': ['movie', '电影', 'Filme'],
            'anime': ['anime', '动漫', 'Animations', 'BDMV', 'DVDISO', 'DVDRip', 'HDTV', 'U2-Rip', 'U2-RBD', 'WEB', 'BDRip', 'LQRip'],
            'ebook': ['ebook', '电子书', 'Books'],
            'music': ['music', '音乐']
        }
        self.tags = list(self.tag_map.keys())

    def strs2tag(self, str):
        if not str:
            return None
        strl = str.lower()
        for k, v in self.tag_map.items():
            for item in v:
                if item.lower() in strl:
                    return k
        return None

    def tag_from_url(self, url, cookie, regx=None):
        if not regx:
            regx = '(基本信息|基本資訊|大小).*(类型|類別).*'
        headers = {
            "Cookie": cookie,
            "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0',
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2"
        }
        str = None
        try:
            print(url)
            resp = requests.get(url=url, headers=headers)
            if resp.content:
                result = re.search(regx, resp.content.decode('utf-8'))
                if result:
                    str = result.group()
        except Exception:
            str = None
        return self.strs2tag(str)

    def classify_by_exists(self):
        torrents = self.qb.torrents_info()
        exists_tag = {torrent.content_path: self.strs2tag(
            torrent.tags) for torrent in torrents if self.strs2tag(torrent.tags)}
        for torrent in torrents:
            if not self.strs2tag(torrent.tags):
                for path in exists_tag.keys():
                    if torrent.content_path.startswith(path):
                        self.qb.torrent_tags.add_tags(
                            tags=exists_tag[path], torrent_hashes=torrent.hash)
                        continue

    def classify(self, sites, user_sites, site_details):
        qbtags = self.qb.torrent_tags.tags
        new_tags = [x for x in self.tags if not qbtags or x not in qbtags]
        if new_tags:
            self.qb.torrent_tags.create_tags(tags=new_tags)

        for info in self.qb.torrents_info():
            if not self.strs2tag(info.tags):
                if 'tracker.open.cd' in info.tracker:
                    self.qb.torrent_tags.add_tags(
                        tags=['music'], torrent_hashes=info.hash)
                if 'greatposterwall.com' in info.tracker:
                    self.qb.torrent_tags.add_tags(
                        tags=['movie'], torrent_hashes=info.hash)
                if 'skyey2.com' in info.tracker or 'pt.skyey.win' in info.tracker:
                    self.qb.torrent_tags.add_tags(
                        tags=['anim'], torrent_hashes=info.hash)
        self.classify_by_exists()

        if 'pter' in site_details and 'cookie' in site_details['pter']:
            for torrent in self.qb.torrents_info():
                if not self.strs2tag(torrent.tags) and 'tracker.pterclub.com' in torrent.tracker and 'comment' in torrent.properties:
                    tag = self.tag_from_url(
                        torrent.properties['comment'], site_details['pter']['cookie'], site_details['pter'].get('classify'))
                    if tag:
                        self.qb.torrent_tags.add_tags(
                            tags=tag, torrent_hashes=torrent.hash)
        self.classify_by_exists()

        if 'hares' in site_details and 'cookie' in site_details['hares']:
            for torrent in self.qb.torrents_info():
                if not self.strs2tag(torrent.tags) and 'club.hares.top' in torrent.tracker:
                    id = re.search('authkey=(\d+)', torrent.tracker).group(1)
                    tag = self.tag_from_url(
                        f'https://club.hares.top/details.php?id={id}', site_details['hares']['cookie'], site_details['hares'].get('classify'))
                    if tag:
                        self.qb.torrent_tags.add_tags(
                            tags=tag, torrent_hashes=torrent.hash)
        self.classify_by_exists()

        torrents = {torrent.hash: torrent for torrent in self.qb.torrents_info(
        ) if not self.strs2tag(torrent.tags)}
        result = self.pyuu.query_site(list(torrents.keys()))
        result = self.pyuu.get_urls([{'torrent': result}], sites, user_sites)[
            0]['torrent']
        for site, details in site_details.items():
            is_set = False
            for info in result:
                if 'info_hash' in info and info['site'] == site and not self.strs2tag(torrents[info['info_hash']].tags):
                    tag = self.tag_from_url(
                        info['details'], details['cookie'], details.get('classify'))
                    if tag:
                        self.qb.torrent_tags.add_tags(
                            tags=tag, torrent_hashes=info['info_hash'])
                        is_set = True
            if is_set:
                self.classify_by_exists()
