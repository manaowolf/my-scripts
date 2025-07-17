#!/usr/bin/env python3
"""
merge_yaml.py
合并豆瓣原始数据和TMDb匹配数据到一个完整的YAML文件
"""

import yaml
import sys

def load_yaml_file(filename):
    """加载YAML文件"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ 加载 {filename} 失败: {e}")
        return None

def merge_data(douban_data, tmdb_data):
    """合并豆瓣和TMDb数据"""
    # 创建TMDb ID映射
    tmdb_mapping = {}
    if tmdb_data and "collections" in tmdb_data:
        for movie in tmdb_data["collections"]["豆瓣电影 Top 250"]["tmdb_movie"]:
            tmdb_mapping[movie["title"]] = {
                "tmdb_id": movie["id"],
                "index": movie["index"]
            }
    
    # 合并数据
    merged_movies = []
    douban_movies = douban_data["豆瓣Top250电影列表"]["movies"]
    
    for movie in douban_movies:
        title_cn = movie["title_cn"]
        tmdb_info = tmdb_mapping.get(title_cn, {})
        
        merged_movie = {
            "rank": movie["rank"],
            "title_cn": movie["title_cn"],
            "title_en": movie["title_en"],
            "year": movie["year"],
            "rating": movie["rating"],
            "director": movie["director"],
            "actors": movie["actors"],
            "tmdb_id": tmdb_info.get("tmdb_id")
        }
        merged_movies.append(merged_movie)
    
    return merged_movies

def save_merged_yaml(merged_movies, filename="douban_top250_complete.yml"):
    """保存合并后的YAML文件"""
    yaml_data = {
        "豆瓣Top250完整数据": {
            "summary": "豆瓣Top250电影完整信息，包含TMDb匹配结果",
            "total_count": len(merged_movies),
            "matched_count": len([m for m in merged_movies if m.get("tmdb_id")]),
            "movies": merged_movies
        }
    }
    
    with open(filename, "w", encoding="utf-8") as f:
        yaml.dump(yaml_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    print(f"💾 已保存到 {filename}")

def main():
    """主函数"""
    print("🔄 开始合并YAML文件...")
    
    # 加载豆瓣原始数据
    print("📖 加载豆瓣原始数据...")
    douban_data = load_yaml_file("douban_top250.yml")
    if not douban_data:
        print("❌ 无法加载豆瓣数据")
        sys.exit(1)
    
    # 加载TMDb匹配数据
    print("📖 加载TMDb匹配数据...")
    tmdb_data = load_yaml_file("douban_top250_kometa.yml")
    if not tmdb_data:
        print("⚠️  无法加载TMDb数据，将只保存豆瓣原始数据")
        tmdb_data = None
    
    # 合并数据
    print("🔄 合并数据...")
    merged_movies = merge_data(douban_data, tmdb_data)
    
    # 保存合并后的数据
    print("💾 保存合并后的数据...")
    save_merged_yaml(merged_movies)
    
    # 显示统计信息
    total_count = len(merged_movies)
    matched_count = len([m for m in merged_movies if m.get("tmdb_id")])
    
    print(f"\n📊 合并完成！")
    print(f"总电影数: {total_count}")
    print(f"TMDb匹配数: {matched_count}")
    print(f"匹配率: {matched_count/total_count*100:.1f}%")
    
    # 显示前几个匹配结果作为示例
    print(f"\n📋 前5个匹配结果示例:")
    for i, movie in enumerate(merged_movies[:5]):
        status = "✅" if movie.get("tmdb_id") else "❌"
        print(f"{status} [{movie['rank']}] {movie['title_cn']} ({movie['year']}) - TMDb: {movie.get('tmdb_id', 'N/A')}")

if __name__ == "__main__":
    main() 