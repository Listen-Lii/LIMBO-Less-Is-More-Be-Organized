# 抽平函数
library(vegan)
raremax <- min(colSums({matrix}))
if ("{depth}" == "mean") raremax <- round(mean(colSums({matrix})))
if ("{depth}" == "median") raremax <- round(median(colSums({matrix})))
rarefied_data <- as.data.frame(t(rrarefy(t({matrix}), raremax)))
print(paste("抽平深度:", raremax))
print(head(rarefied_data))