# Alpha 多样性计算 + 箱线图
library(vegan)
library(ggplot2)
library(ggpubr)
library(dplyr)

DDDc2 <- function(t2) {
  t3 <- as.data.frame(estimateR(t(t2)))
  DDD <- data.frame(
    Shannon = as.array(diversity(t2, "shannon", MARGIN = 2, base = exp(1))),
    Simpson = as.array(diversity(t2, "simpson", MARGIN = 2)),
    ACE = t(t3["S.ACE", ]),
    Chao1 = t(t3["S.chao1", ]),
    richness = t(t3["S.obs", ])
  )
  DDD$samples <- rownames(DDD)
  rownames(DDD) <- NULL
  return(DDD)
}

mkboxplot2 <- function(t4, group, vy) {
  f1 <- as.formula(paste0(vy, '~', group))
  AA <- aov(f1, data = t4)
  duncan_result <- duncan.test(AA, group)
  significant_labels <- as.data.frame(duncan_result$groups) %>% select(-!!sym(vy))
  significant_labels[[group]] <- rownames(significant_labels)
  t4 <- merge(t4, significant_labels, by = group, all.x = TRUE)
  p <- ggboxplot(t4, x = group, y = vy, color = group, add = "jitter")
  p <- p + geom_text(aes(y = max(!!sym(vy)), label = groups), vjust = -0.35) +
    stat_summary(fun.y = 'mean', geom = 'point', colour = 'blue') +
    stat_summary(fun.y = 'mean', geom = 'line', aes(group = 1), colour = 'blue')
  return(p)
}

mkboxplot1 <- function(t4, group, vy, testsel) {
  p <- ggboxplot(t4, x = group, y = vy, color = group, add = "jitter")
  p2 <- p + stat_compare_means(method = testsel)
  return(p2)
}

# 计算 Alpha 多样性
alpha_results <- DDDc2(t({matrix}))

# 合并分组信息
if (!is.null({group}) && exists({group})) {
  alpha_results <- merge(alpha_results, {group}, by.x = 'samples', by.y = colnames({group})[1], all.x = TRUE)
}

# 生成箱线图
if (!is.null({group}) && exists({group})) {
  gp_col <- colnames({group})[2]
  p1 <- mkboxplot2(alpha_results, gp_col, 'Shannon')
  p2 <- mkboxplot2(alpha_results, gp_col, 'Simpson')
  p3 <- mkboxplot2(alpha_results, gp_col, 'ACE')
  p4 <- mkboxplot2(alpha_results, gp_col, 'Chao1')
  p5 <- mkboxplot2(alpha_results, gp_col, 'richness')
} else {
  p1 <- ggplot(alpha_results, aes(y = Shannon)) + geom_boxplot() + labs(title = 'Shannon')
  p2 <- ggplot(alpha_results, aes(y = Simpson)) + geom_boxplot() + labs(title = 'Simpson')
  p3 <- ggplot(alpha_results, aes(y = ACE)) + geom_boxplot() + labs(title = 'ACE')
  p4 <- ggplot(alpha_results, aes(y = Chao1)) + geom_boxplot() + labs(title = 'Chao1')
  p5 <- ggplot(alpha_results, aes(y = richness)) + geom_boxplot() + labs(title = 'richness')
}

alpha_plot <- (p1 + p2 + p3) / (p4 + p5 + ggplot() + theme_minimal())
alpha_plot <- alpha_plot + plot_layout(guides = "collect") & theme(axis.text.x = element_text(angle = 45, hjust = 1), legend.position = "right")

print("Alpha diversity results:")
print(head(alpha_results))
print("Alpha diversity plot generated")