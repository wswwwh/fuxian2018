# 阶段 B 图形资产映射审计

- 状态：`PASS`
- 原论文图：`54/54`；唯一哈希：`54`。
- 复现图：`54/54`；唯一哈希：`54`。
- 需复核行：`0`。
- 原图均从 137 页主 PDF 以 4.2 倍页面渲染重新提取；名义 302.4 dpi 不代表提升原 PDF 内嵌栅格的固有分辨率。
- 复现图采用当前脚本生成的非空 PNG/PDF 权威输出做哈希保持复制；本阶段不覆盖旧图，也不声称重新计算 54 个数值任务。

## 映射表

| 图号 | 原图尺寸 | 复现图尺寸 | 图题 | 裁切 | 状态 |
|---|---:|---:|---|---|---|
| 2.1 | 1173x1227 | 1329x1391 | pdf_caption_block | embedded_band_exact | pass |
| 2.2 | 1626x483 | 1833x623 | pdf_caption_block | embedded_band_exact | pass |
| 2.3 | 1445x1122 | 1593x1318 | pdf_caption_block | embedded_band_exact | pass |
| 2.4 | 1844x840 | 3143x1443 | pdf_caption_block | embedded_band_exact | pass |
| 2.5 | 1445x1099 | 1431x1345 | pdf_caption_block | embedded_band_exact | pass |
| 2.6 | 1834x1632 | 2477x2206 | pdf_caption_block | embedded_band_union | pass |
| 2.7 | 991x862 | 1322x1337 | pdf_caption_block | embedded_band_exact | pass |
| 2.8 | 1866x810 | 3637x1413 | pdf_caption_block | embedded_band_exact | pass |
| 2.9 | 1445x643 | 1319x675 | pdf_caption_block | embedded_band_exact | pass |
| 2.10 | 1898x420 | 2236x608 | pdf_caption_block | embedded_band_exact | pass |
| 2.11 | 1082x848 | 1778x1464 | pdf_caption_block | embedded_band_exact | pass |
| 2.12 | 1196x613 | 2042x992 | pdf_caption_block | embedded_band_exact | pass |
| 2.13 | 1082x1007 | 1426x1391 | pdf_caption_block | embedded_band_exact | pass |
| 2.14 | 1445x1062 | 1974x1366 | pdf_caption_block | embedded_band_exact | pass |
| 2.15 | 1808x1402 | 1901x1413 | pdf_caption_block | embedded_band_exact | pass |
| 3.1 | 1445x1006 | 1137x1137 | pdf_caption_block | embedded_band_exact | pass |
| 3.2 | 1445x923 | 1415x1148 | pdf_caption_block | embedded_band_exact | pass |
| 3.3 | 1520x537 | 2343x802 | pdf_caption_block | embedded_band_exact | pass |
| 3.4 | 1445x952 | 1285x1125 | pdf_caption_block | embedded_band_exact | pass |
| 3.5 | 1792x1994 | 2382x2402 | pdf_caption_block | embedded_band_union | pass |
| 3.6 | 1838x689 | 2553x1053 | pdf_caption_block | embedded_band_exact | pass |
| 3.7 | 1743x1994 | 2382x2402 | pdf_caption_block | embedded_band_union | pass |
| 3.8 | 1864x734 | 2553x1053 | pdf_caption_block | embedded_band_exact | pass |
| 3.9 | 1824x734 | 2523x1098 | pdf_caption_block | embedded_band_exact | pass |
| 3.10 | 1863x1541 | 2021x1828 | pdf_caption_block | embedded_band_union | pass |
| 3.11 | 1883x1112 | 2503x1473 | pdf_caption_block | embedded_band_exact | pass |
| 3.12 | 1839x1874 | 2382x2402 | pdf_caption_block | embedded_band_union | pass |
| 3.13 | 1863x840 | 2553x1053 | pdf_caption_block | embedded_band_exact | pass |
| 3.14 | 1621x2177 | 2429x2643 | pdf_caption_block | embedded_band_union | pass |
| 3.15 | 1784x764 | 2373x1053 | pdf_caption_block | embedded_band_exact | pass |
| 3.16 | 1871x1723 | 2357x2222 | pdf_caption_block | embedded_band_union | pass |
| 3.17 | 1830x855 | 2403x1053 | pdf_caption_block | embedded_band_exact | pass |
| 4.1 | 1866x795 | 2364x1218 | pdf_caption_block | embedded_band_exact | pass |
| 4.2 | 1899x900 | 2223x1083 | pdf_caption_block | embedded_band_exact | pass |
| 4.3 | 1806x1571 | 2552x2366 | pdf_caption_block | embedded_band_union | pass |
| 4.4 | 1879x1420 | 2545x2150 | pdf_caption_block | embedded_band_union | pass |
| 4.5 | 1869x1541 | 2551x2321 | pdf_caption_block | embedded_band_union | pass |
| 4.6 | 1876x1299 | 2449x1976 | pdf_caption_block | embedded_band_union | pass |
| 4.7 | 1899x1110 | 1529x1383 | pdf_caption_block | embedded_band_exact | pass |
| 4.8 | 1899x868 | 1520x1383 | pdf_caption_block | embedded_band_exact | pass |
| 5.1 | 1519x1420 | 2304x2222 | pdf_caption_block | embedded_band_union | pass |
| 5.2 | 1899x594 | 2703x925 | pdf_caption_block | embedded_band_exact | pass |
| 5.3 | 1899x527 | 2703x765 | pdf_caption_block | embedded_band_exact | pass |
| 5.4 | 1263x887 | 1919x1713 | pdf_caption_block | embedded_band_exact | pass |
| 5.5 | 1263x845 | 1642x1563 | pdf_caption_block | embedded_band_exact | pass |
| 5.6 | 1755x1450 | 2425x2222 | pdf_caption_block | embedded_band_union | pass |
| 5.7 | 1755x1451 | 2425x2222 | pdf_caption_block | embedded_band_union | pass |
| 5.8 | 1798x794 | 2690x1383 | pdf_caption_block | embedded_band_exact | pass |
| 5.9 | 991x1050 | 1398x1453 | pdf_caption_block | embedded_band_exact | pass |
| 5.10 | 1780x991 | 2404x1353 | pdf_caption_block | embedded_band_exact | pass |
| 5.11 | 1898x991 | 2404x1353 | pdf_caption_block | embedded_band_exact | pass |
| 5.12 | 1263x681 | 2012x1083 | pdf_caption_block | embedded_band_exact | pass |
| 5.13 | 1445x1046 | 1890x1563 | pdf_caption_block | embedded_band_exact | pass |
| 5.14 | 1235x2025 | 1803x2582 | pdf_caption_block | embedded_band_union | pass |
