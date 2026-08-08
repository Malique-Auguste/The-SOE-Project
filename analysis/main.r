rm(list = ls())
library(fixest)
library(car)

setwd("C:/Users/maliq/Projects/CrimeWatch/")
crime_db <-read.csv("data/aggr_0.10_db.csv")

summary(crime_db)

# Run PPML regression with grid and week fixed effects
model <- fepois(
  crime_num ~ do_num + do_num_1 + do_num_2 + do_num_3 + do_num_4 + do_num_5 + do_num_6 + do_num_7 +
    do_spill + do_spill_1 + do_spill_2 + do_spill_3 + do_spill_4 + do_spill_5 + do_spill_6 + do_spill_7 |
    grid_id + week_num,
  data = crime_db,
)

summary(model, vcov = ~grid_id + week_num)
summary(model, vcov = vcov_conley(lat = "lat", lon = "long", cutoff = 8, distance = "spherical"))
summary(model, vcov = vcov_conley(lat = "lat", lon = "long", cutoff = 16, distance = "spherical"))

cor(crime_db[c("do_num", "do_num_1")], use = "complete.obs")

cor(crime_db[c("do_num", "do_num_1", "do_num_2", "do_num_3", "do_num_4", "do_num_5", "do_num_6", "do_num_7", 
               "do_spill", "do_spill_1", "do_spill_2", "do_spill_3", "do_spill_4", "do_spill_5", "do_spill_6", "do_spill_7")], use = "complete.obs")
