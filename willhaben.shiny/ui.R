library(shiny)
library(data.table)
library(DT)

shinyUI(fluidPage(

    titlePanel("Wilhaben House Scrapper"),

    sidebarLayout(
        sidebarPanel(
            sliderInput("price", "Price:", 0,2E6, c(4E5,6E5), step=1E4),
            selectInput("postCode", "Post code(s):", dt$postalCode, multiple=TRUE, selectize=TRUE, selected = 2542),
            selectInput("select", "Select columns to display", names(dt)[!(names(dt) %in% selected.constant)], multiple = TRUE, 
                        selected = c("objekttyp", "wohnflache", "grundflache")),
            radioButtons("yaxis", "Plot Y-axis",
                         choices = list("price.predicted", "wohnflache", "grundflache", "zimmer", "wien.dist", "kottingbrunn.dist", "hwb.kwh.m2.jahr"), 
                         selected = "price.predicted")
        ),

        mainPanel(
            plotOutput("plot", brush = "plot_brush"),
            dataTableOutput('table'),
        )
    )
))