# Quakebot

[![Total alerts](https://img.shields.io/lgtm/alerts/g/dachosen1/nearquake.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/dachosen1/nearquake/alerts/)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/dachosen1/nearquake.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/dachosen1/nearquake/context:python)
[![Twitter Follow](https://img.shields.io/badge/%20-@__quakebot_-black?color=14171A&labelColor=00acee&logo=twitter&logoColor=ffffff)](https://twitter.com/quakebot_)

Quakebot is designed to tweet earthquakes greater than 5.0 around the world, and provides a historical snapshot of earthquakes.  

### Tweet Schedule: 
Daily: 
- Earthquakes with a magnitude greater than 5.0 

Weekly: 
- Recap of the top earthquakes weekly, Monthly, and YTD
- Recap of the number of the earthquakes grouped daily, weekly, Monthly, and YTD

### Source
Data is provided by [USGS](https://earthquake.usgs.gov)

### Deployment 
Tweets are scheduled via cron job and deployed on a Digital Ocean Droplet. Historical data is stored on a Postgres database hosted by AWS 
