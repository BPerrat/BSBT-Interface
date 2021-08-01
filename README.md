# BSBT-Interface

This repository provides a web interface to facilitate the collection of comparative judgements on geospatial datasets to be processed with the Bayesian Spatial Bradley--Terry model `BSBT` - https://github.com/rowlandseymour/BSBT). In only a couple of minutes, it lets you deploy a web interface to collect comparative judgements by simply requiring a Shapefile containing the regions of interests (i.e. to be compared) as input. The results are stored in an SQLite database which can then be directly processed using the `BSBT` package to obtain a ranking.

# Installation

You can install the BSBT-Interface using the following commands:
```bash
git clone https://github.com/BPerrat/BSBT-Interface.git
cd BSBT-Interface
python3 -m venv venv
source venv/bin/activate
pip install -r website/requirements.txt
```

# Preparing the Data

This is the only setup step required to define the regions of interest. The script `prepare_website.py` streamlines the process and can be called as follow:
```bash
python3 prepare_website.py <your_shapefile.shp>
```

You will be asked to first select which column in the Shapefile should be used as a unique identifier for your regions and secondly to select which column you wish to use to name your regions. In both cases, only suitable candidates are displayed (i.e. if a column doesn't uniquely identify each entry of the shapefile, it will not be candidate).

The script will then:
1. Regionalize (cluster) your regions for a pre-filtering stage if your dataset is large
2. Create images for each region displaying their extent on top of a map
3. Setup the database that will then be used to store the comparative judgements and eventually be passed to the BSBT model.

Once the script has run, it should have populated the folder `website/static/maps` with images and the database `comparative_judgements.db` in the root project folder.

# Launching the Interface

You can run the interface using the following commands:
```bash
export FLASK_APP=website
flask run
```

If you are likely to experience significant traffic, it is recommended to move away from Flask's built-in webserver (called with `flask run`) towards a production WSGI server such as Gunicorn.

# The Interface in Action


# Processing the Judgements

Once data collection is completed, the comparative judgements can be processed using the `BSBT` package in a seamless way.
