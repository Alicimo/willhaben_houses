library(data.table)

dt <- fread("houses.modelled.csv")
dt[,postalCode:=factor(postalCode)]
dt <- dt[live==TRUE]
dt[,price.predicted:=round(price.predicted)]
dt[,item.code:=paste0('<a target="_blank" href=https://www.willhaben.at/iad/finncode/result?finncode=',V1,">",V1,"</a>")]
#dt[,item.code:=V1]
#dt[,V1:=NULL]

selected.constant <- c('item.code','price','price.predicted','postalCode')