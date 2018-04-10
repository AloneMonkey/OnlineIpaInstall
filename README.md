# OnlineIpaInstall
Fast upload ipa online to install

# Usage

Set config in `config/user.config` file

```
{
    //七牛的ak和sk
	"access_key" : "xxxxx",   
	"secret_key" : "xxxxx",
    //七牛的bucket名字和链接
	"bucket_name" : "xxxxx",
	"bucket_url" : "xxxxx",
    //当前repo的地址
	"repo_url" : "https://github.com/AloneMonkey/OnlineIpaInstall/git/raw/master/"
}
```

```
➜  OnlineIpaInstall git:(master) ✗ ./upload.py ipas/Target.ipa
[NewT66y.ipa] uploading......
[NewT66y-AppIcon60x60@2x.png] uploading......
[NewT66y.html] uploading......
Please push local branch to remote, Then open http://o9slcszsf.bkt.clouddn.com/NewT66y.html install
➜  OnlineIpaInstall git:(master) ✗ git add .
➜  OnlineIpaInstall git:(master) ✗ git commit -m "[new] add t66y"
[master 917abb5] [new] add t66y
 7 files changed, 130 insertions(+), 27 deletions(-)
 create mode 100644 htmls/NewT66y.html
 create mode 100644 icons/NewT66y/Payload/caoliu.app/AppIcon60x60@2x.png
 create mode 100644 ipas/Target.ipa
 create mode 100644 plists/NewT66y.plist
➜  OnlineIpaInstall git:(master) git push origin master
Counting objects: 16, done.
Delta compression using up to 4 threads.
Compressing objects: 100% (12/12), done.
Writing objects: 100% (16/16), 550.63 KiB | 22.02 MiB/s, done.
Total 16 (delta 1), reused 0 (delta 0)
remote: Resolving deltas: 100% (1/1), completed with 1 local object.
To https://github.com/AloneMonkey/OnlineIpaInstall.git
   5e1f254..917abb5  master -> master
➜  OnlineIpaInstall git:(master) open http://o9slcszsf.bkt.clouddn.com/NewT66y.html
```