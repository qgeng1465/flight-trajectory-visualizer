import pandas as pd

def optimize_airport_db(input_file, output_file):
    print("加载原始数据集...")
    df = pd.read_csv(input_file)
    original_shape = df.shape
    
    # 步骤 1：滤除没有 IATA 代码的噪音数据
    df_clean = df[df['iata_code'].notna()].copy()
    
    # 步骤 2：限制为大中型民航枢纽
    target_types = ['large_airport', 'medium_airport']
    df_clean = df_clean[df_clean['type'].isin(target_types)]
    
    # 步骤 3：特征选择（仅保留前端 WebGL 必需的维度）
    cols_to_keep = ['iata_code', 'name', 'latitude_deg', 'longitude_deg', 'type']
    df_clean = df_clean[cols_to_keep]
    
    # 输出
    df_clean.to_csv(output_file, index=False)
    print(f"数据清洗完成！")
    print(f"原始规模: {original_shape[0]} 行")
    print(f"优化后规模: {df_clean.shape[0]} 行")

if __name__ == "__main__":
    optimize_airport_db('airports.csv', 'optimized_airports.csv')