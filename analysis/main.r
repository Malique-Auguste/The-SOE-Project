rm(list = ls())
library(fixest)
library(conleyreg)
library(car)

setwd("C:/Users/maliq/Projects/The-SOE-Project/")
crime_db <-read.csv("data/aggr_0.03_4_True_db_s.csv")

summary(crime_db)

# Run PPML regression with 4 lags
model <- fepois(
  crime_num ~ do_num_1 + do_num_2 + do_num_3 + do_num_4 +
    do_spill_1 + do_spill_2 + do_spill_3 + do_spill_4 |
    grid_id + lambda_num,
  data = crime_db,
)

# Run PPML regression with 8 lags
model <- fepois(
  crime_num ~ do_num_1 + do_num_2 + do_num_3 + do_num_4 + do_num_5 + do_num_6 + do_num_7  + do_num_8 +
    do_spill_1 + do_spill_2 + do_spill_3 + do_spill_4 + do_spill_5 + do_spill_6 + do_spill_7 + do_spill_8 |
    grid_id + lambda_num,
  data = crime_db,
)

#### TEST FOR TEMPORAL AUTOCORELATION -JUSTIFICATION OF NO NEED FOR TEMPORAL CUT OFFS
df <- crime_db[obs(model_8), ]
df$resid <- residuals(model, type = "response")

# lag residuals within region
df <- df[order(df$grid_id, df$lambda_num), ]
df$resid_lag1 <- ave(df$resid, df$grid_id, FUN = function(x) c(NA, head(x, -1)))

# pooled check
summary(feols(resid ~ resid_lag1, data = df, cluster = "grid_id"))
#### TEST DONE


cor(crime_db[c("do_num", "do_num_1", "do_num_2", "do_num_3", "do_num_4", "do_num_5", "do_num_6", "do_num_7", 
               "do_spill", "do_spill_1", "do_spill_2", "do_spill_3", "do_spill_4", "do_spill_5", "do_spill_6", "do_spill_7")], use = "complete.obs")
