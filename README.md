# ✈ 飞行足迹 · Flight Footprints
**Language:** [English](#english) | [中文](#chinese)

> A **100% local, privacy-first** personal flight tracker — like the "flight footprints" feature in 航旅纵横, but every trajectory is imported from your own CSV and saved **only in your browser**. No server, no upload, no account.

<a id="english"></a>
## 📖 Overview
**Flight Footprints** turns your personal flight history into a beautiful, interactive 3D globe. Import a simple CSV of your flights (flight number, origin, destination, time) and instantly get a 航旅纵横-style flight logbook: a chronological flight list, live statistics, animated route highlighting, and a cinematic trip replay — all rendered on a WebGL Earth.

Your data never leaves your device. Imported flights are persisted in the browser's `localStorage` only for the current session; each time you open the page you start fresh and can import a new CSV.

## ✨ Core Features
* **📒 Personal Flight Logbook:** A clean side panel lists every flight as a card — flight number, route (IATA ✈ IATA), date, departure time, estimated duration and distance. Sort by time or by distance.
* **📊 Live Statistics:** Total flights, total distance (km, great-circle / Haversine), total flight time, and airports visited — recomputed instantly on import.
* **🎯 Route Highlight & Focus:** Click any flight to highlight its arc in gold, dim the rest, and smoothly fly the camera to frame that route. A detail card shows the full airport names, date, duration and distance.
* **▶ Trip Replay:** Play your flights back chronologically as an animated timeline — the globe follows each leg with a flowing "aircraft" dash animation.
* **💾 Local-Only Persistence (localStorage):** Flights are saved in your browser only while the page is open. Each new CSV import replaces the previous data, so old tracks are not carried over. **Nothing is ever uploaded.**
* **🌍 Fully Offline Globe:** Local Earth textures + 10m-resolution TopoJSON province boundaries. No map API keys, no network tiles.
* **🔍 Semantic Zoom (LOD):** Airport labels and province borders fade in/out based on camera altitude.
* **🛫 Airport Route Filter:** Select any airport to display only flights departing from it, or only flights arriving at it.
* **🛠️ Classic Console:** Theme switch (Satellite / Dark), 3D globe ⇄ 2D map projection, layer toggles, Earth auto-rotation, airport search, and high-res PNG snapshot export.
* **🌐 Bilingual UI:** Full Chinese / English interface.

## 🗂️ CSV Format
Minimum columns (header names are flexible & case-insensitive):

| Column | Accepted names | Example |
|--------|----------------|---------|
| Flight number | `flight_id`, `flight`, `flight_no`, `no` | `MU5601` |
| Origin (IATA) | `origin`, `origin_iata`, `from`, `dep` | `PVG` |
| Destination (IATA) | `dest`, `dest_iata`, `to`, `arr` | `SHE` |
| Departure time | `time`, `dep_time`, `departure`, `date` | `2025-02-18T10:20:00Z` |

Rows with a missing airport code or `origin == dest` are skipped automatically. See `mysample.csv` for a working example.

## 🛠️ Getting Started
1. **Start the local server:** double-click `Start_Server.bat` (runs `python -m http.server 8000` to bypass browser CORS). A browser tab opens automatically.
2. **Import your flights:** in the left "✈ 我的飞行足迹" panel, choose your `.csv`. Statistics and the flight list populate immediately and are saved locally.
3. **Explore:** click a flight to focus its route, hit **▶ 行程回放** for a cinematic replay, toggle 2D/3D, themes and rotation from the right console.

## ⚙️ Optional Data Tools
* `optimize_airports.py` — rebuild `optimized_airports.csv` from a raw OurAirports dump.
* `compress_flights.py` — aggregate a huge raw trajectory CSV into weighted routes.

## 🔒 Privacy
All flight data is processed **entirely in your browser** and stored in `localStorage` under `flightTracker.flights`. There is no backend, no analytics, and no network request carrying your data. Clearing data (with confirmation) wipes both the UI and local storage.

## 🚧 Status
Actively developed. Contributions and feedback are welcome!

---

<a id="chinese"></a>
# ✈ 飞行足迹（纯本地 · 隐私优先）

> 一个 **100% 本地、隐私优先** 的个人飞行轨迹记录器 —— 类似「航旅纵横」里的飞行足迹，但所有轨迹都由你从本地 CSV 导入，并且**只保存在你自己的浏览器里**。无服务器、不上传、无需账号。

## 📖 项目简介
**飞行足迹** 把你的个人飞行历史变成一颗精美的交互式 3D 地球。导入一份简单的航班 CSV（航班号、出发地、目的地、时间），即可获得「航旅纵横」式的飞行记录簿：按时间排列的航班清单、实时统计、航线高亮动画，以及电影感的行程回放 —— 全部渲染在 WebGL 地球上。

你的数据绝不离开本机。导入的航班仅在当前会话期间保存在浏览器 `localStorage`，每次打开页面都会从空白开始，需要重新导入新的 CSV。

## ✨ 核心功能
* **📒 个人飞行记录簿：** 左侧卡片式清单展示每一程 —— 航班号、航线（IATA ✈ IATA）、日期、起飞时间、估算时长与里程。支持按时间/按里程排序。
* **📊 实时统计：** 飞行次数、总里程（km，大圆/Haversine）、总飞行时长、到达机场数，导入即算。
* **🎯 航线高亮与聚焦：** 点击任一航班，该航线金黄高亮、其余变暗，镜头平滑飞过去框住整条航线；详情卡展示机场全称、日期、时长与里程。
* **▶ 行程回放：** 按时间顺序把航班逐条回放成动画时间线，地球跟随每一程，带流动的「飞机划过」虚线效果。
* **💾 纯本地持久化（localStorage）：** 航班仅在当前页面打开期间保存在浏览器里。每次导入新的 CSV 都会替换旧轨迹，不再保留老数据。**绝不上传任何数据。**
* **🌍 纯离线地球：** 本地地球贴图 + 10m 级 TopoJSON 省界。无需地图 API Key、无网络瓦片。
* **🔍 智能缩放 (LOD)：** 机场标签与省界随视角高度动态显隐。
* **🛫 机场航线筛选：** 选择任意机场，可只显示从该机场起飞的航班，或只显示降落在该机场的航班。
* **🛠️ 经典控制台：** 主题切换（卫星/暗色）、3D 地球 ⇄ 2D 展开图、图层控制、地球自转、机场搜索、高清 PNG 截图导出。
* **🌐 中英双语界面。**

## 🗂️ CSV 格式
最少需要的列（表头名灵活、不区分大小写）：

| 字段 | 可识别的列名 | 示例 |
|------|--------------|------|
| 航班号 | `flight_id`、`flight`、`flight_no`、`no` | `MU5601` |
| 出发地(IATA) | `origin`、`origin_iata`、`from`、`dep` | `PVG` |
| 目的地(IATA) | `dest`、`dest_iata`、`to`、`arr` | `SHE` |
| 起飞时间 | `time`、`dep_time`、`departure`、`date` | `2025-02-18T10:20:00Z` |

机场代码缺失或 `起点==终点` 的行会自动跳过。完整示例见 `mysample.csv`。

## 🛠️ 如何运行
1. **启动本地服务：** 双击 `Start_Server.bat`（内部执行 `python -m http.server 8000` 以绕过浏览器跨域限制），浏览器会自动打开。
2. **导入航班：** 在左侧「✈ 我的飞行足迹」面板选择你的 `.csv`，统计与航班清单即刻生成并本地保存。
3. **开始探索：** 点击航班聚焦其航线，点 **▶ 行程回放** 看电影式回放；右侧控制台可切换 2D/3D、主题与自转。

## ⚙️ 可选数据工具
* `optimize_airports.py` —— 从原始 OurAirports 数据重建 `optimized_airports.csv`。
* `compress_flights.py` —— 把庞大的原始轨迹 CSV 聚合成带权重的航线。

## 🔒 隐私说明
所有飞行数据**完全在你的浏览器内处理**，存储在 `localStorage` 的 `flightTracker.flights` 键下。没有后端、没有统计上报、没有任何携带你数据的网络请求。清除数据（带二次确认）会同时清空界面与本地存储。

## 🚧 开发状态
持续开发中，欢迎交流与贡献！
