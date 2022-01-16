import qbittorrentapi
import transmissionrpc
import re
import os

from utils import hash_torrent


class Client:
    def __init__(self, config):
        self.config = config
        if config['type'] == 'qBittorrent':
            self.client = qbittorrentapi.Client(
                host=config['host'], username=config['username'], password=config['password'])
            try:
                self.client.auth_log_in()
            except qbittorrentapi.LoginFailed as e:
                print(e)
        elif config['type'] == 'transmission':
            arr = re.search(r'http[s]*://(.*?)/.*',
                            config['host'] + '/').group(1).split(':')
            try:
                self.client = transmissionrpc.Client(arr[0], arr[1] if len(
                    arr) > 1 else '80', user=config['username'], password=config['password'])
            except transmissionrpc.error.TransmissionError:
                print(
                    "ERROR: Couldn't connect to Transmission. Check rpc configuration.")

    # qb tr返回结构不一样，未封装
    def torrents_info(self, torrent_hashes=[]):
        if self.config['type'] == 'qBittorrent':
            result = self.client.torrents_info(
                torrent_hashes='|'.join(torrent_hashes))
            return [{
                'hash': x.hash,
                'name': x.name,
                'save_path': x.save_path,
                'total_size': x.total_size,
                'progress': x.progress,
                'status': x.state
            } for x in result]
        elif self.config['type'] == 'transmission':
            result = [x for x in self.client.get_torrents() if len(
                torrent_hashes) == 0 or x.hashString in torrent_hashes]
            return [{
                'hash': x.hashString,
                'name': x.name,
                'save_path': x.downloadDir,
                'total_size': x.totalSize,
                'progress': x.progress / 100.0,
                'status': x.status
            } for x in result]

    def torrents_add_url(self, urls):
        if self.config['type'] == 'qBittorrent':
            self.client.torrents_add(urls='\n'.join(
                urls), save_path=self.config['downloadsDir'], is_skip_checking=False, is_paused=True)
        elif self.config['type'] == 'transmission':
            for url in urls:
                self.client.add_uri(
                    url, download_dir=self.config['downloadsDir'], paused=True)

    def torrents_add_from_dir(self, dir, save_path=None):
        for root, dirs, files in os.walk(dir):
            for filename in files:
                if filename.endswith('.torrent'):
                    self.torrents_add_file(torrent_file=os.path.join(
                        root, filename), save_path=save_path)

    def torrents_add_file(self, torrent_file, rename=None, save_path=None, is_paused=True, is_skip_checking=False):
        hashcode = hash_torrent(torrent_file)
        if hashcode:
            if not self.torrents_info([hashcode]):
                if self.config['type'] == 'qBittorrent':
                    result = self.client.torrents_add(
                        torrent_files=torrent_file, rename=rename, save_path=save_path if save_path else self.config['downloadsDir'], is_paused=is_paused, is_skip_checking=is_skip_checking)
                    return f'{result} -> qb: {torrent_file}'
                elif self.config['type'] == 'transmission':
                    if 'file://' not in torrent_file:
                        torrent_file = 'file://' + torrent_file
                    result = self.client.add_torrent(
                        torrent_file, download_dir=save_path if save_path else self.config['downloadsDir'], paused=True)
                    return f'{result} -> tr: {torrent_file}'
        else:
            print('error' + torrent_file)
        return None

    def torrents_delete(self, delete_files=False, torrent_hashes=None):
        if self.config['type'] == 'qBittorrent':
            self.client.torrents_delete(
                delete_files=delete_files, torrent_hashes=torrent_hashes)

    def start(self):
        if self.config['type'] == 'transmission':
            ids = [x.id for x in self.client.get_torrents(
            ) if 'F:\Downloads' not in x.downloadDir and x.progress == 100 and x.status == 'stopped']
            if ids:
                self.client.start_torrent(ids)
