#!/usr/bin/env python3
"""
douban_top250_crawler.py
抓取豆瓣 Top250 电影信息
"""

import sys
import time
import re
import requests
import yaml
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0 Safari/537.36"
    )
}

def crawl_douban_top250():
    """抓取豆瓣Top250电影信息，返回 [(title_cn, title_en, year, rating, director)] 列表"""
    movies = []
    
    print("📥 开始抓取豆瓣 Top250 …")
    
    for start in range(0, 250, 25):  # 10 页 × 25 条
        url = f"https://movie.douban.com/top250?start={start}"
        print(f"正在抓取第 {start//25 + 1} 页: {url}")
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=20)
            response.raise_for_status()
            html = response.text
            soup = BeautifulSoup(html, "html.parser")

            for item in soup.select("div.item"):
                try:
                    # 提取标题信息
                    hd_div = item.select_one("div.hd")
                    if not hd_div:
                        continue
                        
                    titles = list(hd_div.stripped_strings)
                    title_cn = titles[0].strip()
                    title_en = titles[1].strip() if len(titles) > 1 else ""
                    
                    # 提取年份
                    bd_div = item.select_one("div.bd p")
                    if not bd_div:
                        continue
                        
                    bd_text = bd_div.get_text()
                    # 使用最简单的正则表达式匹配4位数字
                    year_match = re.search(r"(\d{4})", bd_text)
                    year = year_match.group(1) if year_match else ""
                    

                    
                    # 提取评分
                    rating_span = item.select_one("span.rating_num")
                    rating = rating_span.get_text().strip() if rating_span else ""
                    
                    # 提取导演信息
                    director_match = re.search(r"导演:\s*([^主]+)", bd_text)
                    director = director_match.group(1).strip() if director_match else ""
                    
                    # 提取主演信息
                    actor_match = re.search(r"主演:\s*([^\.]+)", bd_text)
                    actors = actor_match.group(1).strip() if actor_match else ""
                    
                    # 提取排名
                    rank_span = item.select_one("em")
                    rank = rank_span.get_text().strip() if rank_span else ""
                    
                    print(f"豆瓣抓取: [{rank}] {title_cn} / {title_en} ({year}) - 评分:{rating} - 导演:{director}")
                    
                    movies.append({
                        'rank': rank,
                        'title_cn': title_cn,
                        'title_en': title_en,
                        'year': year,
                        'rating': rating,
                        'director': director,
                        'actors': actors
                    })
                    
                except Exception as e:
                    print(f"解析电影条目时出错: {e}")
                    continue
                    
            time.sleep(1)  # 礼貌延时，避免被豆瓣封
            
        except requests.RequestException as e:
            print(f"请求第 {start//25 + 1} 页时出错: {e}")
            continue
        except Exception as e:
            print(f"处理第 {start//25 + 1} 页时出错: {e}")
            continue
    
    print(f"✅ 抓取完成，共获取 {len(movies)} 部电影")
    return movies

def save_to_file(movies, filename="douban_top250.yml"):
    """将电影信息保存到YAML文件"""
    # 构建YAML数据结构
    yaml_data = {
        "豆瓣Top250电影列表": {
            "summary": "豆瓣评分最高的250部电影合集",
            "total_count": len(movies),
            "movies": []
        }
    }
    
    for movie in movies:
        # 调试信息
        print(f"保存电影: 排名={movie['rank']}, 年份='{movie['year']}'")
        
        movie_data = {
            "rank": int(movie['rank']),
            "title_cn": movie['title_cn'],
            "title_en": movie['title_en'],
            "year": int(movie['year']) if movie['year'] else None,
            "rating": float(movie['rating']) if movie['rating'] else None,
            "director": movie['director'],
            "actors": movie['actors']
        }
        yaml_data["豆瓣Top250电影列表"]["movies"].append(movie_data)
    
    # 保存为YAML文件
    with open(filename, "w", encoding="utf-8") as f:
        yaml.dump(yaml_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    print(f"💾 已保存到 {filename}")

def main():
    """主函数"""
    print("🎬 豆瓣Top250电影抓取工具")
    print("=" * 30)
    
    try:
        # 抓取电影信息
        movies = crawl_douban_top250()
        
        if movies:
            # 保存到文件
            save_to_file(movies)
            
            # 显示统计信息
            print(f"\n📊 统计信息:")
            print(f"总电影数: {len(movies)}")
            
            # 按年份统计
            year_count = {}
            for movie in movies:
                year = movie['year']
                year_count[year] = year_count.get(year, 0) + 1
            
            print(f"年份分布:")
            for year in sorted(year_count.keys(), reverse=True):
                print(f"  {year}: {year_count[year]} 部")
                
        else:
            print("❌ 未抓取到任何电影信息")
            
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断操作")
    except Exception as e:
        print(f"❌ 程序执行出错: {e}")

if __name__ == "__main__":
    main() 