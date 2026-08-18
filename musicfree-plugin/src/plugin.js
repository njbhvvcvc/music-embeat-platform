/**
 * MusicFree Embeat 智能推荐插件 v1.0.0
 *
 * 安装方式：
 * MusicFree → 设置 → 插件设置 → 安装本地插件 → 选择此文件
 *
 * 功能：
 * - 智能推荐：基于 Embeat 引擎的声学推荐
 * - 热门推荐：当前流派热门歌曲
 * - 相似歌曲：根据当前歌曲推荐相似曲目
 *
 * 配置：
 * - API_BASE_URL: 自建 Embeat 服务地址（默认 http://localhost:8080）
 * - API_TOKEN: 鉴权 Token（如服务端未开启鉴权可不填）
 */

const API_BASE_URL = "http://localhost:8080/api/v1";
const API_TOKEN = "";

const headers = {};
if (API_TOKEN) {
  headers["Authorization"] = "Bearer " + API_TOKEN;
}

/**
 * 搜索/推荐（Embeat 插件无传统搜索，改为"推荐"入口）
 * 搜索类型为 "recommend" 时触发智能推荐
 */
async function search(query, page, type) {
  if (type === "recommend") {
    return await getRecommendations(query, page);
  }
  return { isEnd: true, data: [] };
}

/**
 * 获取推荐结果
 */
async function getRecommendations(seed, page) {
  try {
    const resp = await axios.post(
      API_BASE_URL + "/recommend",
      {
        seed: seed,
        top_k: 20,
        channels: "similar,popular,same_artist,related_artist",
      },
      { headers: headers }
    );
    const data = resp.data;
    if (data.code !== 0) {
      return { isEnd: true, data: [] };
    }
    const items = data.data.map(normalizeTrack);
    return { isEnd: true, data: items };
  } catch (e) {
    console.error("Embeat 推荐请求失败:", e);
    return { isEnd: true, data: [] };
  }
}

/**
 * 获取歌曲详情（补全封面、歌词等元数据）
 */
async function getMusicInfo(musicItem) {
  if (!musicItem || !musicItem.id) {
    return null;
  }
  return musicItem;
}

/**
 * 获取播放链接（代理到 GD Studio API）
 */
async function getMediaSource(musicItem, quality) {
  if (!musicItem || !musicItem.id) {
    return null;
  }
  try {
    const brMap = { low: 128, standard: 192, high: 320, super: 999 };
    const br = brMap[quality] || 320;
    const source = musicItem.source || "netease";
    const resp = await axios.get(API_BASE_URL.replace("/api/v1", ""), {
      params: {
        types: "url",
        source: source,
        id: musicItem.id,
        br: br,
      },
    });
    const data = resp.data;
    if (data.url) {
      return { url: data.url, headers: {} };
    }
    return null;
  } catch (e) {
    console.error("获取播放链接失败:", e);
    return null;
  }
}

/**
 * 获取歌词
 */
async function getLyric(musicItem) {
  if (!musicItem || !musicItem.lyric_id) {
    return null;
  }
  try {
    const source = musicItem.source || "netease";
    const resp = await axios.get(API_BASE_URL.replace("/api/v1", ""), {
      params: {
        types: "lyric",
        source: source,
        id: musicItem.lyric_id,
      },
    });
    const data = resp.data;
    return {
      rawLrc: data.lyric || "",
      transLrc: data.tlyric || "",
    };
  } catch (e) {
    return null;
  }
}

/**
 * 导入歌单（将推荐结果保存为歌单）
 */
async function importMusicSheet(text) {
  try {
    const seeds = text.split("\n").filter(Boolean);
    if (seeds.length === 0) return null;
    const allTracks = [];
    for (const seed of seeds.slice(0, 5)) {
      const result = await getRecommendations(seed, 1);
      allTracks.push(...result.data);
    }
    const seen = new Set();
    const unique = allTracks.filter((t) => {
      if (seen.has(t.id)) return false;
      seen.add(t.id);
      return true;
    });
    return {
      title: "Embeat 智能推荐",
      data: unique.slice(0, 50),
    };
  } catch (e) {
    console.error("导入歌单失败:", e);
    return null;
  }
}

/**
 * 标准化曲目数据为 MusicFree IMusicItem 格式
 */
function normalizeTrack(item) {
  return {
    id: item.track_id || "",
    title: item.title || "未知歌曲",
    artist: item.artist || "未知歌手",
    album: item.album || "",
    artwork: item.pic_url || "",
    source: "embeat",
    url: "",
    platform: "Embeat 推荐",
  };
}

module.exports = {
  platform: "Embeat 推荐",
  version: "1.0.0",
  srcUrl: "https://github.com/yourname/musicfree-plugin-embeat/releases/latest/download/plugin.js",
  cacheControl: "no-cache",
  search: search,
  getMusicInfo: getMusicInfo,
  getMediaSource: getMediaSource,
  getLyric: getLyric,
  importMusicSheet: importMusicSheet,
};