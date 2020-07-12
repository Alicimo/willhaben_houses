all: generate model shiny

generate:
	python3 src/scrapper.py

model:
	Rscript -e "rmarkdown::render('reports/analysis.Rd')"

shiny:
	Rscript -e "rsconnect::deployApp('willhaben.shiny')"

