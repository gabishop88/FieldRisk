## ----setup, include=FALSE-----------------------------------------------------
knitr::opts_chunk$set(echo = TRUE)
library(apsimx)
library(ggplot2)
apsimx_options(warn.versions = FALSE)
tmp.dir <- tempdir()

## ----inspect-apsimx-xml-maize-------------------------------------------------
extd.dir <- system.file("extdata", package = "apsimx")
rue.pth <- inspect_apsim_xml("Maize75.xml", src.dir = extd.dir, parm = "rue")
ext.pth <- inspect_apsim_xml("Maize75.xml", src.dir = extd.dir, parm = "y_extinct_coef")
## To pass them to optim_apsim, combine them
pp <- c(rue.pth, ext.pth)

## ----obsWheat-----------------------------------------------------------------
data(obsWheat)
## See the structure
head(obsWheat)
## Only 10 observations
dim(obsWheat)
## Visualize the data
ggplot(obsWheat, aes(Date, Wheat.AboveGround.Wt)) + 
  geom_line() + 
  ggtitle("Biomass (g/m2)")
  
ggplot(obsWheat, aes(Date, Wheat.Leaf.LAI)) + 
  geom_line() +
  ggtitle("LAI")
  
ggplot(obsWheat, aes(Date, Wheat.Phenology.Stage)) + 
  geom_line() +
  ggtitle("Phenology Stages")

## ----wheat-sim-b4-opt, echo = FALSE-------------------------------------------
sim0 <- read.csv(file.path(extd.dir, "wheat-sim-b4-opt.csv"))
sim0$Date <- as.Date(sim0$Date)

## ----sim0-wheat-sim, eval = FALSE---------------------------------------------
# sim0 <- apsimx("Wheat-opt-ex.apsimx", src.dir = extd.dir, value = "report")

## ----sim0-viz-----------------------------------------------------------------
## Select 
sim0.s <- subset(sim0, 
                 Date > as.Date("2016-09-30") & Date < as.Date("2017-07-01"))
## Visualize before optimization
## phenology
ggplot() + 
  geom_point(data = obsWheat, aes(x = Date, y = Wheat.Phenology.Stage)) +
  geom_line(data = sim0.s, aes(x = Date, y = Wheat.Phenology.Stage)) + 
  ggtitle("Phenology")
## LAI
ggplot() + 
  geom_point(data = obsWheat, aes(x = Date, y = Wheat.Leaf.LAI)) +
  geom_line(data = sim0.s, aes(x = Date, y = Wheat.Leaf.LAI)) + 
  ggtitle("LAI")
## Biomass
ggplot() + 
  geom_point(data = obsWheat, aes(x = Date, y = Wheat.AboveGround.Wt)) +
  geom_line(data = sim0.s, aes(x = Date, y = Wheat.AboveGround.Wt)) + 
    ggtitle("Biomass (g/m2)")

## ----inspect------------------------------------------------------------------
## Finding RUE
inspect_apsimx_replacement("Wheat-opt-ex.apsimx", src.dir = extd.dir,
                           node = "Wheat", 
                           node.child = "Leaf",
                           node.subchild = "Photosynthesis",
                           node.subsubchild = "RUE", 
                           parm = "FixedValue",
                           verbose = FALSE)
## Finding BasePhyllochron
inspect_apsimx_replacement("Wheat-opt-ex.apsimx", src.dir = extd.dir,
                           node = "Wheat", 
                           node.child = "Cultivars",
                           node.subchild = "USA",
                           node.subsubchild = "Yecora", 
                           verbose = FALSE)
## Constructing the paths is straight-forward
pp1 <- "Wheat.Leaf.Photosynthesis.RUE.FixedValue"
pp2 <- "Wheat.Cultivars.USA.Yecora.BasePhyllochron"

## ----optim-apsimx, eval = FALSE-----------------------------------------------
# ## wop is for wheat optimization
# wop <- optim_apsimx("Wheat-opt-ex.apsimx",
#                     src.dir = extd.dir,
#                     parm.paths = c(pp1, pp2),
#                     data = obsWheat,
#                     weights = "mean",
#                     replacement = c(TRUE, TRUE),
#                     initial.values = c(1.2, 120))

## ----load-wop, echo = FALSE---------------------------------------------------
data("wheat-opt-ex", package = "apsimx")

## ----wop-result---------------------------------------------------------------
wop

## ----optim-apsimx-hessian, eval = FALSE---------------------------------------
# ## wop is for wheat optimization
# wop.h <- optim_apsimx("Wheat-opt-ex.apsimx",
#                       src.dir = extd.dir,
#                       parm.paths = c(pp1, pp2),
#                       data = obsWheat,
#                       weights = "mean",
#                       replacement = c(TRUE, TRUE),
#                       initial.values = c(1.2, 120),
#                       hessian = TRUE)

## ----wop-result-hessian-------------------------------------------------------
wop.h

## ----wop-result-opt, eval = FALSE---------------------------------------------
# ## We re-run the model because the Wheat-opt-ex.apsimx file
# ## is already edited
# sim.opt <- apsimx("Wheat-opt-ex.apsimx", src.dir = extd.dir, value = "report")
# sim.opt.s <- subset(sim.opt,
#                     Date > as.Date("2016-09-30") & Date < as.Date("2017-07-01"))

## ----import-wop-result, echo = FALSE------------------------------------------
sim.opt.s <- read.csv(file.path(extd.dir, "wheat-sim-opt.csv"))
sim.opt.s$Date <- as.Date(sim.opt.s$Date)

## ----wop-result-opt-visualize-------------------------------------------------
  ## phenology
  ggplot() + 
    geom_point(data = obsWheat, aes(x = Date, y = Wheat.Phenology.Stage)) +
    geom_line(data = sim.opt.s, aes(x = Date, y = Wheat.Phenology.Stage)) + 
    ggtitle("Phenology")
  ## LAI
  ggplot() + 
    geom_point(data = obsWheat, aes(x = Date, y = Wheat.Leaf.LAI)) +
    geom_line(data = sim.opt.s, aes(x = Date, y = Wheat.Leaf.LAI)) + 
    ggtitle("LAI")
  ## Biomass
  ggplot() + 
    geom_point(data = obsWheat, aes(x = Date, y = Wheat.AboveGround.Wt)) +
    geom_line(data = sim.opt.s, aes(x = Date, y = Wheat.AboveGround.Wt)) + 
    ggtitle("Biomass (g/m2)")

