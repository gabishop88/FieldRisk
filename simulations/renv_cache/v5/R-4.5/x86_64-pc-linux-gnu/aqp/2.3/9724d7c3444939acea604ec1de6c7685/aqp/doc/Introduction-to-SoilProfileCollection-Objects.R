## ----setup, echo=FALSE, results='hide', warning=FALSE---------------------------------------------
knitr::opts_chunk$set(
  message = FALSE,
  warning = FALSE,
  background = '#F7F7F7',
  fig.align = 'center',
  dev = 'png',
  dpi = 96,
  optipng = knitr::hook_optipng,
  comment = "#>"
)
options(width = 100, stringsAsFactors = FALSE, timeout = 600)

# keep examples from using more than 2 cores
data.table::setDTthreads(Sys.getenv("OMP_THREAD_LIMIT", unset = 2))

## ----install, eval=FALSE--------------------------------------------------------------------------
# # install CRAN release + dependencies
# install.packages('aqp', dependencies = TRUE)
# install.packages('remotes', dependencies = TRUE)
# 
# # install latest version from GitHub
# remotes::install_github("ncss-tech/aqp", dependencies = FALSE)

## ----load-packages--------------------------------------------------------------------------------
library(aqp)
library(lattice)

## ----creation-------------------------------------------------------------------------------------
# load sample data set, a data.frame object with horizon-level data from 10 profiles
data(sp4)
str(sp4)

# optionally read about it...
# ?sp4

# upgrade to SoilProfileCollection
# 'id' is the name of the column containing the profile ID
# 'top' is the name of the column containing horizon upper boundaries
# 'bottom' is the name of the column containing horizon lower boundaries
depths(sp4) <- id ~ top + bottom

# define "horizon designation" column name for the collection
hzdesgnname(sp4) <- 'name'

# check it out:
class(sp4)
print(sp4)

## ----promote_to_spc, eval=FALSE-------------------------------------------------------------------
# idcolumn ~ hz_top_column + hz_bottom_column

## ----fig.width = 6--------------------------------------------------------------------------------
# character vector of horizon templates
# must all use the same formatting
x <- c(
  'P1:AAA|BwBwBwBw|CCCCCCC|CdCdCdCd',
  'P2:ApAp|AE|BhsBhs|Bw1Bw1|Bw2|CCCCCCC',
  'P3:A|Bt1Bt1Bt1|Bt2Bt2Bt2|Bt3|Cr|RRRRRR'
)

# each horizon label is '10' depth-units (default)
s <- quickSPC(x)

# sketch profiles
par(mar = c(0, 0, 0, 0))
plotSPC(s, name.style = 'center-center', 
        cex.names = 1, depth.axis = FALSE, 
        hz.depths = TRUE
)

## ----hz_and_site_data-----------------------------------------------------------------------------
# site-level (based on length of assigned data == number of profiles)
sp4$elevation <- rnorm(n = length(sp4), mean = 1000, sd = 150) 

# horizon-level (calculated from two horizon-level columns)
sp4$thickness <- sp4$bottom - sp4$top 

# extraction of specific attributes by name
sp4$clay # vector of clay content (horizon data)
sp4$elevation # vector of simulated elevation (site data)

# unit-length value explicitly targeting site data
site(sp4)$collection_id <- 1

# assign a single single value into horizon-level attributes
sp4$constant <- rep(1, times = nrow(sp4))

# unit-length value explicitly targeting horizon data
horizons(sp4)$analysis_group <- "SERP"

# _moves_ the named column from horizon to site
site(sp4) <- ~ constant 

## ----hz_and_site_data_2---------------------------------------------------------------------------
# extract horizon data to data.frame
h <- horizons(sp4)

# add a new column and save back to original object
h$random.numbers <- rnorm(n = nrow(h), mean = 0, sd = 1)

# _replace_ original horizon data with modified version
replaceHorizons(sp4) <- h

# extract site data to data.frame
s <- site(sp4)

# add a fake group to the site data
s$group <- factor(rep(c('A', 'B'), length.out = nrow(s)))

# join new site data with previous data: old data are _not_ replaced
site(sp4) <- s

# check
sp4

## ----diagnostic-----------------------------------------------------------------------------------
dh <- data.frame(
  id = 'colusa',
  kind = 'argillic',
  top = 8,
  bottom = 42,
  stringsAsFactors = FALSE
)

# overwrite any existing diagnostic horizon data
diagnostic_hz(sp4) <- dh

# append to diagnostic horizon data
dh <- diagnostic_hz(sp4)
dh.new <- data.frame(
  id = 'napa',
  kind = 'argillic',
  top = 6,
  bottom = 20,
  stringsAsFactors = FALSE
)

# overwrite existing diagnostic horizon data with appended data
diagnostic_hz(sp4) <- rbind(dh, dh.new)

## ----restrictions---------------------------------------------------------------------------------
# get the depth of each profile
rf.top <- profileApply(sp4, max)
rf.bottom <- rf.top + 20

# the profile IDs can be extracted from the names attribute
pIDs <- names(rf.top)

# note: profile IDs must be stored in a column named for idname(sp4) -> 'id'
rf <- data.frame(
  id = pIDs, 
  top = rf.top, 
  bottom = rf.bottom, 
  kind = 'fake',
  stringsAsFactors = FALSE
)

# overwrite any existing diagnostic horizon data
restrictions(sp4) <- rf

# check
restrictions(sp4)

## ----metadata-------------------------------------------------------------------------------------
# metadata structure
str(metadata(sp4))

# alter the depth unit metadata attribute
depth_units(sp4) <- 'inches' # units are really 'cm'

# add or replace custom metadata
metadata(sp4)$describer <- 'DGM'
metadata(sp4)$date <- as.Date('2009-01-01')
metadata(sp4)$citation <- 'McGahan, D.G., Southard, R.J, Claassen, V.P. 2009. Plant-Available Calcium Varies Widely in Soils on Serpentinite Landscapes. Soil Sci. Soc. Am. J. 73: 2087-2095.'

# check new values have been added
str(metadata(sp4))

# fix depth units, set back to 'cm'
depth_units(sp4) <- 'cm'

## -------------------------------------------------------------------------------------------------
# generate some fake coordinates as site level attributes
sp4$x <- rnorm(n = length(sp4), mean = 354000, sd = 100)
sp4$y <- rnorm(n = length(sp4), mean = 4109533, sd = 100)

# initialize spatial coordinates (CRS optional)
initSpatial(sp4, crs = "EPSG:26911") <- ~ x + y

# extract coordinates as matrix
getSpatial(sp4)

# get/set spatial reference system using prj()<-
prj(sp4) <- '+proj=utm +zone=11 +datum=NAD83'

# return CRS information
prj(sp4)

if (requireNamespace("sf", quietly = TRUE)) {
  # extract spatial data + site level attributes in new spatial object
  sp4.sp <- as(sp4, 'SpatialPointsDataFrame')
  sp4.sf <- as(sp4, 'sf')
}

## ----eval=FALSE-----------------------------------------------------------------------------------
# checkSPC(sp4)

## -------------------------------------------------------------------------------------------------
spc_in_sync(sp4)

## -------------------------------------------------------------------------------------------------
z <- rebuildSPC(sp4)

## -------------------------------------------------------------------------------------------------
checkHzDepthLogic(sp4)
checkHzDepthLogic(sp4, byhz = TRUE)

## ----coercion, eval=FALSE-------------------------------------------------------------------------
# # check our work by viewing the internal structure
# str(sp4)
# 
# # create a data.frame from horizon+site data
# as(sp4, 'data.frame')
# 
# # or, equivalently:
# as.data.frame(sp4)
# 
# # convert SoilProfileCollection to a named list containing all slots
# as(sp4, 'list')
# 
# # extraction of site + spatial data as SpatialPointsDataFrame
# as(sp4, 'SpatialPointsDataFrame')

## ----eval=FALSE-----------------------------------------------------------------------------------
# # explicit string matching
# idx <- which(sp4$group == 'A')
# 
# # numerical expressions
# idx <- which(sp4$elevation < 1000)
# 
# # regular expression, matches any profile ID containing 'shasta'
# idx <- grep('shasta', profile_id(sp4), ignore.case = TRUE)
# 
# # perform subset based on index
# sp4[idx, ]

## ----eval=FALSE-----------------------------------------------------------------------------------
# subset(sp4, group == 'A')
# subset(sp4, elevation < 1000)
# subset(sp4, grepl('shasta', id, ignore.case = TRUE))

## ----eval = FALSE---------------------------------------------------------------------------------
# sp4[, 2]

## ----eval = FALSE---------------------------------------------------------------------------------
# sp4[, , .FIRST]
# sp4[, , .LAST]

## ----eval = FALSE---------------------------------------------------------------------------------
# sp4[, , .FIRST, .TOP]
# sp4[, , .LAST, .HZID]

## ----concatenation, eval=FALSE--------------------------------------------------------------------
# # subset data into chunks
# s1 <- sp4[1:2, ]
# s2 <- sp4[4, ]
# s3 <- sp4[c(6, 8, 9), ]
# 
# # combine subsets
# s <- combine(list(s1, s2, s3))
# 
# # double-check result
# plotSPC(s)

## ----eval=FALSE-----------------------------------------------------------------------------------
# # sample data as data.frame objects
# data(sp1)
# data(sp3)
# 
# # rename IDs horizon top / bottom columns
# sp3$newid <- sp3$id
# sp3$hztop <- sp3$top
# sp3$hzbottom <- sp3$bottom
# 
# # remove originals
# sp3$id <- NULL
# sp3$top <- NULL
# sp3$bottom <- NULL
# 
# # promote to SoilProfileCollection
# depths(sp1) <- id ~ top + bottom
# depths(sp3) <- newid ~ hztop + hzbottom
# 
# # label each group via site-level attribute
# site(sp1)$g <- 'sp1'
# site(sp3)$g <- 'sp3'
# 
# # combine
# x <- combine(list(sp1, sp3))
# 
# # make grouping variable into a factor for groupedProfilePlot
# x$g <- factor(x$g)
# 
# # check results
# str(x)
# 
# # graphical check
# # convert character horizon IDs into numeric
# x$.horizon_ids_numeric <- as.numeric(hzID(x))
# 
# par(mar = c(0, 0, 3, 1))
# plotSPC(x, color='.horizon_ids_numeric', col.label = 'Horizon ID')
# groupedProfilePlot(x, 'g', color='.horizon_ids_numeric', col.label = 'Horizon ID', group.name.offset = -15)

## ----eval=FALSE-----------------------------------------------------------------------------------
# # continuing from above
# # split subsets of x into a list of SoilProfileCollection objects using site-level attribute 'g'
# res <- split(x, 'g')
# str(res, 1)

## ----fig.height=4, fig.width=8--------------------------------------------------------------------
d <- duplicate(sp4[1, ], times = 8)
par(mar = c(0, 2, 0, 1))
plotSPC(d, color = 'ex_Ca_to_Mg')

## ----fig.height=4, fig.width=8--------------------------------------------------------------------
# an example soil profile  
x <- data.frame(
  id = 'A',
  name = c('A', 'E', 'Bhs', 'Bt1', 'Bt2', 'BC', 'C'),
  top = c(0, 10, 20, 30, 40, 50, 100),
  bottom = c(10, 20, 30, 40, 50, 100, 125),
  z = c(8, 5, 3, 7, 10, 2, 12)
)

# init SPC
depths(x) <- id ~ top + bottom
hzdesgnname(x) <- 'name'

# horizon depth variability for simulation
horizons(x)$.sd <- 2

# duplicate several times
x.dupes <- duplicate(x, times = 5)

# simulate some new profiles based on example
# 2cm constant standard deviation of transition between horizons assumed
x.sim <- perturb(x, n = 5, thickness.attr = '.sd')

# graphical check
par(mar = c(0, 2, 0, 4))

# inspect unique results
plotSPC(unique(x.dupes, vars = c('top', 'bottom')),
        name.style = 'center-center',
        width = 0.15)

## ----fig.height=4, fig.width=8--------------------------------------------------------------------
# "uniqueness" is a function of variables selected to consider
plotSPC(unique(x.sim, vars = c('top', 'bottom')),
        name.style = 'center-center')

plotSPC(unique(x.sim, vars = c('name')),
        name.style = 'center-center',
        width = 0.15)

## ----fig.height=5, fig.width=9--------------------------------------------------------------------
par(mar = c(4, 3, 2, 2))
explainPlotSPC(sp4, name = 'name')

## ----fig.height=5, fig.width=9--------------------------------------------------------------------
par(mar = c(4, 3, 2, 2))
explainPlotSPC(sp4, name = 'name', width = 0.3)

## ----fig.height=5, fig.width=9--------------------------------------------------------------------
par(mar = c(4, 3, 2, 2))
explainPlotSPC(sp4, name = 'name', y.offset = 5)

## ----fig.height=5, fig.width=9--------------------------------------------------------------------
par(mar = c(4, 3, 2, 2))
explainPlotSPC(sp4, name = 'name', y.offset = -10)

## ----fig.height=5, fig.width=9--------------------------------------------------------------------
par(mar = c(4, 3, 2, 2))
explainPlotSPC(sp4, name = 'name', scaling.factor = 0.5)

## ----fig.height=5, fig.width=9--------------------------------------------------------------------
par(mar = c(4, 3, 2, 2))
explainPlotSPC(sp4, name = 'name', plot.order = length(sp4):1)

## ----fig.height=5, fig.width=9--------------------------------------------------------------------
par(mar = c(4, 3, 2, 2))
explainPlotSPC(sp4, name = 'name', n = length(sp4) + 2)

## ----fig.width=5, fig.height=6--------------------------------------------------------------------
data(osd)
x <- osd

## ----fig.width=5, fig.height=6--------------------------------------------------------------------
par(mar = c(0, 2, 0, 4), xpd = NA)
plotSPC(x[1, ], cex.names = 1)

## ----fig.width=7, fig.height=6--------------------------------------------------------------------
# set margins and turn off clipping
par(mar = c(0, 2, 0, 4), xpd = NA)
plotSPC(x[1:2, ], cex.names = 1, width = 0.25)

## ----fig.width=8, fig.height=6--------------------------------------------------------------------
par(mar = c(0, 2, 0, 4), xpd = NA)
plotSPC(x, cex.names = 1, depth.axis = list(line = -0.1), width = 0.3)

## ----fig.width=8, fig.height=6--------------------------------------------------------------------
par(mar = c(0, 0, 1, 1))
plotSPC(
  x,
  cex.names = 1,
  name.style = 'center-center',
  width = 0.3,
  depth.axis = FALSE,
  hz.depths = TRUE,
  hz.depths.offset = 0.08
)

## ----fig.height=5, fig.width=9--------------------------------------------------------------------
par(mar = c(4, 3, 2, 2))
pos <- jitter(1:length(sp4))
explainPlotSPC(sp4, name = 'name', relative.pos = pos)

## ----fig.height=5, fig.width=9--------------------------------------------------------------------
par(mar = c(4, 3, 2, 2))
pos <- c(1, 1.2, 3, 4, 5, 5.2, 7, 8, 9, 10)
explainPlotSPC(sp4, name = 'name', relative.pos = pos)

## ----fig.height=5, fig.width=9--------------------------------------------------------------------
par(mar = c(4, 3, 2, 2))
new.pos <- fixOverlap(pos)
explainPlotSPC(sp4, name = 'name', relative.pos = new.pos)

## ----fig.height=5, fig.width=9--------------------------------------------------------------------
par(mar = c(4, 3, 2, 2))
new.pos <- fixOverlap(pos, thresh = 0.7)
explainPlotSPC(sp4, name = 'name', relative.pos = new.pos)

## ----fig.height=4, fig.width=8--------------------------------------------------------------------
par(mar = c(0, 0, 3, 0))
plotSPC(sp4,
        name = 'name',
        color = 'clay',
        col.label = 'Clay Content (%)')

## ----fig.height=4, fig.width=8--------------------------------------------------------------------
par(mar = c(0, 0, 3, 0)) 
plotSPC(
  sp4,
  name = 'name',
  color = 'clay',
  col.label = 'Clay Content (%)'
)

## ----fig.height=4, fig.width=8--------------------------------------------------------------------
par(mar = c(0, 0, 3, 0))
plotSPC(
  sp4,
  name = 'name',
  color = 'name',
  col.label = 'Original Horizon Name'
)

## ----fig.height=4, fig.width=8--------------------------------------------------------------------
par(mar = c(0, 0, 3, 0)) 

# generalize horizon names into 3 groups
sp4$genhz <- generalize.hz(sp4$name, new = c('A', 'AB', 'Bt'), pat = c('A[0-9]?', 'AB', '^Bt'))

plotSPC(
  sp4,
  name = 'name',
  color = 'genhz',
  col.label = 'Generalized Horizon Name'
)

## ----plotting-vol-fraction, fig.height=4, fig.width=8---------------------------------------------
par(mar = c(0, 0, 3, 0)) 
# convert coarse rock fragment proportion to percentage
sp4$frag_pct <- sp4$CF * 100

# label horizons with fragment percent
plotSPC(sp4, name = 'frag_pct', color = 'frag_pct')

# symbolize volume fraction data
addVolumeFraction(sp4, colname = 'frag_pct')

## ----plotting-depth-interval----------------------------------------------------------------------
# extract top/bottom depths associated with all A horizons
tops <- minDepthOf(sp4, pattern = '^A', hzdesgn = 'name', top = TRUE)
bottoms <- maxDepthOf(sp4, pattern = '^A', hzdesgn = 'name', top = FALSE)

IDs <- profile_id(sp4)

# assemble data.frame
a <- data.frame(id = IDs, top = tops$top, bottom = bottoms$bottom)

# check
a

## ----fig.height=4, fig.width=8--------------------------------------------------------------------
par(mar = c(0, 0, 0, 0))
plotSPC(sp4)

# annotate A horizon depth interval with brackets
addBracket(a, col = 'red', offset = -0.4)

## ----fig.height=4, fig.width=8--------------------------------------------------------------------
par(mar = c(0, 0, 0, 0))
plotSPC(sp4, name = 'name')

# addBracket() looks for a column `label`; add a ID for each bracket
a$label <- site(sp4)$id

# note that depth brackets "knows which profiles to use" via profile ID
addBracket(
  a,
  col = 'red',
  label.cex = 0.75,
  missing.bottom.depth = 25,
  offset = -0.4
)

## ----fig.height=4, fig.width=8--------------------------------------------------------------------
par(mar = c(0, 0, 0, 0)) 
groupedProfilePlot(sp4, groups = 'group')
addBracket(a, col = 'red', offset = -0.4)

## ----fig.height=4, fig.width=8--------------------------------------------------------------------
par(mar = c(0, 0, 0, 0))
a.sub <- a[1:4,]
groupedProfilePlot(sp4, groups = 'group')
addBracket(a.sub, col = 'red', offset = -0.4)

## ----fig.height=4, fig.width=8--------------------------------------------------------------------
a$bottom <- NA
par(mar = c(0, 0, 0, 0))
groupedProfilePlot(sp4, groups = 'group')
addBracket(a, col = 'red', offset = -0.4)

## ----fig.height=4, fig.width=8--------------------------------------------------------------------
par(mar = c(0, 0, 0, 0))
groupedProfilePlot(sp4, groups = 'group')
addBracket(
  a,
  col = 'red',
  label.cex = 0.75,
  missing.bottom.depth = 25,
  offset = -0.4
)

## ----fig.height=4, fig.width=8--------------------------------------------------------------------
par(mar = c(0, 0, 0, 0))
plotSPC(sp4, max.depth = 75)

# copy root-restricting features
a <- restrictions(sp4)

# add a label: restrictive feature 'kind'
a$label <- a$kind

# add restrictions using vertical bars
addBracket(
  a,
  col = 'red',
  label.cex = 0.75,
  tick.length = 0,
  lwd = 3,
  offset = -0.4
)

## ----eval=FALSE-----------------------------------------------------------------------------------
# # library(svglite)
# # svglite(filename = 'e:/temp/fig.svg', width = 7, height = 6, pointsize = 12)
# #
# # par(mar = c(0,2,0,4), xpd = NA)
# # plotSPC(x, cex.names=1, depth.axis = list(line = -0.2), width=0.3)
# #
# # dev.off()

## ----profileApply-1-------------------------------------------------------------------------------
# max() returns the depth of a soil profile
sp4$soil.depth <- profileApply(sp4, FUN = max)

# max() with additional argument give max depth to non-missing 'clay'
sp4$soil.depth.clay <- profileApply(sp4, FUN = max, v = 'clay')

# nrow() returns the number of horizons
sp4$n.hz <- profileApply(sp4, FUN = nrow)

# compute the mean clay content by profile using an inline function
sp4$mean.clay <- profileApply(sp4, FUN = function(i) mean(i$clay))

# estimate soil depth based on horizon designation
sp4$soil.depth <- profileApply(sp4, estimateSoilDepth, name = 'name')

## ----profileApply-2-------------------------------------------------------------------------------
# save as horizon-level attribute
sp4$delta.clay <- profileApply(sp4, FUN = function(i) c(NA, diff(i$clay)))

# check results:
horizons(sp4)[1:6, c('id', 'top', 'bottom', 'clay', 'delta.clay')]

## ----profileApply-3-------------------------------------------------------------------------------
# compute hz-thickness weighted mean exchangeable-Ca:Mg
wt.mean.ca.mg <- function(i) {
  # use horizon thickness as a weight
  thick <- i$bottom - i$top
  
  # compute the thickness weighted mean, ignoring missing values
  weighted.mean(i$ex_Ca_to_Mg, w = thick, na.rm = TRUE)
}

# apply our custom function and save results as a site-level attribute
sp4$wt.mean.ca.to.mg <- profileApply(sp4, wt.mean.ca.mg)

## ----profileApply-4, fig.height=5, fig.width=8----------------------------------------------------
# plot the data using our new order based on Ca:Mg weighted average
# the result is an index of rank 
new.order <- order(sp4$wt.mean.ca.to.mg)

par(mar = c(4, 0, 3, 0)) # tighten figure margins
plotSPC(sp4,
        name = 'name',
        color = 'ex_Ca_to_Mg',
        plot.order = new.order)

# add an axis labeled with the sorting criteria
axis(1, at = 1:length(sp4), labels = round(sp4$wt.mean.ca.to.mg, 3), cex.axis = 0.75)
mtext(1, line = 2.25, text = 'Horizon Thickness Weighted Mean Ex. Ca:Mg', cex = 0.75)

## ----slice-formula, eval=FALSE--------------------------------------------------------------------
# # slice select horizon-level attributes
# seq ~ var.1 + var.2 + var.3 + ...
# # slice all horizon-level attributes
# seq ~ .

## ----fig.height=4, fig.width=8--------------------------------------------------------------------
# resample to 1cm slices
s <- dice(sp4, fm = 0:15 ~ sand + silt + clay + name + ex_Ca_to_Mg)

# check the result
class(s)

# plot sliced data
par(mar = c(0, 0, 3, 0)) # tighten figure margins
plotSPC(s, color = 'ex_Ca_to_Mg')

## ----eval=FALSE-----------------------------------------------------------------------------------
# # slice from 0 to max depth in the collection
# s <- dice(sp4, fm= 0:max(sp4) ~ sand + silt + clay + name + ex_Ca_to_Mg)
# 
# # extract all data over the range of 5--10 cm:
# plotSPC(s[, 5:10])
# 
# # extract all data over the range of 25--50 cm:
# plotSPC(s[, 25:50])
# 
# # extract all data over the range of 10--20 and 40--50 cm:
# plotSPC(s[, c(10:20, 40:50)])

## ----fig.height=4, fig.width=8--------------------------------------------------------------------
# truncate to the interval 5-15cm
clods <- glom(sp4, z1 = 5, z2 = 15)

# plot outlines of original profiles
par(mar = c(0, 0, 3, 1.5)) 
plotSPC(sp4, color = NA, name = NA, print.id = FALSE, depth.axis = FALSE, lwd = 0.5)

# overlay glom() depth criteria
rect(xleft = 0.5, ybottom = 15, xright = length(sp4) + 0.5, ytop = 5, lty = 2)

# add SoilProfileCollection with selected horizons
plotSPC(clods, add = TRUE, cex.names = 0.6, name = 'name', color = 'ex_Ca_to_Mg', name.style = 'center-center')

## ----fig.height=4, fig.width=8--------------------------------------------------------------------
# truncate to the interval 5-15cm
sp4.truncated <- trunc(sp4, 5, 15)

# plot outlines of original profiles
par(mar = c(0, 0, 3, 1.5)) 
plotSPC(sp4, color = NA, name = NA, print.id = FALSE, lwd = 0.5)

# overlay truncation criteria
rect(xleft = 0.5, ybottom = 15, xright = length(sp4) + 0.5, ytop = 5, lty = 2)

# add truncated SoilProfileCollection
plotSPC(sp4.truncated, depth.axis = FALSE, add = TRUE, cex.names = 0.6, name = 'name', color = 'ex_Ca_to_Mg', name.style = 'center-center')

## ----slab, fig.height=4, fig.width=8--------------------------------------------------------------
# aggregate a couple of the horizon-level attributes, 
# across the entire collection, 
# from 0--10 cm
# computing the mean value ignoring missing data
slab(
  sp4,
  fm = ~ sand + silt + clay,
  slab.structure = c(0, 10),
  slab.fun = mean,
  na.rm = TRUE
)

# again, this time within groups defined by a site-level attribute:
slab(
  sp4,
  fm = group ~ sand + silt + clay,
  slab.structure = c(0,  10),
  slab.fun = mean,
  na.rm = TRUE
)

# again, this time over several depth ranges
slab(
  sp4,
  fm = ~ sand + silt + clay,
  slab.structure = c(0, 10, 25, 40),
  slab.fun = mean,
  na.rm = TRUE
)

# again, this time along 1-cm slices, computing quantiles
agg <- slab(sp4, fm = ~ Mg + Ca + ex_Ca_to_Mg + CEC_7 + clay)

# see ?slab for details on the default aggregate function
head(agg)

# plot median +/i bounds defined by the 25th and 75th percentiles
# this is lattice graphics, syntax is a little rough
xyplot(top ~ p.q50 | variable, data = agg, ylab = 'Depth', 
       xlab = 'median bounded by 25th and 75th percentiles',
       lower = agg$p.q25, upper = agg$p.q75, ylim = c(42, -2),
       panel = panel.depth_function,
       alpha = 0.25, sync.colors = TRUE,
       par.settings = list(superpose.line = list(col = 'RoyalBlue', lwd = 2)), 
       prepanel = prepanel.depth_function,
       cf = agg$contributing_fraction, cf.col = 'black', cf.interval = 5,
       layout = c(5, 1), strip = strip.custom(bg = grey(0.8)),
       scales = list(x = list(
         tick.number = 4,
         alternating = 3,
         relation = 'free'
       ))
)

## ----slab-2, fig.height=4, fig.width=8------------------------------------------------------------
# processing the "napa" and tehama profiles
idx <- which(profile_id(sp4) %in% c('napa', 'tehama'))
napa.and.tehama <- slab(sp4[idx,], fm = ~ Mg + Ca + ex_Ca_to_Mg + CEC_7 + clay)

# combine with the collection-wide aggregate data
g <- make.groups(collection = agg, napa.and.tehama = napa.and.tehama)

# compare graphically:
xyplot(top ~ p.q50 | variable, groups = which, data = g, ylab = 'Depth',
       xlab = 'median bounded by 25th and 75th percentiles',
       lower = g$p.q25, upper = g$p.q75, ylim = c(42, -2),
       panel = panel.depth_function,
       alpha = 0.25, sync.colors = TRUE, cf = g$contributing_fraction, cf.interval = 10,
       par.settings = list(superpose.line = list(
         col = c('RoyalBlue', 'Red4'),
         lwd = 2,
         lty = c(1, 2)
       )),
       prepanel = prepanel.depth_function,
       layout = c(5, 1), 
       strip = strip.custom(bg = grey(0.8)),
       scales = list(x = list(
         tick.number = 4,
         alternating = 3,
         relation = 'free'
       )),
       auto.key = list(columns = 2,
                       lines = TRUE,
                       points = FALSE)
)

## ----fig.height=4.5, fig.width=9------------------------------------------------------------------
library(data.table)

# 9 random profiles
# 1 simulated property via logistic power peak (LPP) function
# 6, 7, or 8 horizons per profile
# result is a list of single-profile SPC
d <- lapply(
  as.character(1:9), 
  random_profile, 
  n = c(6, 7, 8), 
  n_prop = 1, 
  method = 'LPP',
  SPC = TRUE
)

# combine into single SPC
d <- combine(d)

# GSM depths
gsm.depths <- c(0, 5, 15, 30, 60, 100, 200)

# aggregate using mean: wt.mean within slabs
# see ?slab for ideas on how to parameterize slab.fun
d.gsm <- slab(d, fm = id ~ p1, slab.structure = gsm.depths, slab.fun = mean, na.rm = TRUE)

# note: result is in long-format
# note: horizon names are lost due to aggregation
head(d.gsm, 7)

## ----fig.height=7, fig.width=9--------------------------------------------------------------------
# reshape to wide format
# this scales to > 1 aggregated variables
d.gsm.pedons <- data.table::dcast(
  data.table(d.gsm), 
  formula = id + top + bottom ~ variable, 
  value.var = 'value'
)

# init SPC
depths(d.gsm.pedons) <- id ~ top + bottom

# iterate over aggregated profiles and make new hz names
d.gsm.pedons$hzname <- profileApply(d.gsm.pedons, function(i) {
  paste0('GSM-', 1:nrow(i))
})

# compare original and aggregated
par(mar = c(1, 0, 3, 3), mfrow = c(2, 1))
plotSPC(d, color = 'p1')
mtext('original depths', side = 2, line = -1.5)
plotSPC(d.gsm.pedons, color = 'p1')
mtext('GSM depths', side = 2, line = -1.5)

## ----fig.height=7, fig.width=9--------------------------------------------------------------------
# reshape to wide format
d.gsm.pedons.2 <- data.table::dcast(
  data.table(d.gsm), 
  formula = id + top + bottom ~ variable, 
  value.var = 'contributing_fraction'
)

# init SPC
depths(d.gsm.pedons.2) <- id ~ top + bottom

# compare original and aggregated
par(mar = c(1, 0, 3, 3), mfrow = c(2, 1))
plotSPC(d.gsm.pedons, name = '', color = 'p1')
mtext('GSM depths', side = 2, line = -1.5)

plotSPC(
  d.gsm.pedons.2,
  name = '',
  color = 'p1',
  col.label = 'Contributing Fraction',
)
mtext('GSM depths', side = 2, line = -1.5)

## ----fig.height=6, fig.width=10-------------------------------------------------------------------
library(cluster)
library(ape)

# start fresh
data(sp4)
depths(sp4) <- id ~ top + bottom
hzdesgnname(sp4) <- 'name'

# eval dissimilarity:
# using Ex-Ca:Mg ratio and CEC at pH 7
# no depth-weighting (k = 0)
# to a maximum depth of 40 cm
d <- NCSP(sp4, vars = c('ex_Ca_to_Mg', 'CEC_7'), k = 0, maxDepth = 40)

# check distance matrix:
round(d, 1)

# visualize dissimilarity matrix via divisive hierarchical clustering
d.diana <- diana(d)

# may require some margin adjustments
par(mar = c(0, 0, 4, 0))

plotProfileDendrogram(
  sp4,
  d.diana,
  scaling.factor = 0.9,
  y.offset = 5,
  cex.names = 0.7,
  width = 0.3,
  color = 'ex_Ca_to_Mg',
  name.style = 'center-center',
  hz.depths = TRUE,
  depth.axis = FALSE
)

