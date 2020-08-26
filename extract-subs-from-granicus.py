#!/usr/bin/python

import sys
import os
import argparse
import re
import subprocess
import urlparse
import json
import cgi

parser = argparse.ArgumentParser()
parser.add_argument('--format', action='store', choices=[ 'webvtt', 'srt' ], default='webvtt')
opts, args = parser.parse_known_args()

def extract_captions_from_webpage(webpage_URL):
	curl = subprocess.Popen([ '/usr/bin/curl', '-L', webpage_URL ], stdout=subprocess.PIPE, stderr=open('/dev/null', 'wb'))
	'''<!DOCTYPE html>
<html lang="en">
<head>
<meta property="og:image" content="//sanfrancisco.granicus.com/core/Handlers/media/attachmentdisplay.ashx?guid=853dfbab-b605-4621-afd4-a86b2cef3012"/>
<meta property="og:video" content="https://sanfrancisco.granicus.com/players/modernplayer.swf?enableclosedcaptions=false&enableembedding=false&menu=true&quality=high&wmode=window&scale=noscale&allowFullScreen=false&VideoUrl=%2F%2Fsanfrancisco.granicus.com%2FASX.php%3Fview_id%3D192%26clip_id%3D36441%26r%3D08fd8aa9d040c2e665416ad4a98c613b%26intro%3D1%26sn%3Dsanfrancisco.granicus.com%26bitrate%3D%26stream_type%3Drtmp&ScriptUrl=%2F%2Fsanfrancisco.granicus.com%2FJSON.php%3Fview_id%3D192%26clip_id%3D36441%26intro%3D1%26r%3D08fd8aa9d040c2e665416ad4a98c613b&AspectRatio=true&SiteID=sanfrancisco.granicus.com" />
<meta name="description" content="Live and Recorded Public meetings of BOS Budget and Appropriations Committee - Recessed Meeting for City and County of San Francisco" />
<meta name="keywords" content="BOS Budget and Appropriations Committee - Recessed Meeting, City and County of San Francisco, live, video, meeting, public, recorded, events, city, state, county, federal, transparency, freedom of information, FOIA, agenda, minutes" />
'''
	head = curl.stdout.read(1024)
	curl.stdout.close()
	curl.wait()
	meta_video_exp = re.compile('<meta property="og:video" content="([^"]+)" />')
	match = meta_video_exp.search(head)
	if match:
		JSON_URL = match.group(1)
		return extract_captions_from_Granicus_JSON(JSON_URL)

def extract_captions_from_Granicus_JSON(URL_or_path):
	if hasattr(URL_or_path, 'read'):
		JSON = URL_or_path.read()
	elif URL_or_path.startswith('https:'):
		if 'modernplayer.swf' in URL_or_path:
			parsed_SWF_URL = urlparse.urlparse(URL_or_path)
			query = urlparse.parse_qs(parsed_SWF_URL.query)
			JSON_URL = 'https:' + query['ScriptUrl'][0]
		else:
			JSON_URL = URL_or_path

		curl = subprocess.Popen([ '/usr/bin/curl', '-L', JSON_URL ], stdout=subprocess.PIPE, stderr=open('/dev/null', 'wb'))
		JSON = curl.stdout.read()
		curl.stdout.close()
		curl.wait()
	else:
		JSON = open(URL_or_path, 'r').read()

	decoder = json.JSONDecoder()
	timestamps = decoder.decode(JSON)

	last_caption = None
	for each in timestamps[0]:
		if each['type'] == 'text':
			if last_caption is not None:
				last_caption['end_time'] = each['time']
			last_caption = each

	return timestamps

def convert_captions_to_WebVTT(captions):
	def convert_seconds_to_timestamp(total_seconds_str):
		total_seconds = float(total_seconds_str)
		hours = int(total_seconds / 3600)
		minutes = int(total_seconds / 60) % 60
		seconds = total_seconds % 60.0
		# Sadly %02.3f doesn't Just Work, so we have to do this garbage.
		seconds_int = int(seconds)
		seconds_frac = seconds - seconds_int
		seconds_str = '%02u' % (seconds_int,) + ('%.3f' % (seconds_frac,)).lstrip('0')
		return ('%02u:%02u:%s' % (hours, minutes, seconds_str))
	
	chunks = [
		'''WEBVTT
'''
	]

	for each in captions[0]:
		if each['type'] == 'text':
			start_timestamp = convert_seconds_to_timestamp(each['time'])
			try:
				end_timestamp = convert_seconds_to_timestamp(each['end_time'])
			except KeyError:
				# The last caption won't have an end time, since the end time is the start time of the caption after it. Make up a five-second duration for the last caption.
				fake_end_time = str(float(each['time']) + 5.0)
				end_timestamp = convert_seconds_to_timestamp(fake_end_time)
			text = each['text']
			chunks.append('''%s --> %s
%s
''' % (start_timestamp, end_timestamp, cgi.escape(text)))

	return '\n'.join(chunks)

def convert_captions_to_SRT(captions):
	def convert_seconds_to_timestamp(total_seconds_str):
		total_seconds = float(total_seconds_str)
		hours = int(total_seconds / 3600)
		minutes = int(total_seconds / 60) % 60
		seconds = total_seconds % 60.0
		# Sadly %02.3f doesn't Just Work, so we have to do this garbage.
		seconds_int = int(seconds)
		seconds_frac = seconds - seconds_int
		seconds_str = '%02u' % (seconds_int,) + ('%.3f' % (seconds_frac,)).lstrip('0')
		return ('%02u:%02u:%s' % (hours, minutes, seconds_str)).replace('.', ',')
	
	chunks = [
		''
	]
	counter = 0

	for each in captions[0]:
		if each['type'] == 'text':
			start_timestamp = convert_seconds_to_timestamp(each['time'])
			try:
				end_timestamp = convert_seconds_to_timestamp(each['end_time'])
			except KeyError:
				# The last caption won't have an end time, since the end time is the start time of the caption after it. Make up a five-second duration for the last caption.
				fake_end_time = str(float(each['time']) + 5.0)
				end_timestamp = convert_seconds_to_timestamp(fake_end_time)
			text = each['text']
			counter = counter + 1
			chunks.append('''%u
%s --> %s
%s
''' % (counter, start_timestamp, end_timestamp, cgi.escape(text)))

	return '\n'.join(chunks)

try:
	(URL_or_path,) = args
	use_stdin = False
except ValueError:
	use_stdin = True

if use_stdin:
	captions = extract_captions_from_Granicus_JSON(sys.stdin)
elif URL_or_path.startswith('https:'):
	captions = extract_captions_from_webpage(URL_or_path)
else:
	captions = extract_captions_from_Granicus_JSON(URL_or_path)

if opts.format == 'srt':
	sys.stdout.write(convert_captions_to_SRT(captions))
else:
	sys.stdout.write(convert_captions_to_WebVTT(captions))
