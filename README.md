# cliputils

CLIP STUDIO PAINT の clip ファイルを扱うツールです。
現状 SQLite3 データベースを出力するくらいにしか役に立ちません。

ブロックデータの圧縮方法がよくわからないのでこれ以上は期待しないでください。zlib じゃないっぽい。


```sh
# ヘッダ、外部データ、SQLite3データに分割し、test ディレクトリを作成して出力する。
python cliputils.py -v -s -c test.clip

# 外部データのブロックデータを分割して出力
python cliputils.py -v -s --blockdata -c test.clip
```

# clip ファイルメモ

* ``CSFCHUNK``、``CHNK????`` は識別用の文字列で8バイト。
* 識別文字列に続く数値はビッグエンディアン符号なし64-bit整数。
* CHNKExta の外部データやそれに含まれるチャンクとその内部のブロックデータは繰り返し構造になっている。

## 全体の構造

| バイト数 | 内容 | 説明 |
|---|---|---|
| 8 | "CSFCHUNK" | ファイル情報チャンク識別文字列 |
| 8 | 整数 | ファイルサイズ |
| 8 | 整数? | CHNKHead の開始オフセットで24固定? |
| |
| 8 | "CHNKHead" | ヘッダチャンク識別文字列 |
| 8 | 整数 | CHNKHead ヘッダ情報サイズ 40固定? |
| 40? | ヘッダ情報 | 内容は知らない |
| |
| 8 | "CHNKExta" | 外部(external)データチャンク識別文字列 |
| 8 | 整数 | 外部データサイズ |
| 8 | 整数 | extrnlid + id文字列の長さで 40固定？ |
| 40 | 文字列 | 外部データ id 文字列 (extrnlid...)|
| - | データ | ブロックデータ |
| |
| ... | ... | CHNKExta チャンクの繰り返し |
| |
| 8 | "CHNKSQLi" | SQLiteチャンク識別文字列 |
| 8 | 整数 | SQLite3 データベースサイズ |
| - | SQLite3 データ | |
| |
| 8 | "CHNKFoot" | フッタチャンク識別文字列 |
| 8 | 整数 | フッタサイズ フッタの内容は空で0固定？ |

## ブロックデータの構造
* sqlite の Offsets にも BlockData 位置が記録される
* BlockDataBeginChunkのみサイズを表わす4-byte uintが先頭にある。
* 整数はビッグエンディアン32-bit符号なし整数
* BlockDataBeginChunk、データ、BlockDataEndChunkの繰り返しで、次にBlockStatus、最後にBlockCheckSumで終わる。

### BlockDataBeginChunk
| バイト数 | 内容 | 説明 |
|---|---|---|
| 4 | 整数 | BlockDataBeginChunk のサイズ(自身を含む)。 |
| 4 | 整数 | uint 文字列長 |
| - | 可変長2-byte文字列 | 'BlockDataBeginChunk' |
| 4 | 整数 | ブロックデータインデックス |
| 12 | ？ | ？ |
| 4 | 整数 | データがある場合は 1、空の場合は 0。 |
| - | ブロックデータ | |

### BlockDataEndChunk
| バイト数 | 内容 | 説明 |
|---|---|---|
| 4 | 整数 | uint 文字列長 |
| - | 可変長2-byte文字列 | 'BlockDataEndChunk' |

### BlockStatus BlockCheckSum
| バイト数 | 内容 | 説明 |
|---|---|---|
| 4 | 整数 | uint 文字列長 |
| - | 可変長2-byte文字列 | 'BlockStatus' 'BlockCheckSum' |
| 28 | ？ | ？ |

# 注意点など
* SQLiteデータベースのみ改変する場合は ``CSFCHUNK`` のファイルサイズと ``CHNKSQLi`` のデータベースサイズを修正する。
* SQLiteデータベース内にも外部データのオフセット情報が記録されているので、外部データの長さに変更がある場合はSQLiteデータベースの Offsets も修正する。
* レイヤーのサムネイル画像は外部データではなく SQLiteデータベース内にpngファイルとして入っている。
* まだしっかり検証していない。  ハッキリしない部分には ? をつけた。
