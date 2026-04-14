// data_worker.js 
// V2.0 极速流式分块聚合引擎 (Streaming Map-Reduce Engine)

importScripts('https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.4.1/papaparse.min.js');

self.onmessage = function(e) {
    const { file, db } = e.data;
    
    // 使用 V8 引擎底层的 Map 结构，实现 O(1) 复杂度的超高速寻址与内存预分配
    let arcMap = new Map();
    let hubMap = new Map();

    Papa.parse(file, {
        header: true, 
        dynamicTyping: true, 
        skipEmptyLines: true, 
        fastMode: true,
        // 【核心提速机制】：开启 chunk 流式分块处理。
        // 读取一部分处理一部分，即用即弃，绝不撑爆内存 (No Out-Of-Memory)
        chunk: function(results) {
            const data = results.data;
            for (let i = 0; i < data.length; i++) {
                const x = data[i];
                const s_iata = (x.origin || '').trim().toUpperCase();
                const d_iata = (x.dest || '').trim().toUpperCase();
                
                const s = db[s_iata];
                const d = db[d_iata];
                
                if (s && d) {
                    const w = x.weight || 1; // 自动兼容原数据或已带有权重的数据
                    const arcKey = s_iata + '-' + d_iata;
                    
                    // 极速高频轨迹汇聚 (Edge Aggregation)
                    if (arcMap.has(arcKey)) {
                        arcMap.get(arcKey).weight += w;
                    } else {
                        arcMap.set(arcKey, { startLat: s.lt, startLng: s.lg, endLat: d.lt, endLng: d.lg, weight: w });
                    }
                    
                    // 极速核心枢纽汇聚 (Node Aggregation)
                    hubMap.set(s_iata, (hubMap.get(s_iata) || 0) + w);
                    hubMap.set(d_iata, (hubMap.get(d_iata) || 0) + w);
                }
            }
        },
        complete: function() {
            // 将 Map 字典序列化为数组并跨线程回传
            const rawArcs = Array.from(arcMap.values());
            const rawHubs = Array.from(hubMap.entries()).map(([k, v]) => ({ ...db[k], iata: k, v }));
            
            self.postMessage({ status: 'success', rawArcs, rawHubs });
        },
        error: function(err) { 
            self.postMessage({ status: 'error', message: err.message }); 
        }
    });
};