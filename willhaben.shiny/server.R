library(shiny)
library(DT)
library(data.table)
library(ggplot2)

subset.dt <- function(dt, input){
    if(!is.null(input$postCode)){ dt<- dt[postalCode %in% input$postCode]}
    dt <- dt[price > input$price[1]][price < input$price[2]]
    #print(dt)
    dt
}

shinyServer(function(input, output) {
    output$table <- DT::renderDataTable({
        x <- subset.dt(dt,input)
        x.select <- brushedPoints(x, input$plot_brush)
        if(nrow(x.select)!=0){
            x <- x.select
        }
        x <- x[,.SD,.SDcols=c(selected.constant, input$select)]
        x
    }, rownames = F, escape=F)
    
    output$plot <- renderPlot({
        x <- subset.dt(dt,input)
        x.min <- max(c(0,min(x$price,na.rm = T)-5E4))
        x.max <- max(x$price,na.rm = T)+5E4
        y.max <- max(x[,.SD,.SDcols=input$yaxis],na.rm=T)
        
        p <- ggplot() + aes(x=price,y=!! rlang::sym(input$yaxis)) + xlim(x.min,x.max) + ylim(0,y.max)
        p <- p + geom_point(data=dt,colour="grey80")
        p <- p + geom_point(data=x)
        p <- p + geom_vline(xintercept = input$price, linetype='dashed')
        
        x.select <- brushedPoints(x, input$plot_brush)
        p <- p + geom_point(size=2,data=x.select, col='gold')
        
        p <- p + theme_bw(20) + theme(panel.grid = element_blank())
        p
    })
})
