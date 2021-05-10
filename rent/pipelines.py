# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import re

class RentPipeline:
    def process_item(self, item, spider):

        id = re.match('.*property-(\d*)', item['url']).group(1)
        item['id'] = int(id)

        rent_amt = re.match('^Lease \$(.*)$', item['monthly_rental']).group(1)
        rent_amt = rent_amt.replace(',', '')
        item['monthly_rental'] = int(rent_amt)

        ads_type = re.match('.*\[(.*) Ads\]', item['title']).group(1)
        item['ads_type'] = ads_type

        vistor_cnt = re.match('.*#(\d*).*', item['tag']).group(1)
        item['vistor_cnt'] = int(vistor_cnt)

        for a in ['salesable_area', 'building_area']:
            if item.get(a):
                area = re.match('(\d.*) Sq. Feet.*', item[a]).group(1)
                item[a] = int(area)

        return item
