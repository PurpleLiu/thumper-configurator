# Thumper 選配器

BlackCrow Thumper 1:8 CJ7 攀爬車（[Printables 323433](https://www.printables.com/model/323433)）的非官方選配整理網站：點選配置 → 檢查相容性 → 產生列印清單和採購清單。

- 純靜態網站（`site/`），不需要後端，也不需要建置步驟。
- **不放 STL 檔**，作者不允許轉載；每個零件都連回 Printables 下載。
- 照片取自作者的 Printables 頁面，版權屬於原作者 BlackCrow 和各配件作者。

## 資料夾

| 路徑 | 內容 |
|---|---|
| `site/` | 網站本體（index.html、style.css、app.js、data.js、img/）。Cloudflare 就發佈這一層 |
| `tools/catalog_def.py` | 手寫的選項、規則、採購品項、預設配置，**改規則改這裡** |
| `tools/assembly_def.py` | 組裝階段、官方影片、齒比資料 |
| `tools/build.py` | 把 catalog_def 和 Printables 資料合成 `site/data.js`，並下載圖片 |
| `data/raw/` | 從 Printables API 抓下來的頁面資料（不進 git） |
| `規則清單.md` | 規則草稿，給人看的版本 |

## 改完資料後重建

```bash
cd tools
python build.py            # 重建 data.js 並更新圖片
python build.py --no-img   # 只重建 data.js
```

`build.py` 會讀上一層專案的 `_工具腳本/`（零件中文名、我們的材質建議），所以要在完整專案資料夾裡執行。

## 本機預覽

```bash
python -m http.server 8765 --directory site
```

打開 http://localhost:8765

## 部署（GitHub + Cloudflare Workers）

網址：https://thumper-cfg.purpleliu.com/

Cloudflare Workers 連 GitHub 自動建置，設定在 `wrangler.jsonc`（只發佈 `site/`）：
- 組建命令：留空
- 部署命令：`npx wrangler deploy`

之後只要 `git push`，Cloudflare 就會自動更新網站（約 1–3 分鐘）。
