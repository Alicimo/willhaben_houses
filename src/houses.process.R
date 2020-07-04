library(data.table)
library(stringr)
library(sf)
library(hereR)
set_key('MZ32xprIUALb2Ypy579fDeHscTzx4fK9EgfXgFVaMw0') #hereR key

get.houses <- function(data.dir){
  dt <- fread(paste0(data.dir,'/houses.csv'), check.names = T)
  if(file.exists(paste0(data.dir,'/houses.processed.csv'))){
    print("Existing house file found")
    dt.processed <- fread(paste0(data.dir,'/houses.processed.csv'), check.names = T)
  } else {
    dt.processed <- data.table()
  }
  if(nrow(dt) == nrow(dt.processed)){
    print("Existing file has same house count")
    dt <- dt.processed
    dt[,postalCode:=factor(postalCode)]
  } else{
    #dt[!(V1 %in% dt.processed$V1)]
    
    dt[,price:=as.numeric(gsub('\\.','',substr(kaufpreis,3,20)))]
    dt[,wohnflache:=as.numeric(substr(wohnflache,1,nchar(wohnflache)-3))]
    dt[,grundflache:=as.numeric(substr(grundflache,1,nchar(grundflache)-3))]
    dt[,nutzflache:=as.numeric(substr(nutzflache,1,nchar(nutzflache)-3))]
    dt[,zimmer:=as.numeric(gsub(',','.',zimmer))]
    dt[,hwb.kwh.m2.jahr:=as.numeric(gsub(',','.',hwb.kwh.m2.jahr))]
    dt[,fgee:=as.numeric(gsub(',','.',fgee))]
    dt[grep('ab \\d',verfugbar), verfugbar:='completion.date.stated']
    
    dt[is.na(wohnflache),wohnflache:=nutzflache]
    dt[is.na(wohnflache)]$wohnflache <- mean(dt$wohnflache, na.rm=T)
    dt[is.na(grundflache),grundflache:=nutzflache]
    dt[is.na(grundflache)]$grundflache <- mean(dt$grundflache, na.rm=T)
    
    dt[is.na(hwb.kwh.m2.jahr)]$hwb.kwh.m2.jahr <- mean(dt$hwb.kwh.m2.jahr, na.rm=T)
    
    dt[dt==''] <- 'UNKNOWN'
    
    x <- data.table(dt[,geocode(location)])
    x[is.na(x)] <- 'UNKNOWN'
    x[,postalCode:=factor(as.numeric(postalCode))]
    x[,type:=NULL]
    dt <- cbind(dt, x)
    
    dt[,url:=NULL]
    dt[,X0:=NULL]
    dt[,X0.1:=NULL]
    dt[,X0.2:=NULL]
    dt[,stockwerk.e:=NULL]
    dt[,kaufpreis:=NULL]
    dt[,location:=NULL]
    
    wien <- geocode('hauptbahnhof, wien, austria')
    dt[,wien.dist:=as.numeric(st_distance(geometry,wien))]
    
    kottingbrunn <- geocode('hauptbahnhof, kottingbrunn, austria')
    dt[,kottingbrunn.dist:=as.numeric(st_distance(geometry,kottingbrunn))]
    fwrite(dt, paste0(data.dir,'/houses.processed.csv'))
  }
  return(dt)
}