# pigeonium_v0_server
pigeonium_v0のサーバー動かすやつ  
config.pyを適切に設定して実行(AdminPrivateKey,superiorAddress,SwapWalletPrivateKeyをデフォルト設定で放置しないこと)

## Apacheを用いて公開する
ドメインとかの都合で色々やりたい人向け

Apacheのモジュールを有効化
```
a2enmod proxy proxy_html proxy_http
```
設定ファイルの編集
```
<VirtualHost *:80>
    ServerName example.com
    ProxyRequests Off
    ProxyPass / http://localhost:14513/
    ProxyPassReverse / http://localhost:14513/
</VirtualHost>
```
