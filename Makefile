all: scrape data/houses.processed.csv data/houses.modelled.csv willhaben.shiny/houses.modelled.csv

scrape:
	python3 src/scrapper.py

data/houses.processed.csv:
	Rscript src/process.houses.R

data/houses.modelled.csv: data/houses.processed.csv
	Rscript src/make.model.R

willhaben.shiny/houses.modelled.csv: data/houses.modelled.csv
	cp data/houses.modelled.csv willhaben.shiny/
	Rscript -e "rsconnect::deployApp('willhaben.shiny')"
