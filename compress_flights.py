import pandas as pd

def compress_flight_data(input_csv, output_csv):
    """把庞大的原始轨迹 CSV 聚合成带权重的唯一航线 CSV。

    输出列: flight_id, origin, dest, time, weight
    - weight: 该航线的总飞行次数
    - flight_id / time: 取该航线最近一次（时间最新）的航班号与时间作为代表，
      这样压缩后的 CSV 依然能被 app 完整识别（含航司与日期），
      不再显示「— / 无日期」。
    """
    print(f"正在读取原始轨迹数据: {input_csv} ...")
    try:
        df = pd.read_csv(input_csv)
        original_count = len(df)

        if not {'origin', 'dest'}.issubset(df.columns):
            print("错误：CSV 文件中必须包含 'origin' 和 'dest' 列！")
            return

        # 识别可用的航班号 / 时间列（若原始数据有）
        FID = ('flight_id', 'flight', 'flight_no', 'no')
        TIME = ('time', 'dep_time', 'departure', 'date')
        fid_col = next((c for c in FID if c in df.columns), None)
        time_col = next((c for c in TIME if c in df.columns), None)

        # 剔除缺机场代码 / 起点==终点 的无效行
        df = df.dropna(subset=['origin', 'dest'])
        df = df[df['origin'] != df['dest']]

        # 按时间倒序排序，保证每组第一条 = 最近一次飞行
        if time_col:
            df = df.sort_values(time_col, na_position='last')

        rows = []
        for (o, d), sub in df.groupby(['origin', 'dest'], sort=False):
            rows.append({
                'flight_id': str(sub[fid_col].iloc[0]) if fid_col else '',
                'origin': o,
                'dest': d,
                'time': sub[time_col].iloc[0] if time_col else '',
                'weight': len(sub),
            })

        compressed = pd.DataFrame(rows, columns=['flight_id', 'origin', 'dest', 'time', 'weight'])
        compressed.to_csv(output_csv, index=False)

        new_count = len(compressed)
        compression_rate = (1 - new_count / original_count) * 100 if original_count else 0

        print("\n✅ 数据压缩完成！")
        print(f"原始轨迹数量: {original_count} 条")
        print(f"压缩后唯一航线: {new_count} 条")
        print(f"压缩率: {compression_rate:.2f}% (您的显卡将少做这么多无用功！)")
        print(f"每行保留该航线最近一次的航班号与时间作为代表")
        print(f"已生成文件: {output_csv}")

    except FileNotFoundError:
        print(f"错误：找不到文件 {input_csv}，请确保它在这个文件夹里。")

if __name__ == "__main__":
    # 执行压缩：flights.csv（原始轨迹）-> sample.csv（去重后唯一航线）
    compress_flight_data("flights.csv", "sample.csv")
