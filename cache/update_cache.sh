# Copyright 2018 Building Energy Gateway.  All rights reserved.
#
# Continuously update Building Energy Gateway cache
#
# To run this script periodically, edit the root crontab:
#   sudo crontab -e
#
# To restart this script every 5 minutes, for example, enter this line:
#   */5 * * * * sh /opt/nav/bg/cache/update_cache.sh
#

# Set working directory
cd /opt/nav/bg/cache

# Start cache updater
/home/ea/anaconda3/bin/python ./update_cache.py -h localhost -p 8000 -s 5
