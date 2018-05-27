# Real-Time Politics

## This repo
Tools + datasets for opening up data related to the democratic process and institutions:
- House of Representatives and Senate Hansard
- ParlView video recordings
- Parliament of Australia stats and Senate StatsNet
- FoI disclosure logs
- Lobbyists register
- Think tanks, special interest organisations, ...

## Goal
Set a data-driven playground for a political dashboard (attempt at assessing if our institutions and representatives work for us).

Ping me if you have related ideas / projects.



## Quirks

AEC 2016 national electorates converted from MapInfo TAB to ESRI shp using ogr2ogr:

```
ogr2ogr -f "ESRI Shapefile" -t_srs EPSG:4326 aec/data/national2016.shp ~/Data/aec/COM_ELB.TAB 
Warning 6: Normalized/laundered field name: 'Total_Population' to 'Total_Popu'
Warning 6: Normalized/laundered field name: 'Australians_Over_18' to 'Australian'
```


Download all NLTK packages:

```
>>> import nltk
>>> nltk.download()
```

Download spaCy model:

```
python -m spacy download en_core_web_sm
```