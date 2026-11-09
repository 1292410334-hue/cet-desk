# 四六级自习室

一本练习册。不用登录、不必联网，纸色和宋体，没有卡片墙和渐变。

打开就是封面：写上名字、填借阅卡、翻目次。六页：

| 页 | 做什么 |
| --- | --- |
| 01 封面 | 练习册封面 + 借阅卡（每天记了几个词）+ 目次 |
| 02 单词 | 四级 4190 / 六级 3991 词；核心词 四级 1554、六级 2298，一键只看核心。音标、例句、短语、同近义，翻卡、自测、错词本 |
| 03 真题 | 2013—2026 共 55 个考次、455 份文件；2026.06 四级三套 + 六级三套（含三份解析）已存本地，点「本」在站内直接读 |
| 04 听力 | 22 段原声，倍速 / 前后 15 秒 / 循环 / 记住听到哪一秒 |
| 05 练习 | 词义、音标、短语搭配、拼写四种题，从真实词条现出，当场判分，错词进错词本 |
| 06 作文 | 词数、段落、连接词、重复词、拼写、句长、标点 —— 规则批注，不是 AI 聊天 |

记录只写在浏览器 localStorage 里，没有账号，没有埋点，作文不上传。

## 部署（发给别人、手机上打开）

整套站是纯静态文件，没有后端、没有数据库、不需要装任何东西。三种发法：

| 方式 | 要不要账号 | 以后怎么改 |
| --- | --- | --- |
| 共享文件夹 / 网盘 | 不用 | 改完重新压缩发一次 |
| **GitHub Pages**（推荐） | 免费 GitHub 账号 | 改完跑 `tools/deploy.ps1`，一分钟生效 |
| Netlify Drop / Cloudflare Pages | 免费账号 | 改完把文件夹重新拖一次 |

**GitHub Pages（要长期用、随时改，用这个）**

1. 在 GitHub 建一个空仓库（不要勾 README）
2. 在本文件夹跑：

```
powershell -ExecutionPolicy Bypass -File tools/deploy.ps1 -Repo https://github.com/你的名字/仓库.git
```

3. 网页上仓库 Settings → Pages → Source 选 `main / (root)` → Save
4. 一两分钟后打开 `https://你的名字.github.io/仓库名/`，手机电脑都能看

以后改完再跑一次第 2 步。没有 git 也能用：网页上直接上传改过的文件，Pages 同样会重建。

**Netlify Drop**：打开 app.netlify.com/drop，把这个文件夹拖进去，立刻得到一个链接；以后改完再拖一次。

**局域网临时看**（手机同 Wi-Fi）：

```
powershell -ExecutionPolicy Bypass -File tools/serve.ps1
```

## 手机上怎么看

**同一个 Wi-Fi**：在电脑上跑

```
powershell -ExecutionPolicy Bypass -File tools/serve.ps1
```

它会打印两个地址，手机浏览器打开 `http://<电脑的内网IP>:8080/` 就行。防火墙第一次可能会问，允许即可。

**发给别人（公网）**：推到 GitHub 再开 Pages

```
powershell -ExecutionPolicy Bypass -File tools/deploy.ps1 -Repo https://github.com/你/仓库.git
```

推完在仓库 Settings → Pages 选 `main / (root)`，一两分钟就有 `https://你.github.io/仓库/`，手机电脑都能开。
也可以直接把整个文件夹拖到 Netlify Drop，同样能拿到链接。

## 怎么打开

双击 `index.html`。

词库以 `.js` 形式提供（`window.DATA_CET4 = [...]`），所以 `file://` 双击也能读，不需要起服务器。

想要本地服务器也行：

```
python -m http.server 8000
```

## 快捷键

单词页：`J` 认识 · `K` 不熟 · `空格` 揭释义 / 下一个 · `←` `→` 前后翻。

## 核心词怎么算的

- 四级核心 = 四级大纲词 − 初中词表 − 高中词表 = **1554**
- 六级核心 = 六级大纲词 − 四级大纲词 = **2298**

两条都可复现，脚本在 `tools/build_core.py`。词表来自同一个仓库的 `1 初中-乱序.txt` / `2 高中-乱序.txt`。

## 2026 那几套和解析

`data/papers_local/` 里已经存了 10 份：

- 四级 2026.06：三套原卷 PDF + 一份参考答案（md 已转成 html，表格和分数对照都能读）
- 六级 2026.06：三套原卷 PDF + 三份解析 PDF

真题库里标「本」的，点开就是本地 PDF；其余的也都改走 `gh-proxy.com` 镜像，点开同样直接是 PDF，不必登 GitHub。
想批量抓到本地（离线）用：

```
python tools/fetch_papers.py --session 2025.12 --kinds 答案解析
python tools/fetch_papers.py --level cet6 --from 2024 --kinds 答案解析
```

抓完会重写 `data/papers.js` 的本地标记；`md` 参考答案再跑一次 `python tools/make_answer_html.py` 转成可读网页。

## 听力现状（2026-11）

国内连不上 `raw.githubusercontent.com`，GitHub API 又限流（60 次/小时、单文件走 base64 JSON 很慢），所以：

- 仓库里现在只有 **1 段**离线音频（2024.12 四级第一套，5 MB），页面标「本地」，点开就能听
- 其余 21 段只有远程地址，点了会提示「不在本地」
- 页面现在优先用 `gh-proxy.com` 镜像流播放（境内可通，实测 200），本地没有的也能听，只是要缓冲几秒
- 抓下来离线用：`python tools/fetch_audio_chunks.py`（分块 + 逐块重试，一段 15 MB 约十几分钟）

这是网络问题，不是播放器的问题：本地音频用 `<audio>` 直接放，已实测 878 秒时长正常。

## 听力：本地优先，远程兜底

清单在 `data/audio.js`。每段音频有两种来路：

- **本地**（页面标「本地」）：文件在 `data/audio/`，离线也能放。仓库里只放了 1 段四级的样例（约 5 MB）。
- **远程**：直接指 GitHub 上的原件，需要联网。国内访问 `raw.githubusercontent.com` 常常不通。

想把某几段抓到本地：

```
python tools/build_audio.py --fetch 2025.06      # 某一个考次
python tools/build_audio.py --fetch cet6_2026_06 # 某一个文件（按 id 匹配）
python tools/build_audio.py --fetch all          # 全抓，约 550 MB 原件 → 压缩后 ~220 MB
```

脚本走 `api.github.com` 的 blob 接口取文件（绕开被墙的 raw 域名），再用 ffmpeg 压成 48kbps 单声道。跑完会重写 `data/audio.js`，页面自动标「本地」。

## 练习怎么出的题

不是题库，是从词库现算：

- 词义：一个词，四个释义（三个来自别的词）
- 音标：给 `/ˈkɜːtən/`，选词
- 搭配：把短语里的词挖掉，四个候选都来自有短语的词
- 拼写：给释义 + 首字母 + 字母数，自己敲

答错会把词写进 `cet.known.cet4/6` 的 `again` 集合，单词页的「错词本」里就能看到。

## 作文批改的口径

七个维度：词数（四级 120 / 六级 150）、段落（建议三段）、连接词覆盖、句子长度、重复实词、拼写（对照本站词库 + 约 400 个常用词）、标点与大小写。合计 15 分。

明确说：这是规则检查，不做语义评价，也不给范文。专有名词、缩写可能被误标成拼写错误。

## 设计上参照的两个 skill

- `Leonxlnx/taste-skill`（tasteskill 2.5）：一屏一个区块、左右边齐、悬停微动效、每页一个「moment」、不叠渐变不发虚光
- `elayadesign/ai-design-skills` 的 `landing-page-design`：字号只落 12/14/16/18/20/24/30/36/48 这几档、间距只用 2/4/8/12/16/24/32/40/48 的刻度、统一缓动曲线、焦点环、跳到正文、reduce motion

两者冲突的地方按 taste-skill 走：不做滚动淡入的卡片，只在首屏做一次入场、首页做一次逐词亮起。

## 资料从哪来

- 词库：[KyleBing/english-vocabulary](https://github.com/KyleBing/english-vocabulary)（有道词条，含例句/短语/同近义）
- 音标：[RealKai42/qwerty-learner](https://github.com/RealKai42/qwerty-learner)
- 真题与音频：[0609x/CET46-Resources](https://github.com/0609x/CET46-Resources)

版权归原作者与原出版方，仅限个人学习，请勿商用。

## 怎么给别人

**压缩包**：整个文件夹发过去，解压双击 `index.html`。

**局域网**：`python -m http.server 8000`，同 Wi-Fi 访问 `http://你的内网IP:8000`。

**公开链接**（GitHub Pages）：

```
git init && git add . && git commit -m "cet desk"
git branch -M main
git remote add origin https://github.com/<你>/<仓库>.git
git push -u origin main
# Settings → Pages → Source: main / root
```

注意：`data/` 里词库约 2.9 MB、样例音频 5 MB，GitHub 单文件限制 100 MB，没问题。

## 重新生成数据

```
python tools/build_data.py     # 词库 + 真题清单（同时写 .json 和 .js）
python tools/build_audio.py    # 听力清单（--fetch 抓音频）
```

## 目录

```
.
├── index.html        封面
├── words.html        单词本
├── papers.html       真题库
├── listen.html       听力
├── quiz.html         练习
├── write.html        作文
├── assets/
│   ├── style.css     全部样式（无框架）
│   ├── app.js        存储 / 日期 / 顶栏
│   ├── words.js  papers.js  listen.js  quiz.js  write.js
├── data/
│   ├── cet4.js  1.7 MB
│   ├── cet6.js  1.1 MB
│   ├── papers.js  0.14 MB
│   ├── audio.js   10 KB
│   └── audio/     本地音频
└── tools/
    ├── build_data.py
    └── build_audio.py
```
