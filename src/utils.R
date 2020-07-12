library(data.table)
library(stringr)
library(sf)
library(glmnetUtils)
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
    dt <- munging(dt)
    dt <- add.distance(dt)
    fwrite(dt, paste0(data.dir,'/houses.processed.csv'))
  }
  return(dt)
}

munging <- function(dt){
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
  
  return(dt)
}

add.distance <- function(dt){
  wien <- geocode('hauptbahnhof, wien, austria')
  kottingbrunn <- geocode('hauptbahnhof, kottingbrunn, austria')
  dt[,wien.dist:=as.numeric(st_distance(geometry,wien))]
  dt[,kottingbrunn.dist:=as.numeric(st_distance(geometry,kottingbrunn))]
  return(dt)
}

remove.outliers <- function(dt){
  dt <- dt[!is.na(price)]
  dt <- dt[price!=15E6]
  dt <- dt[price>1E4]
  dt <- dt[V1!=378588454]
  return(dt)
}

houses.lasso <- function(dt, verbose=T){
  ignored <- c('V1','location','gesamtflache','nutzflache','fgee','hwb.energieklasse',
               'fgee.energieklasse','zimmer',"betriebskosten.inkl.mwst","heizkosten.exkl.mwst", 
               "monatliche.kosten.mwst", "monatliche.kosten.inkl.mwst", "sonstige.kosten.exkl.mwst",
               'geometry','country','state','county','houseNumber','address','street','district','city','live')
  
  x <- dt[,.SD,.SDcols=names(dt)[!(names(dt) %in% c(ignored))]]
  m <- cv.glmnet(log(price) ~ ., data=x)
  
  if(verbose){
    plot(m)
    c <- as.matrix(coef(m,s='lambda.min'))
    print(c[c!=0,,drop=F])
  }
  
  dt.prices <- cbind(dt, price.predicted = exp(predict(m,x,s=m$lambda.min)[,1]))
  dt.prices[,residual:=price.predicted - price]
  dt.prices <- dt.prices[order(-residual)]
  return(dt.prices)
}