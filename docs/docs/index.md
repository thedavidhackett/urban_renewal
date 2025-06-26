# Urban Renewal Projects in Chicago

## Overview

This project makes use of the [Chicago Public Library's collection of Urban Renewal Records](https://www.chipublib.org/chicago-department-of-urban-renewal-records-photographic-negatives-digital-collection/). The collection contains over 15,000 photos taken by the Chicago Department of Urban Renewal between 1956 and 1978. Most of the photos are of project sites in Chicago and many included both a date and location for the photo. While these photos are unlikely to represent a complete picture of all the projects undertaken by the Department of Urban Renewal they can at least provide a sample of the location and timing of projects. The goal of this project was to create a data visualization showing the locations of Urban Renewal Projects overtime. You can see the final product here:

[Urban Renewal Project Locations in Chicago over Time](urban_renewal_project_locations_overtime.md)

## Project Steps

### Scraping project data 

The first step was getting the data associated with each photo. This data typically included a title and subject categories. The majority of the photos were also associated with a date and an address. The script scrape_urban_renewal_locations.py made calls directly to the api and wrote the data into a csv file.

### Extracting Street Addresses with NER

While a majority of the photos came with a street address already indicated a significant amount did not. However
the majority of the these had an address in the title, typically surround by other text. A model from [spaCy](https://spacy.io/) was trained to perform named entity recognition on the dataset. Since many of the projects with addresses already also had the address in their title this created a natural training dataset. Extra examples were added to account for address patterns not seen in the training dataset by injecting constucted addresses matching those patterns into random titles from the existing dataset. The model achieved 100% precision, and over 99% recall and F1 scores on the test dataset.

## Extracting Street Addresses with Regex

While the model performed well it did not successfully extract every address when used on the projects missing addresses. Many of the addresses followed similar patterns and so were extracted using regex matching. Its possible this might have been more effective than using NER in the first place, but oh well. After this a few addresses were added by hand.

## Geocoding Addresses

After the addresses were extracted I created a dataset of unique addresses since many of the photos were of the same project (and thus had the same address). The addresses were geocoded using the [Census Geocoder API](https://geocoding.geo.census.gov/geocoder/Geocoding_Services_API.html) and another [package](https://pypi.org/project/batchcensusgeocode/) I created specifically to make batch geocoding more convenient.

## Creating Data Visualization

Finally (plotly)[https://plotly.com/graphing-libraries/] was used to create a data visualization showing a map of Chicago with each project location appearing as a dot based on the date of the first photo taken at that location. 