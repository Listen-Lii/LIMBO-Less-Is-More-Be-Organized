# Beta 多样性计算 + 排序图
library(vegan)
library(ggplot2)

NMDploting2 <- function(x, gp, id, gpid) {
  nmds_otu <- metaMDS(x, distance = "bray", k = 2)
  nmds_otu_site <- data.frame(nmds_otu$points)
  nmds_otu_site$x <- row.names(nmds_otu_site)
  nmds_otu_site <- merge(nmds_otu_site, gp, by.x = "x", by.y = id, all.x = TRUE)
  p <- ggplot(data = nmds_otu_site, aes(x = MDS1, y = MDS2, color = .data[[gpid]], fill = .data[[gpid]])) +
    geom_point(size = 3) +
    theme_bw() +
    theme(panel.grid = element_blank()) +
    geom_vline(xintercept = 0, lty = "dashed") +
    geom_hline(yintercept = 0, lty = "dashed") +
    labs(x = "NMDS1", y = "NMDS2", color = gpid, fill = gpid) +
    annotate("text", label = paste("Stress =", round(nmds_otu$stress, 4)), x = -Inf, y = Inf, hjust = -0.2, vjust = 2, size = 4, colour = "black")
  return(p)
}

# 计算距离矩阵
dist_mat <- vegdist(t({matrix}), method = "bray")

# 计算 Beta 多样性
if ("{method}" == "NMDS") {
  result <- metaMDS(dist_mat)
  beta_results <- as.data.frame(result$points)
  beta_results$Stress <- result$stress
  beta_plot <- NMDploting2(t({matrix}), NULL, NULL, "Group")
} else {
  result <- cmdscale(dist_mat, k = 2)
  beta_results <- as.data.frame(result)
  colnames(beta_results) <- c("PC1", "PC2")
  beta_results$Group <- rownames(beta_results)
  beta_plot <- ggplot(beta_results, aes(x = PC1, y = PC2, color = Group)) +
    geom_point(size = 3) +
    theme_bw() +
    theme(panel.grid = element_blank()) +
    labs(x = "PC1", y = "PC2")
}

print("Beta diversity results:")
print(head(beta_results))
print("Beta diversity plot generated")