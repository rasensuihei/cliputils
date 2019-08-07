# cliputils

CLIP STUDIO PAINT の clip ファイルを扱うツールです。
現状 SQLite3 データベースを出力するくらいにしか役に立ちません。

```sh
# ヘッダ、外部データ、SQLite3データに分割し、test ディレクトリを作成して出力する。
python cliputils.py -v -s -c test.clip

# 外部データのデータブロックを分割して出力
python cliputils.py -v -s --datablocks -c test.clip
```
