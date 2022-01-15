from argparse import ArgumentParser
from Pyuu import Pyuu
from classify import Classify
from client import Client
from utils import load_file
from verify import Verify

to_sites = []
client_cache = {}

token = load_file('./db/iyuu.json')['iyuu.cn']
sites = load_file('./db/sites.json')
user_sites = load_file('./db/user_sites.json')
site_details = load_file('./db/site_details.json', {})
clients_conf = load_file('./db/clients.json')
if to_sites:
    user_sites = {k: v for k, v in user_sites.items() if k in to_sites}
temp = {}
for k, v in sites.items():
    if k in user_sites and (not to_sites or k in to_sites):
        if k in site_details:
            if 'details' in site_details[k]:
                v['details'] = site_details[k]['details']
        temp[k] = v
sites = temp

def get_client(name):
    if name not in client_cache:
        for conf in clients_conf.values():
            if not name:
                client_cache[name] = Client(conf)
                break
            if conf['name'] == name:
                client_cache[name] = Client(conf)
                break
    if name not in client_cache:
        raise Exception('client not exists')
    return client_cache[name]

def autoseed(client_name):
    pyuu = Pyuu(token)
    pyuu.auto_reseed(get_client(client_name), get_client(client_name), sites, user_sites)

def autotag(client_name):
    clfy = Classify(token, get_client(client_name))
    clfy.classify(sites, user_sites, site_details)

if __name__ == "__main__":
    argparser = ArgumentParser(description='pyuu')
    argparser.add_argument("--run", "-r", choices=['autoseed', 'autotag', 'verify'])
    argparser.add_argument("--client", "-c", help="客户端名称")
    argparser.add_argument("--torrent", "-t", help="verify：种子文件")
    argparser.add_argument("--savepath", "-s", help="verify：保存目录")
    results = argparser.parse_args()

    print('START')
    if results.run == 'autoseed':
        pyuu = Pyuu(token)
        pyuu.auto_reseed(get_client(results.client), get_client(results.client), sites, user_sites)
        # get_client(results.client_to).tr_recover('./temp')
    if results.run == 'autotag':
        clfy = Classify(token, get_client(results.client))
        clfy.classify(sites, user_sites, site_details)
    if results.run == 'verify':
        Verify().verify_torrent(results.torrent, results.savepath)
    print('END')
