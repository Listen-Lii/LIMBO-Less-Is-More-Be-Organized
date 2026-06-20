# 矩阵重构 - 按分类学级别汇总
library(dplyr)
summarize_by_taxonomy <- function(otu, taxonomy, tax_unit = "{level}") {
  merged <- cbind(otu, taxonomy[tax_unit])
  colnames(merged)[ncol(merged)] <- tax_unit
  summarized <- aggregate(. ~ get(tax_unit), data = merged, sum)
  names(summarized)[1] <- tax_unit
  return(as.data.frame(summarized))
}
reconstructed_matrix <- summarize_by_taxonomy({matrix}, {annotation})
print(head(reconstructed_matrix))