#!/usr/bin/env python3
"""
douban_to_tmdb.py
读取豆瓣Top250 YAML文件，匹配TMDb电影ID
"""

import sys
import time
import yaml
import requests
from urllib.parse import quote_plus

# 需要安装的库: pip install pyyaml requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0 Safari/537.36"
    )
}

def load_douban_data(filename="douban_top250.yml"):
    """加载豆瓣YAML数据"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data["豆瓣Top250电影列表"]["movies"]
    except Exception as e:
        print(f"❌ 加载豆瓣数据失败: {e}")
        return None

def tmdb_search(title_cn, title_en, year, api_key):
    """在TMDb上搜索电影，返回最优匹配的tmdb_id"""
    def search(title, year=None):
        url = (
            "https://api.themoviedb.org/3/search/movie"
            f"?api_key={api_key}&query={quote_plus(title)}"
        )
        if year:
            url += f"&year={year}"
        return requests.get(url, timeout=15).json().get("results", [])

    # 优先使用年份精确搜索
    results = search(title_cn, year) if year else search(title_cn)
    
    if not results and title_en:
        # 清理英文标题（去掉开头的斜杠和空格）
        clean_title_en = title_en.strip().lstrip('/').strip()
        if clean_title_en:
            results = search(clean_title_en, year) if year else search(clean_title_en)
    
    if not results:
        # 如果带年份搜索失败，尝试不带年份的搜索
        results = search(title_cn)
        if not results and title_en:
            clean_title_en = title_en.strip().lstrip('/').strip()
            if clean_title_en:
                results = search(clean_title_en)
    
    if not results:
        return None

    # 过滤掉非电影类型
    movie_results = []
    for movie in results:
        genres = movie.get("genre_ids", [])
        # 排除脱口秀、电视电影、纪录片
        if 10767 in genres or 10770 in genres or 99 in genres:
            continue
        movie_results.append(movie)
    
    if not movie_results:
        movie_results = results  # 兜底

    # 打印搜索结果
    print(f"  [TMDb搜索] query: {title_cn} / {title_en} ({year})")
    for movie in movie_results[:3]:  # 只显示前3个结果
        tmdb_year = movie.get('release_date', '')[:4] if movie.get('release_date') else ''
        print(
            f"    TMDb: {movie.get('id')} | "
            f"title: {movie.get('title')} | "
            f"original: {movie.get('original_title')} | "
            f"year: {tmdb_year}"
        )

    # 匹配策略
    if year:
        # 1. 标题和年份都完全匹配
        for movie in movie_results:
            tmdb_title = movie.get("title", "").strip().lower()
            tmdb_original = movie.get("original_title", "").strip().lower()
            tmdb_year = movie.get("release_date", "")[:4]
            if tmdb_year == str(year):
                if tmdb_title == title_cn.strip().lower() or tmdb_original == title_en.strip().lower():
                    return movie["id"]

        # 2. 年份完全匹配（不管标题）
        for movie in movie_results:
            tmdb_year = movie.get("release_date", "")[:4]
            if tmdb_year == str(year):
                return movie["id"]

    # 3. 标题完全匹配（忽略年份）
    for movie in movie_results:
        tmdb_title = movie.get("title", "").strip().lower()
        tmdb_original = movie.get("original_title", "").strip().lower()
        if tmdb_title == title_cn.strip().lower() or tmdb_original == title_en.strip().lower():
            return movie["id"]

    # 4. 标题模糊匹配
    for movie in movie_results:
        tmdb_title = movie.get("title", "").strip().lower()
        tmdb_original = movie.get("original_title", "").strip().lower()
        if title_cn.strip().lower() in tmdb_title or title_en.strip().lower() in tmdb_original:
            return movie["id"]

    # 5. 返回第一个结果
    return movie_results[0]["id"] if movie_results else None

def build_kometa_yaml(matched_movies, filename="douban_top250_kometa.yml"):
    """生成Kometa可用的YAML文件"""
    doc = {
        "collections": {
            "豆瓣电影 Top 250": {
                "summary": "豆瓣评分最高的 250 部电影合集；自动生成于脚本",
                "tmdb_movie": []
            }
        }
    }
    
    for movie in matched_movies:
        if movie.get('tmdb_id'):
            doc["collections"]["豆瓣电影 Top 250"]["tmdb_movie"].append({
                "id": movie['tmdb_id'],
                "title": movie['title_cn'],
                "index": movie['rank']
            })
    
    with open(filename, "w", encoding="utf-8") as f:
        yaml.dump(doc, f, allow_unicode=True, sort_keys=False)
    
    print(f"\n🎉 已生成 {filename}，共 {len([m for m in matched_movies if m.get('tmdb_id')])} 部影片")

def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("用法: python douban_to_tmdb.py <TMDB_API_KEY>")
        sys.exit(1)
    
    api_key = sys.argv[1]
    
    print("📖 加载豆瓣Top250数据...")
    movies = load_douban_data()
    if not movies:
        print("❌ 无法加载豆瓣数据")
        sys.exit(1)
    
    print(f"✅ 加载了 {len(movies)} 部电影")
    
    matched_movies = []
    misses = []
    
    for idx, movie in enumerate(movies, 1):
        title_cn = movie['title_cn']
        title_en = movie['title_en']
        year = movie['year']
        rank = movie['rank']
        
        print(f"\n[{rank:3}] 处理: {title_cn} / {title_en} ({year})")
        
        tmdb_id = tmdb_search(title_cn, title_en, year, api_key)
        
        if tmdb_id:
            movie['tmdb_id'] = tmdb_id
            matched_movies.append(movie)
            print(f"{rank:3}/250  √  {title_cn} ({year})  →  TMDb:{tmdb_id}")
        else:
            misses.append(f"{title_cn} / {title_en} ({year})")
            print(f"{rank:3}/250  ×  未找到: {title_cn} / {title_en} ({year})")
        
        time.sleep(0.4)  # 减速，避免TMDb触发速率限制
    
    # 生成Kometa YAML
    build_kometa_yaml(matched_movies)
    
    # 保存未匹配的电影
    if misses:
        with open("not_found.txt", "w", encoding="utf-8") as nf:
            nf.write("\n".join(misses))
        print(f"\n❌ 未匹配到TMDb的电影: {len(misses)} 部")
        print("已记录到 not_found.txt，可手动补充")
        for m in misses[:5]:  # 只显示前5个
            print(" -", m)
        if len(misses) > 5:
            print(f" ... 还有 {len(misses) - 5} 部")

if __name__ == "__main__":
    main()