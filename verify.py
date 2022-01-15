import bencode
import hashlib
import os
import math
import hmac
from tqdm import tqdm


class Verify:
    def __init__(self):
        self.SHA1_LEN = 20
        self.cache = {}

    def verify_piece(self, data, piece):
        return hmac.compare_digest(piece, hashlib.sha1(data).digest())

    def verify(self, files, piece_length, pieces):
        check_num = 8
        pbar = tqdm(total=len(pieces) / 20)
        piece_idx = 0
        prev = bytes()
        for file, length in files:
            if not os.path.exists(file):
                pbar.close()
                return False
            file_size = os.stat(file).st_size
            if file_size != length:
                pbar.close()
                return False
            piece_num = math.ceil(file_size / piece_length)
            interval = max(int(piece_num / check_num), 1)
            with open(file, 'rb') as f:
                start = - len(prev)
                while start < file_size:
                    if len(prev) > 0:
                        piece_data = prev + f.read(piece_length - len(prev))
                        prev = bytes()
                    else:
                        f.seek(start)
                        piece_data = f.read(piece_length)
                    step = interval if start + interval * piece_length < file_size - 3 * piece_length else 1
                    start += piece_length * step
                    if len(piece_data) >= piece_length:
                        if not self.verify_piece(piece_data, pieces[piece_idx * self.SHA1_LEN: (piece_idx + 1) * self.SHA1_LEN]):
                            pbar.close()
                            return False
                        piece_idx += step
                        pbar.update(step)
                    else:
                        prev = piece_data
        pbar.close()
        return True

    def verify_torrent(self, torrent, output):
        print(f'verifing:{torrent}')
        with open(torrent, 'rb') as f:
            info = bencode.bdecode(f.read())['info']
        if info['pieces'] in self.cache:
            return self.cache[info['pieces']]
        path = os.path.join(output, info['name'])
        files = []
        if 'files' not in info:
            files.append((path, info['length']))
        else:
            for i in range(len(info['files'])):
                fl_info = info['files'][i]
                file = os.path.join(path, *fl_info['path'])
                files.append((file, fl_info['length']))
        self.cache[info['pieces']] = self.verify(files, info['piece length'], info['pieces'])
        return self.cache[info['pieces']]
