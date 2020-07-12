library(git2r)
project.dir <- workdir(repository())
data.dir <- paste0(project.dir,'/data')
src.dir <- paste0(project.dir,'/src')

source(paste0(src.dir,'/utils.R'))
dt <- get.houses(data.dir)