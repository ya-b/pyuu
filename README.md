# 介绍
只支持qbittorrent。并且和qbittorrent安装到同一主机

快速hash校验： 每个文件取8~10个piece进行校验（和qbittorrent安装到同一主机，并且挂载点要一样（会从qb获取文件位置），不然读取不到文件）

辅种：客户端先调用iyuu服务端接口获取辅种信息->下载种子->每个文件取8~10个piece进行校验（其实也不安全）->跳检添加到qb
# 使用
###0.安装依赖

先安装python, pip，之后运行：
```
pip install -r requirements.txt
```
###1.配置

配置好[IYUUPlus](https://github.com/ledccn/IYUUPlus)，复制iyuuplus/db目录下[clients.json iyuu.json sites.json user_sites.json]到此项目db下

###2.运行

1)辅种
```
python index.py --run autoseed --client localQB
```
2)校验种子文件（文件夹）并辅种
```
python index.py --run autoseed --client localQB  --torrent /torrentdir --savepath /downloaddir
```
3)校验种子文件（文件夹）
```
python index.py --run verify --torrent /BT_BACKUP/xxx.torrent --savepath /downloaddir
```

# 感谢
- [ledccn/IYUUPlus](https://github.com/ledccn/IYUUPlus)
- [ChisBread/transmission_skip_patch](https://github.com/ChisBread/transmission_skip_patch)
- [stewrutledge/makeTorrent](https://github.com/stewrutledge/makeTorrent)