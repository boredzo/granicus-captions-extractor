# Granicus WebVTT extractor

I live in San Francisco. Our City government uses a service called Granicus to [stream and host videos of government hearings, such as those of the Board of Supervisors](https://sfgovtv.org/).

These hearings typically include live captions. The videos can be downloaded, but don't include subtitle tracks and the subs can't be downloaded separately.

So I wrote a tool that downloads the subtitles in the JSON format Granicus's player uses, and converts them to WebVTT format, which other video players and converters can use.

You can also look at the WebVTT file yourself to search the captions for keywords and find interesting times in the video.

## Usage
	extract-webvtt-from-granicus.py $VOD_URL >output.webvtt

Generally you give it the URL of a video-on-demand (VOD) stream. This is the page that pops up when you click on “Video” on [the Recent Archives page](https://sfgovtv.org/recent-archives). (You may have to jump through some hoops to get the page URL, such as by popping open the Element Inspector and accessing `window.location.href` in the Console.) You can also feed it a JSON file that you've scraped yourself, if it's in the format Granicus uses.

The tool writes the WebVTT output to stdout, so you'll want to redirect that to a file.