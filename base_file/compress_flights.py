import pandas as pd

def compress_flight_data(input_csv, output_csv):
    print(f"正在读取原始轨迹数据: {input_csv} ...")
    try:
        # 1. 读取原始数据
        df = pd.read_csv(input_csv)
        original_count = len(df)
        
        # 2. 检查必须的列是否存在
        if not {'origin', 'dest'}.issubset(df.columns):
            print("错误：CSV 文件中必须包含 'origin' 和 'dest' 列！")
            return
            
        # 3. 核心魔法：按起点和终点进行分组，并计算出现的次数 (size)
        # 比如 500条 PVG->JFK 会被合并为 1条，新增一列 'weight' 值为 500
        compressed_df = df.groupby(['origin', 'dest']).size().reset_index(name='weight')
        
        # 4. 剔除起点和终点一样的数据（无效原地打转的数据）
        compressed_df = compressed_df[compressed_df['origin'] != compressed_df['dest']]
        
        # 5. 保存为新的极致精简版 CSV
        compressed_df.to_csv(output_csv, index=False)
        
        new_count = len(compressed_df)
        compression_rate = (1 - new_count / original_count) * 100
        
        print("\n✅ 数据压缩完成！")
        print(f"原始轨迹数量: {original_count} 条")
        print(f"压缩后唯一航线: {new_count} 条")
        print(f"压缩率: {compression_rate:.2f}% (您的显卡将少做这么多无用功！)")
        print(f"已生成文件: {output_csv}")
        
    except FileNotFoundError:
        print(f"错误：找不到文件 {input_csv}，请确保它在这个文件夹里。")

if __name__ == "__main__":
    # 执行压缩，生成 compressed_flights.csv
    compress_flight_data("sample_data.csv", "compressed_flights.csv")