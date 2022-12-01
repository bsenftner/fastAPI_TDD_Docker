#!/bin/bash
# expects two args, in this order:
# 1) filename of the gzipped postgres backup to restore
# 2) the postgres container id
#
# gunzip < $1 | docker exec -i $2 psql -U basic_blog -d basic_blog_dev
#
gunzip < $1 | docker exec -i $2 psql -U basic_blog basic_blog_dev 
echo "restored $1"
