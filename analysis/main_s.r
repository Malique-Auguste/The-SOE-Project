rm(list = ls())
library(fixest)
library(conleyreg)
library(car)

setwd("C:/Users/maliq/Projects/The-SOE-Project/")

alpha <- "0.10"
lambda <- "7"
precision <- "True"

crime_db <- read.csv(paste("data/aggr", alpha, lambda, precision, "db.csv", sep = "_"))

cutoff_dist <- 5
if (alpha == "0.05") {
  cutoff_dist <- 8
} else if (alpha == "0.10") {
  cutoff_dist <- 16
}


# RUN CORRECT REGRESSION

# Run PPML regression with 4 lags
model_4 <- fepois(
  y ~ x_1_d + x_2_d + x_3_d + x_4 +
    s_1_d + s_2_d + s_3_d + s_4 |
    grid_id + lambda_num,
  data = crime_db,
)

# Run PPML regression with 8 lags
model_8 <- fepois(
  y ~ x_1_d + x_2_d + x_3_d + x_4_d + x_5_d + x_6_d + x_7_d + x_8 +
    s_1_d + s_2_d + s_3_d + s_4_d + s_5_d + s_6_d + s_7_d + s_8 |
    grid_id + lambda_num,
  data = crime_db,
)

summary(model_4, vcov = vcov_conley(lat = "lat", lon = "long", cutoff = cutoff_dist, distance = "spherical"))
summary(model_8, vcov = vcov_conley(lat = "lat", lon = "long", cutoff = cutoff_dist, distance = "spherical"))
summary(model_8, vcov = ~grid_id + lambda_num)
summary(model_8, cluster = ~grid_id)





# TEST AUTOCORRELAITON
model_8 <- fepois(
  y ~ y_1 + y_2 + y_3 + y_4 |
    grid_id + lambda_num,
  data = crime_db,
)

summary(model_8, vcov = vcov_conley(lat = "lat", lon = "long", cutoff = cutoff_dist, distance = "spherical"))






#TEST REVERSE CAUSALITY
# Run PPML regression with 8 lags
model_8 <- fepois(
  y ~ x2_d + x1_d + x_1_d + x_2_d + x_3_d + x_4 +
    s2_d + s1_d + s_1_d + s_2_d + s_3_d + s_4 |
    grid_id + lambda_num,
  data = crime_db,
)

summary(model_8, vcov = vcov_conley(lat = "lat", lon = "long", cutoff = cutoff_dist, distance = "spherical"))





# COUNT CRIMES AVERTED
library(MASS)
library(dplyr)

# ---- SETUP: pull the pieces out of your fitted model ----
b    <- coef(model_8)
Z    <- model.matrix(model_8, type = "rhs")
yhat <- fitted(model_8, type = "response")

# ---- STEP 1: the headline number ----
# "How many violent crimes didn't happen because of PDOs?"
ix <- grep("^x_", colnames(Z))
is <- grep("^s_", colnames(Z))

cf <- function(cols) {
  sum(yhat * (exp(-as.vector(Z[, cols, drop = FALSE] %*% b[cols])) - 1))
}

c(own   = cf(ix),
  spill = cf(is),
  both  = cf(c(ix, is)))

# ---- STEP 2: is it a big number or a small one? ----
sum(yhat)              # total violent crimes in the sample

# ---- STEP 3: uncertainty ----
V <- vcov(model_8, vcov = vcov_conley(lat = "lat", lon = "long",
                                      cutoff = cutoff_dist,
                                      distance = "spherical"))
set.seed(1)
draws <- MASS::mvrnorm(5000, b, V)
sims  <- apply(draws, 1, function(bb) sum(yhat * (exp(-as.vector(Z %*% bb)) - 1)))
quantile(sims, c(.025, .5, .975))
