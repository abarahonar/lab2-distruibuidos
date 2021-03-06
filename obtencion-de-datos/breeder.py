from confluent_kafka import admin, Producer
import pandas as pd
import tarfile
import fastavro
import wget
import os
import urllib.request
import sys
from bs4 import BeautifulSoup
import schedule
import time
from itertools import cycle


KAFKA_HOST = os.getenv("KAFKA_HOST")
WORKING_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(WORKING_DIRECTORY)
KAFKA_CONFIG = {
    "bootstrap.servers": KAFKA_HOST
}
url_format = "https://ztf.uw.edu/alerts/public/{}"


def create_dir():
    if not os.path.isdir(OUTPUT_PATH):
        os.mkdir(OUTPUT_PATH)
        return True
    return False


def download_data(file):
    create_dir()
    wget.download(url_format.format(file), os.path.join(OUTPUT_PATH, file))





def read_avro(file):
    with open(file, 'rb') as f:
        raw = f.read()
        f.seek(0)
        reader = fastavro.reader(f)
        data = reader.next()
        return raw


def to_stream_tar(file, producer):
    tar = tarfile.open(os.path.join(OUTPUT_PATH, file))
    particion = cycle(range(4))
    try:
        for member in tar.getmembers():
            tar.extract(member, OUTPUT_PATH)
            data = read_avro(os.path.join(OUTPUT_PATH, member.name))
            os.remove(os.path.join(OUTPUT_PATH, member.name))
            producer.produce('Magnitudes', value=data, particion = next(particion))
            producer.flush()
    except Exception as e:
        pass
    tar.close()


def to_stream_dir(path_dir, kafka_client, name):
    for file in os.listdir(path_dir):
        if file[-6:] == "tar.gz":
            to_stream_tar(file, producer)
    os.remove(OUTPUT_PATH+"/"+name)
def files():
	datos = urllib.request.urlopen('https://ztf.uw.edu/alerts/public/').read().decode()
	soup =  BeautifulSoup(datos)
	tags = soup('a')
	archives = []
	for tag in tags:
		archives.append(tag.get('href'))	
	return archives

def new_file(archives):
	print("Descargando archivo: " + archives[15])
	wget.download("https://ztf.uw.edu/alerts/public/"+archives[15], os.path.join(OUTPUT_PATH))
	to_stream_dir(OUTPUT_PATH, client, archives[15])
    
schedule.every().day.at("11:00").do(new_file, files())

if __name__ == "__main__":
    producer = Producer(KAFKA_CONFIG)
    while(True):
        schedule.run_pending()
        time.sleep(30)