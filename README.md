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

run:

```
./upload.py /path/to/ipa
```